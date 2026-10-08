"""Preregistered round-2 scoring. Runs tests; never supplies task solutions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from round2_fixtures import cases


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n')


def read(path):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    def constant(value): raise ValueError('nonfinite JSON number')
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=constant)


def headings(path):
    if not path.is_file(): return False
    text=path.read_text().lower()
    return all(label in text for label in ('rules','verification','limits','next step')) and len(text)>100


def score(case_id, workspace, initial, seconds=60):
    workspace=Path(workspace).resolve();spec=cases()[case_id]
    mutable=set(spec['mutable'])
    drift=[name for name,digest in initial.items() if name not in mutable and
           (not (workspace/name).is_file() or (workspace/name).is_symlink() or sha(workspace/name)!=digest)]
    groups={};logs={};deadline=time.monotonic()+seconds
    if case_id=='sales_import':
        for method in spec['groups']:
            command=[sys.executable,'-B','-m','unittest','-v',f'test_engine.ImportTests.{method}']
            try:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise subprocess.TimeoutExpired(command,seconds)
                proc=subprocess.run(command,cwd=workspace,capture_output=True,text=True,timeout=min(20,remaining))
                text=proc.stdout+proc.stderr
                passed=proc.returncode==0 and 'Ran 1 test' in text
                logs[method]={'command':command,'exit_code':proc.returncode,'output':text}
            except subprocess.TimeoutExpired:
                passed=False;logs[method]={'command':command,'timeout':True}
            groups[method]=passed
    else:
        try:actual=read(workspace/'decision.json')
        except (ValueError,OSError):actual={}
        if not isinstance(actual,dict):actual={}
        for name,expected in spec['expected'].items():
            groups[name]=type(actual.get(name)) is type(expected) and actual.get(name)==expected
        brief=workspace/'BRIEF.md'
        groups['brief_state']=headings(workspace/'STATE.md') and brief.is_file() and len(brief.read_text())>200
        if set(actual)!=set(spec['expected']):groups['decision']=False
        logs['actual']=actual
    points=sum(weight for name,weight in spec['groups'].items() if groups.get(name))
    state_ok=headings(workspace/'STATE.md')
    return {'status':'PASS' if points==100 and not drift and state_ok else 'FAIL',
            'score':points if not drift else 0,'groups':groups,'protected_drift':drift,
            'state_present_and_structured':state_ok,'evidence':logs}
