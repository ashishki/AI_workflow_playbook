#!/usr/bin/env python3
"""Prepare and score a bounded Controlled Delegation experiment. No model calls."""
from __future__ import annotations
import argparse, json, random, shutil, statistics, subprocess, sys
from collections import defaultdict
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = next((p for p in (HERE, *HERE.parents) if (p/'plugins/playbook-native/skills').is_dir()), HERE)
SUITE = HERE/'suite.json'
RUN_SCHEMA = 'playbook.controlled_delegation.run.v1'
RESULTS_SCHEMA = 'playbook.controlled_delegation.results.v1'
STATUSES = {'PASS','FAIL','BLOCKED','NOT_RUN'}

class ExperimentError(ValueError): pass

def strict_json(path: Path):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise ExperimentError(f'Duplicate JSON key in {path}: {k}')
            out[k]=v
        return out
    def constant(value): raise ExperimentError(f'Non-finite JSON number in {path}: {value}')
    try: value=json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,parse_constant=constant)
    except (OSError,UnicodeError,json.JSONDecodeError) as exc: raise ExperimentError(f'Invalid JSON: {path}') from exc
    if not isinstance(value,dict): raise ExperimentError(f'Expected JSON object: {path}')
    return value

def write_json(path: Path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def safe_rel(value):
    if not isinstance(value,str) or not value: raise ExperimentError('Empty path')
    p=PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or '\\' in value: raise ExperimentError(f'Unsafe path: {value}')
    return p.as_posix()

def load_manifest():
    m=strict_json(SUITE)
    if m.get('schema')!='playbook.controlled_delegation.experiment.v1': raise ExperimentError('Unsupported suite')
    cs,ss=m.get('conditions'),m.get('scenarios')
    if not isinstance(cs,list) or [x.get('id') for x in cs]!=['A','B','C']: raise ExperimentError('Need A/B/C')
    if not isinstance(ss,list) or not ss or len({x.get('id') for x in ss})!=len(ss): raise ExperimentError('Invalid scenarios')
    for c in cs:
        if not isinstance(c.get('instructions'),str): raise ExperimentError('Missing condition instructions')
    for s in ss:
        if not isinstance(s.get('task'),str) or not isinstance(s.get('files'),dict) or not s['files']: raise ExperimentError('Missing task/files')
        seen=set()
        for name,content in s['files'].items():
            key=safe_rel(name)
            if key in seen or not isinstance(content,str): raise ExperimentError('Invalid embedded file')
            seen.add(key)
    return m

def empty_run(s,c):
    return {'schema':RUN_SCHEMA,'scenario':s,'condition':c,'status':'NOT_RUN','outcome_score':None,
      'critical_errors':0,'subagents_started':0,'max_parallel':0,'max_depth':0,'owner_checkpoints':0,
      'human_minutes':None,'wall_seconds':None,'input_tokens':None,'output_tokens':None,'cost_usd':None,
      'approval_noise':0,'write_conflicts':0,'failed_or_conflicting_worker_detected':None,
      'fresh_session_success':None,'usage_complete':None,'task_status':None,
      'implementation_subagents_started':None,'review_subagents_started':None,'evidence':[],'notes':''}

def implementation_count(run):
    """Reviews are recorded separately from implementation/research delegation."""
    value=run.get('implementation_subagents_started')
    return value if value is not None else run['subagents_started']-(run.get('review_subagents_started') or 0)

def task_observed(run):
    """A blocked preflight's default zero counters are not a failed task run."""
    return run['status'] in {'PASS','FAIL'} or run.get('task_status') in {'PASS','FAIL'}

def prepare(output: Path, *, seed:int, head:str, model:str, host:str):
    m=load_manifest(); skills=ROOT/'plugins/playbook-native/skills'
    if not skills.is_dir(): raise ExperimentError('Run from a complete Playbook checkout')
    output=output.resolve()
    if output.exists() and any(output.iterdir()): raise ExperimentError(f'Output not empty: {output}')
    output.mkdir(parents=True,exist_ok=True)
    conditions={x['id']:x for x in m['conditions']}; order=[]; runs=[]
    for s in m['scenarios']:
        for cid,c in conditions.items():
            w=output/'workspaces'/s['id']/cid; w.mkdir(parents=True)
            for name,content in s['files'].items():
                p=w/safe_rel(name); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding='utf-8')
            if c['playbook']: shutil.copytree(skills,w/'.agents/skills')
            bounds=(f"\n\nScenario implementation/research worker bound: {s.get('min_subagents_c',0)}–{s.get('max_subagents_c',3)}. "
                    "Independent reviewers are recorded separately; do not count a reviewer as an implementation/research worker."
                    if cid=='C' else '')
            (w/'AGENTS.md').write_text(f"# Experiment condition {cid}\n\nWork only inside this workspace. Do not read sibling workspaces. Do not commit/push. Preserve evidence locally.\n\n{c['instructions'].strip()}{bounds}\n",encoding='utf-8')
            (w/'TASK.md').write_text(f"# Scenario {s['id']} / condition {cid}\n\n{s['task'].strip()}\n\n## Run record\nCreate `run-result.json` from `RUN_RESULT_TEMPLATE.json`. Record observed values only; PASS needs existing evidence files.\n",encoding='utf-8')
            write_json(w/'RUN_RESULT_TEMPLATE.json',empty_run(s['id'],cid))
            order.append({'scenario':s['id'],'condition':cid,'workspace':w.relative_to(output).as_posix()})
            runs.append(empty_run(s['id'],cid))
    random.Random(seed).shuffle(order)
    write_json(output/'run-plan.json',{'schema':'playbook.controlled_delegation.plan.v1','experiment_id':m['experiment_id'],'seed':seed,'head':head,'model':model,'host':host,'order':order})
    write_json(output/'results.json',{'schema':RESULTS_SCHEMA,'experiment_id':m['experiment_id'],'environment':{'head':head,'model':model,'host':host,'permissions':'record exact value','operator':'record exact value'},'runs':runs})
    return {'status':'prepared','output':str(output),'workspaces':len(order),'plan':str(output/'run-plan.json'),'results':str(output/'results.json')}
