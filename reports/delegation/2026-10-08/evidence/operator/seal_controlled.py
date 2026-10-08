"""Offline evidence extraction. Run only after all genuine host sessions finish."""
import collections, hashlib, json, pathlib, shutil, sys

repo=pathlib.Path.cwd()
root=repo/'.playbook-artifacts/controlled-delegation'
report=repo/'reports/delegation/2026-10-08'
report.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(repo/'engineering/experiments/controlled-delegation'))
from experiment_core import empty_run,strict_json,write_json
from experiment_checks import check_workspace

def read_events(path):
    events=[]
    for line in path.read_text().splitlines():
        if line.strip(): events.append(json.loads(line))
    return events

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

sessions={}
for p in pathlib.Path('/root/.codex/sessions/2026/10/08').glob('*.jsonl'):
    with p.open() as f:
        first=json.loads(f.readline())
    meta=first.get('payload',{})
    if str(root/'workspaces') not in meta.get('cwd',''):continue
    events=read_events(p); context=None; usage=None; end=None; active=None; intervals=[]
    for e in events:
        x=e.get('payload',{})
        if e['type']=='turn_context':context={k:x.get(k) for k in ('model','effort','approval_policy','sandbox_policy','cwd')}
        if e['type']=='event_msg' and x.get('type')=='token_count' and x.get('info'):usage=x['info'].get('total_token_usage')
        if e['type']=='event_msg' and x.get('type')=='task_started' and active is None: active=e['timestamp']
        if e['type']=='event_msg' and x.get('type')=='task_complete':
            end=e['timestamp']
            if active:intervals.append([active,end]);active=None
    if active:intervals.append([active,None])
    sessions[meta['id']]={'id':meta['id'],'source':meta.get('source'),'cwd':meta['cwd'],
        'start':first['timestamp'],'end':end,'active_intervals':intervals,'context':context,'usage':usage,'raw':p}

def parent(s):
    src=s.get('source')
    return src.get('subagent',{}).get('thread_spawn',{}).get('parent_thread_id') if isinstance(src,dict) else None

def nested(s,ids):
    p=parent(s)
    return bool(p and (p in ids or p in sessions and nested(sessions[p],ids)))

