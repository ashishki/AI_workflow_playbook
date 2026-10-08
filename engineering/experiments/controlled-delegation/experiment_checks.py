"""Mechanical collection and validation for Controlled Delegation. No model calls."""
from __future__ import annotations
import math, subprocess, sys
from pathlib import Path
from experiment_core import (ExperimentError, RUN_SCHEMA, RESULTS_SCHEMA, STATUSES,
    empty_run, implementation_count, load_manifest, safe_rel, strict_json, task_observed, write_json)

def unit_check(w):
    r=subprocess.run([sys.executable,'-m','unittest','discover','-v'],cwd=w,capture_output=True,text=True,encoding='utf-8',timeout=120)
    return {'status':'PASS' if r.returncode==0 else 'FAIL','returncode':r.returncode,'stdout':r.stdout[-12000:],'stderr':r.stderr[-12000:]}

def check_workspace(scenario, workspace:Path):
    w=workspace.resolve()
    if not w.is_dir(): raise ExperimentError(f'Missing workspace: {w}')
    fixture=next((s for s in load_manifest()['scenarios'] if s['id']==scenario),None)
    if fixture is None: raise ExperimentError(f'Unknown scenario: {scenario}')
    mutable={'small_fix':{'budget.py'},'medium_implementation':{'lead_router/router.py'},'fresh_session':{'router.py'}}.get(scenario,set())
    errors=[]
    for name,original in fixture['files'].items():
        path=w/name
        if not path.is_file(): errors.append(f'Missing fixture: {name}')
        elif not path.resolve().is_relative_to(w): errors.append(f'Fixture escapes workspace: {name}')
        elif name not in mutable and path.read_text(encoding='utf-8')!=original: errors.append(f'Changed protected fixture: {name}')
    if errors: return {'status':'FAIL','fixture_errors':errors}
    if scenario in {'small_fix','medium_implementation','fresh_session'}:
        r=unit_check(w)
        if scenario=='medium_implementation':
            r['state_present']=(w/'STATE.md').is_file(); r['status']='PASS' if r['status']=='PASS' and r['state_present'] else 'FAIL'
        if scenario=='fresh_session':
            d=strict_json(w/'decision.json') if (w/'decision.json').is_file() else {}
            req={'state_present':(w/'STATE.json').is_file(),'handoff_present':(w/'HANDOFF.md').is_file(),'decision_present':(w/'decision.json').is_file(),'fresh_session_claimed':d.get('fresh_session') is True,'old_behavior_preserved':d.get('old_behavior_preserved') is True}
            r.update(req); r['status']='PASS' if r['status']=='PASS' and all(req.values()) else 'FAIL'
        return r
    d=strict_json(w/'decision.json') if (w/'decision.json').is_file() else {}
    checks = ({'decision_none':d.get('decision')=='none','alpha_missing_audit':d.get('alpha_missing_audit_log') is True,'beta_over_budget':d.get('beta_over_budget') is True,'beta_not_eu_only':d.get('beta_not_eu_only') is True}
      if scenario=='parallel_research' else
      {'reject_stale':d.get('decision')=='reject_stale_summary','conflict_detected':d.get('conflict_detected') is True,'none_recommended':d.get('recommended_option')=='none'} if scenario=='conflict_detection' else None)
    if checks is None: raise ExperimentError(f'Unknown scenario: {scenario}')
    checks['explanation_present']=isinstance(d.get('explanation'),str) and bool(d['explanation'].strip())
    if scenario=='parallel_research': checks['exact_business_fields']=set(d)=={'decision','alpha_missing_audit_log','beta_over_budget','beta_not_eu_only','explanation'}
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}

def validate_run(r,scenarios,conditions):
    if r.get('schema')!=RUN_SCHEMA or r.get('scenario') not in scenarios or r.get('condition') not in conditions or r.get('status') not in STATUSES: raise ExperimentError('Invalid run identity/status')
    for f in ('failed_or_conflicting_worker_detected','fresh_session_success','usage_complete'):
        if r.get(f) is not None and not isinstance(r[f],bool): raise ExperimentError(f'Invalid boolean confirmation: {f}')
    if r.get('task_status') is not None and r['task_status'] not in STATUSES: raise ExperimentError('Invalid task_status')
    if r.get('mechanical') is not None and (not isinstance(r['mechanical'],dict) or r['mechanical'].get('status') not in STATUSES): raise ExperimentError('Invalid mechanical status')
    for f in ('critical_errors','subagents_started','max_parallel','max_depth','owner_checkpoints','approval_noise','write_conflicts'):
        v=r.get(f)
        if not isinstance(v,int) or isinstance(v,bool) or v<0: raise ExperimentError(f'Invalid {f}')
    for f in ('implementation_subagents_started','review_subagents_started'):
        v=r.get(f)
        if v is not None and (not isinstance(v,int) or isinstance(v,bool) or not 0<=v<=r['subagents_started']): raise ExperimentError(f'Invalid {f}')
    if all(r.get(f) is not None for f in ('implementation_subagents_started','review_subagents_started')) and r['implementation_subagents_started']+r['review_subagents_started']!=r['subagents_started']: raise ExperimentError('Inconsistent worker/reviewer counts')
    score=r.get('outcome_score')
    if score is not None and (not isinstance(score,(int,float)) or isinstance(score,bool) or not 0<=score<=100): raise ExperimentError('Invalid outcome_score')
    for f in ('human_minutes','wall_seconds','input_tokens','output_tokens','cost_usd'):
        v=r.get(f)
        if v is not None and (not isinstance(v,(int,float)) or isinstance(v,bool) or v<0 or isinstance(v,float) and not math.isfinite(v)): raise ExperimentError(f'Invalid {f}')
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
        if r.get('task_status')=='FAIL':r['status']='FAIL'
        if r.get('status')=='PASS' and (missing or r['mechanical']['status']!='PASS'):
            r['status']='FAIL'; r['notes']=(str(r.get('notes',''))+' Mechanical/evidence acceptance failed.').strip()
        if r.get('condition')=='C' and task_observed(r):
            spec=next(s for s in load_manifest()['scenarios'] if s['id']==item['scenario'])
            if not spec.get('min_subagents_c',0)<=implementation_count(r)<=spec.get('max_subagents_c',3):
                r['status']='FAIL'; r['notes']+=' Implementation/research worker bound violated.'
        if r.get('status')=='PASS' and (r.get('usage_complete') is not True or any(r.get(f) is None for f in ('input_tokens','output_tokens','cost_usd'))):
            r['status']='BLOCKED'; r['notes']+=' Required host usage/cost evidence unavailable (VPS prompt step 6).'
        out.append(r)
    value={**base,'runs':sorted(out,key=lambda x:(x['scenario'],x['condition']))}; validate_results(value); write_json(output,value)
    return {'status':'collected','output':str(output),'runs':len(out)}
