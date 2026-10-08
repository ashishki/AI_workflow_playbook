#!/usr/bin/env python3
"""Prepare and score a bounded Controlled Delegation experiment. No model calls."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

# Keep these modules local to the experiment when loaded via importlib in tests.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from experiment_core import (ExperimentError, RESULTS_SCHEMA, empty_run, load_manifest,
    prepare, strict_json)
from experiment_checks import check_workspace, collect, validate_results
from experiment_report import decision, make_report

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    x=sub.add_parser('prepare'); x.add_argument('--output',type=Path,required=True); x.add_argument('--seed',type=int,default=20261008); x.add_argument('--head',required=True); x.add_argument('--model',required=True); x.add_argument('--host',default='codex')
    x=sub.add_parser('check-workspace'); x.add_argument('--scenario',required=True); x.add_argument('--workspace',type=Path,required=True)
    x=sub.add_parser('collect'); x.add_argument('--run-root',type=Path,required=True); x.add_argument('--output',type=Path,required=True)
    x=sub.add_parser('report'); x.add_argument('--input',type=Path,required=True); x.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        r=prepare(a.output,seed=a.seed,head=a.head,model=a.model,host=a.host) if a.cmd=='prepare' else check_workspace(a.scenario,a.workspace) if a.cmd=='check-workspace' else collect(a.run_root,a.output) if a.cmd=='collect' else make_report(strict_json(a.input),a.output_dir)
        print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)); return 0 if r.get('status') not in {'FAIL','blocked'} else 1
    except (ExperimentError,OSError,subprocess.SubprocessError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'blocked','reason':str(exc)},ensure_ascii=False),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