plan=strict_json(root/'run-plan.json'); all_receipts=[]
for item in plan['order']:
    w=root/item['workspace']; logs=w/'.playbook-artifacts'
    operator=strict_json(logs/'initial-sha256.json')
    ops=json.loads((logs/'operator-sessions.json').read_text())
    expected=2 if item['scenario']=='fresh_session' else 1
    if len(ops)!=expected:raise RuntimeError(f'Incomplete sessions: {w}')
    ids={i for op in ops for i in op['thread_ids']}
    local=[s for s in sessions.values() if s['id'] in ids or nested(s,ids)]
    native=[s for s in local if s['id'] not in ids]
    external=[]
    for p in logs.rglob('codex_events.jsonl'):
        events=read_events(p)
        extids=[e['thread_id'] for e in events if e.get('type')=='thread.started']
        usages=[e['usage'] for e in events if e.get('type')=='turn.completed']
        if not extids: continue
        if any(i in sessions for i in extids): continue
        external.append({'id':extids[0],'source':'native_role_runner_read_only_review',
            'usage':usages[-1] if usages else None,'completed':bool(usages),'raw':p})
    # Preserve model claims, then replace metrics with host observations.
    rawrecord=logs/'agent-run-result.json'
    if not rawrecord.exists() and (w/'run-result.json').exists():shutil.copyfile(w/'run-result.json',rawrecord)
    r=strict_json(rawrecord) if rawrecord.exists() else empty_run(item['scenario'],item['condition'])
    mechanics=check_workspace(item['scenario'],w)
    complete=all(op['returncode']==0 and op['completed'] and not op['timeout'] for op in ops)
    r['agent_reported_status']=r['status']
    r['task_status']='PASS' if mechanics['status']=='PASS' and complete and r['agent_reported_status']=='PASS' else 'FAIL'
    r['mechanical_outcome_status']=mechanics['status']
    r['wall_seconds']=round(sum(op['wall_seconds'] for op in ops),3)
    totals=collections.Counter()
    for s in local+external:
        if s['usage']:
            totals.update({k:v for k,v in s['usage'].items() if isinstance(v,int)})
    r['input_tokens']=totals.get('input_tokens')
    r['output_tokens']=totals.get('output_tokens')
    r['cached_input_tokens']=totals.get('cached_input_tokens')
    r['reasoning_output_tokens']=totals.get('reasoning_output_tokens')
    r['uncached_input_tokens']=r['input_tokens']-r['cached_input_tokens'] if r['input_tokens'] is not None and r['cached_input_tokens'] is not None else None
    r['cost_usd']=None; r['human_minutes']=None; r['outcome_score']=None
    r['subagents_started']=len(native)+len(external)
    points=[]
    for s in native:
        for start,end in s['active_intervals']:
            points.extend([(start,1),(end or '9999',-1)])
    current=maximum=0
    for _,delta in sorted(points,key=lambda x:(x[0],x[1])):
        current+=delta;maximum=max(maximum,current)
    r['max_parallel']=max(maximum,1 if external else 0)
    depths=[s['source']['subagent']['thread_spawn']['depth'] for s in native]
    r['max_depth']=max(depths+[1 if external else 0])
    r['native_subagents_started']=len(native)
    r['external_review_sessions_started']=len(external)
    def is_reviewer(s):
        name=s['source']['subagent']['thread_spawn'].get('agent_path','').split('/')[-1]
        return name in ('independent_review','independent_reviewer','reviewer','code_review','slice_review','review')
    r['review_subagents_started']=sum(is_reviewer(s) for s in native)+len(external)
    r['implementation_subagents_started']=r['subagents_started']-r['review_subagents_started']
    r['usage_scope']='Sum of distinct main, native child and Role Runner review sessions; excludes coordinating parent Codex task and test runner overhead.'
    r['usage_complete']=complete and all(s.get('usage') is not None for s in local+external) and len([s for s in local if s['id'] in ids])==expected
    r['measurement_status']='BLOCKED'
    r['measurement_blockers']=['Actual USD cost not exposed by ChatGPT-authenticated host.', 'Owner active time not measured; no invented zero or saving.']
    r['status']='FAIL' if r['task_status']=='FAIL' else 'BLOCKED'
    r['notes']+=' Operator: live task outcome recorded separately; experiment acceptance BLOCKED because actual USD cost/owner-time measurement is unavailable (VPS prompt step 6). Outcome score has no preregistered rubric and remains null.'
    if not complete:
        r['notes']+=' Host execution did not finish within the fixed session budget; this is FAIL, even if the mechanical output is correct. Tokens are observed counters through interruption, not a complete billing receipt.'
    if item['scenario']=='parallel_research' and item['condition']=='C' and not complete:
        r['failed_or_conflicting_worker_detected']=True
        r['failure_observation']='Main explicitly saved BLOCKED pending a non-returning additional review from the existing constraints worker; operator then enforced 600-second budget.'
    # Verify original tests and source task/instructions were not weakened.
    protected=[n for n in operator if pathlib.PurePosixPath(n).name in ('AGENTS.md','TASK.md','RUN_RESULT_TEMPLATE.json') or pathlib.PurePosixPath(n).name.startswith('test_')]
    drift=[n for n in protected if not (w/n).is_file() or digest(w/n)!=operator[n]]
    r['protected_files_unchanged']=not drift
    if drift:r['status']='FAIL';r['task_status']='FAIL';r['critical_errors']+=1;r['notes']+=f' Protected-file drift: {drift}.'
    if item['scenario']=='fresh_session':
        raw_phase1=read_events(logs/'phase-1-events.jsonl')
        phase1_code=[c['path'] for e in raw_phase1 for c in e.get('item',{}).get('changes',[]) if pathlib.Path(c['path']).name in ('router.py','test_router.py')]
        r['fresh_session_success']=complete and len(ids)==2 and not phase1_code and mechanics['status']=='PASS'
        r['phase1_code_changes']=phase1_code
    # Keep raw rollouts locally; export only metadata, hashes and synthetic outputs.
    archive=logs/'host-rollouts';archive.mkdir(exist_ok=True)
    public_sessions=[]
    for s in local+external:
        if s['id'] in sessions:
            dest=archive/(s['id']+'.jsonl')
            shutil.copyfile(s['raw'],dest)
            raw=dest
        else:raw=s['raw']
        public_sessions.append({**{k:v for k,v in s.items() if k!='raw'},'raw_path':raw.relative_to(root).as_posix(),'sha256':digest(raw)})
    r['evidence']=list(dict.fromkeys(r.get('evidence',[])+['.playbook-artifacts/operator-sessions.json','.playbook-artifacts/operator-mechanical.json','.playbook-artifacts/initial-sha256.json','.playbook-artifacts/agent-run-result.json']+[op['events'] for op in ops]+[p.relative_to(w).as_posix() for p in archive.glob('*.jsonl')]))
    missing=[x for x in r['evidence'] if not (w/x).is_file()]
    if missing:r['status']='FAIL';r['notes']+=f' Missing evidence: {missing}.'
    outputs={}
    for n in ('budget.py','lead_router/router.py','router.py','decision.json','STATE.json','STATE.md','HANDOFF.md'):
        if (w/n).is_file():outputs[n]=(w/n).read_text()
    receipt={'scenario':item['scenario'],'condition':item['condition'],'workspace':item['workspace'],
        'operator_sessions':ops,'host_sessions':public_sessions,'mechanical':mechanics,
        'protected_file_drift':drift,'synthetic_outputs':outputs,
        'files':[{'path':(w/x).relative_to(root).as_posix(),'sha256':digest(w/x),'bytes':(w/x).stat().st_size} for x in r['evidence'] if (w/x).is_file()]}
    receipt_path=report/'evidence'/f'{item["scenario"]}-{item["condition"]}.json'
    write_json(receipt_path,receipt)
    r['published_receipt']=receipt_path.relative_to(report).as_posix()
    write_json(w/'run-result.json',r)
    all_receipts.append({'path':receipt_path.relative_to(report).as_posix(),'sha256':digest(receipt_path)})
write_json(report/'evidence-index.json',{'raw_root':root.relative_to(repo).as_posix(),'head':plan['head'],'receipts':all_receipts})
shutil.copyfile(root/'run-plan.json',report/'run-plan.json')
print('Sealed 15 actual run records; raw transcripts remain local.')
