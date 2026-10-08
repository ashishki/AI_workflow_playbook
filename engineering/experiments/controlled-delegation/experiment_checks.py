"""Mechanical collection and validation for Controlled Delegation. No model calls."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
from experiment_core import (ExperimentError, RUN_SCHEMA, RESULTS_SCHEMA, STATUSES,
    empty_run, load_manifest, safe_rel, strict_json, write_json)

def unit_check(w):
    r=subprocess.run([sys.executable,'-m','unittest','discover','-v'],cwd=w,capture_output=True,text=True,encoding='utf-8',timeout=120)
    return {'status':'PASS' if r.returncode==0 else 'FAIL','returncode':r.returncode,'stdout':r.stdout[-12000:],'stderr':r.stderr[-12000:]}

def check_workspace(scenario, workspace:Path):
    w=workspace.resolve()
    if not w.is_dir(): raise ExperimentError(f'Missing workspace: {w}')
    if scenario in {'small_fix','medium_implementation','fresh_session'}:
        r=unit_check(w)
        if scenario=='medium_implementation':
            r['state_present']=(w/'STATE.md').is_file(); r['status']='PASS' if r['status']=='PASS' and r['state_present'] else 'FAIL'
        if scenario=='fresh_session':
            d=strict_json(w/'decision.json') if (w/'decision.json').is_file() else {}
            req={'state_present':(w/'STATE.json').is_file(),'handoff_present':(w/'HANDOFF.md').is_file(),'decision_present':(w/'decision.json').is_file(),'fresh_session_claimed':d.get('fresh_session') is True}
            r.update(req); r['status']='PASS' if r['status']=='PASS' and all(req.values()) else 'FAIL'
        return r
    d=strict_json(w/'decision.json') if (w/'decision.json').is_file() else {}
    checks = ({'decision_none':d.get('decision')=='none','alpha_missing_audit':d.get('alpha_missing_audit_log') is True,'beta_over_budget':d.get('beta_over_budget') is True,'beta_not_eu_only':d.get('beta_not_eu_only') is True}
      if scenario=='parallel_research' else
      {'reject_stale':d.get('decision')=='reject_stale_summary','conflict_detected':d.get('conflict_detected') is True,'none_recommended':d.get('recommended_option')=='none'} if scenario=='conflict_detection' else None)
    if checks is None: raise ExperimentError(f'Unknown scenario: {scenario}')
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}

def validate_run(r,scenarios,conditions):
    if r.get('schema')!=RUN_SCHEMA or r.get('scenario') not in scenarios or r.get('condition') not in conditions or r.get('status') not in STATUSES: raise ExperimentError('Invalid run identity/status')
    for f in ('critical_errors','subagents_started','max_parallel','max_depth','owner_checkpoints','approval_noise','write_conflicts'):
        v=r.get(f)
        if not isinstance(v,int) or isinstance(v,bool) or v<0: raise ExperimentError(f'Invalid {f}')
    score=r.get('outcome_score')
    if score is not None and (not isinstance(score,(int,float)) or isinstance(score,bool) or not 0<=score<=100): raise ExperimentError('Invalid outcome_score')
    for f in ('human_minutes','wall_seconds','input_tokens','output_tokens','cost_usd'):
        v=r.get(f)
        if v is not None and (not isinstance(v,(int,float)) or isinstance(v,bool) or v<0): raise ExperimentError(f'Invalid {f}')
    ev=r.get('evidence')
    if not isinstance(ev,list): raise ExperimentError('evidence must be list')
    for x in ev: safe_rel(x)
    if r['status']=='PASS' and not ev: raise ExperimentError('PASS needs evidence')

def validate_results(v):
    m=load_manifest(); runs=v.get('runs')
    if v.get('schema')!=RESULTS_SCHEMA or v.get('experiment_id')!=m['experiment_id'] or not isinstance(runs,list): raise ExperimentError('Invalid results')
    ss={x['id'] for x in m['scenarios']}; cs={x['id'] for x in m['conditions']}; expected={(s,c) for s in ss for c in cs}; seen=set()
    for r in runs:
        if not isinstance(r,dict): raise ExperimentError('Run must be object')
        validate_run(r,ss,cs); key=(r['scenario'],r['condition'])
        if key in seen: raise ExperimentError(f'Duplicate run {key}')
        seen.add(key)
    if seen!=expected: raise ExperimentError(f'Missing runs: {sorted(expected-seen)}')
    return m

def collect(run_root:Path, output:Path):
    root=run_root.resolve(); plan=strict_json(root/'run-plan.json'); base=strict_json(root/'results.json'); out=[]
    if plan.get('experiment_id')!=base.get('experiment_id'): raise ExperimentError('Mismatched plan/results')
    for item in plan.get('order',[]):
        w=root/item['workspace']; path=w/'run-result.json'; r=strict_json(path) if path.is_file() else empty_run(item['scenario'],item['condition'])
        missing=[]
        for x in r.get('evidence',[]) if isinstance(r.get('evidence'),list) else []:
            try: rel=safe_rel(x)
            except ExperimentError: missing.append(str(x)); continue
            if not (w/rel).is_file(): missing.append(rel)
        r['missing_evidence']=missing; r['mechanical']=check_workspace(item['scenario'],w)
        if r.get('status')=='PASS' and (missing or r['mechanical']['status']!='PASS'):
            r['status']='FAIL'; r['notes']=(str(r.get('notes',''))+' Mechanical/evidence acceptance failed.').strip()
        out.append(r)
    value={**base,'runs':sorted(out,key=lambda x:(x['scenario'],x['condition']))}; validate_results(value); write_json(output,value)
    return {'status':'collected','output':str(output),'runs':len(out)}
