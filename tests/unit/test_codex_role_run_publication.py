from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools" / "run_codex_role.py"


RENDERER = r'''#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--root")
p.add_argument("--task")
p.add_argument("--role", required=True)
p.add_argument("--feature-id")
p.add_argument("--slice-id")
p.add_argument("--parse-report")
a=p.parse_args()
markers={"product_design_review":"PRODUCT_DESIGN_REVIEW","program_design_review":"PROGRAM_DESIGN_REVIEW","slice_review":"SLICE_REVIEW","maintainability_review":"MAINTAINABILITY_REVIEW"}
if a.parse_report:
    text=Path(a.parse_report).read_text()
    m=re.search(rf"(?m)^{markers[a.role]}: (PASS|ADVISORY|STOP_SHIP)\s*$", text)
    if not m: raise SystemExit("missing required marker")
    print(json.dumps({"verdict":m.group(1)}))
else:
    print(f"Role: {a.role}\nRequired marker: {markers[a.role]}: PASS | ADVISORY | STOP_SHIP")
'''


FAKE_CODEX = r'''#!/usr/bin/env python3
import json, sys
from pathlib import Path
if sys.argv[1:]==["--version"]:
    print("codex-cli 0.test"); raise SystemExit(0)
a=sys.argv[1:]
out=Path(a[a.index("--output-last-message")+1])
prompt=a[-1]
marker=next(v for v in ["PRODUCT_DESIGN_REVIEW","PROGRAM_DESIGN_REVIEW","SLICE_REVIEW","MAINTAINABILITY_REVIEW"] if v in prompt)
out.write_text(f"{marker}: PASS\nNo findings.\n")
print(json.dumps({"type":"turn.completed","usage":{}}))
'''


APPROVER = r'''from __future__ import annotations
import json
from pathlib import Path

def write_design_review_record(*, root, feature_id, role, report_path, reviewed_design, reviewer_binding):
    path=Path(root)/".playbook-artifacts"/"reviews"/feature_id/"design"/f"{role}.review.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "feature_id":feature_id,
        "role":role,
        "report_path":report_path,
        "reviewer_binding":reviewer_binding,
        "reviewed_design":reviewed_design,
    }, sort_keys=True)+"\n")
'''


def executable(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_valid_design_review_is_published_and_bound_to_design(tmp_path: Path) -> None:
    project=tmp_path/"project"
    project.mkdir()
    subprocess.run(["git","init","-q"],cwd=project,check=True)
    subprocess.run(["git","config","user.email","test@example.com"],cwd=project,check=True)
    subprocess.run(["git","config","user.name","Test"],cwd=project,check=True)
    (project/".gitignore").write_text(".playbook-artifacts/\n")
    tools=project/"tools"
    tools.mkdir()
    executable(tools/"render_codex_exec_prompt.py",RENDERER)
    (tools/"approve_feature_design.py").write_text(APPROVER)
    design=project/"docs"/"design"
    design.mkdir(parents=True)
    (project/"docs"/"tasks.md").write_text("# Tasks\nT01\n")
    (project/"docs"/"PROJECT_BRIEF.md").write_text("# Brief\n")
    (project/"docs"/"ARCHITECTURE.md").write_text("# Architecture\n")
    (design/"F01.md").write_text("# Feature Design\n")
    (design/"F01.design.json").write_text(json.dumps({
        "schema_version":"playbook.feature_design.v1",
        "feature_id":"F01",
        "status":"review_required",
        "planning_depth":"designed_slices",
        "risk_level":"high",
        "brief_ref":"docs/PROJECT_BRIEF.md",
        "architecture_refs":["docs/ARCHITECTURE.md"],
        "approval_policy":"human_required",
        "slices":[],
    })+"\n")
    codex=executable(tmp_path/"fake-codex",FAKE_CODEX)
    subprocess.run(["git","add","."],cwd=project,check=True)
    subprocess.run(["git","commit","-q","-m","fixture"],cwd=project,check=True)

    result=subprocess.run([
        sys.executable,str(RUNNER),"run","--root",str(project),"--task","T01",
        "--feature-id","F01","--role","program_design_review","--codex-bin",str(codex),
        "--run-id","publish-design-review",
    ],cwd=ROOT,env=dict(os.environ),text=True,capture_output=True,check=False)

    assert result.returncode==0,result.stderr
    published=project/".playbook-artifacts"/"reports"/"F01"/"program_design_review.md"
    record=project/".playbook-artifacts"/"reviews"/"F01"/"design"/"program_design_review.review.json"
    assert published.read_text()=="PROGRAM_DESIGN_REVIEW: PASS\nNo findings.\n"
    payload=json.loads(record.read_text())
    assert payload["feature_id"]=="F01"
    assert payload["report_path"]==".playbook-artifacts/reports/F01/program_design_review.md"
    assert payload["reviewer_binding"].startswith("codex-role-run:publish-design-review:")
