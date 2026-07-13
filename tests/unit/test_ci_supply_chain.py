from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/playbook-checks.yml"


def test_ci_actions_are_immutable_and_least_privilege() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    action_refs = re.findall(r"uses:\s*([^@\s]+)@([^\s#]+)", workflow)

    assert action_refs
    assert all(re.fullmatch(r"[0-9a-f]{40}", revision) for _, revision in action_refs)
    assert "\npermissions:\n  contents: read\n" in workflow
    assert workflow.count("persist-credentials: false") == 1
