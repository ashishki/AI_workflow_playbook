#!/usr/bin/env python3
"""Preregister, run, and report real repeated A/B/C tasks. No simulated fallback."""
from __future__ import annotations
import argparse
import datetime
import json
import random
import shutil
import statistics
import subprocess
import sys
import time
import uuid
from pathlib import Path
from round2_checks import read, score, sha, write
from round2_fixtures import cases
from round2_host import capture_threads, environment, events, execute, setup_bin

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
EXPERIMENT='controlled-delegation-round2-2026-10-08'
TOTAL_SECONDS=540
MAIN_SECONDS=300
REVIEW_SECONDS=90

COMMON='''Read AGENTS.md and TASK.md. Complete the synthetic task using only files in this workspace; do not read sibling workspaces, the parent repository, hidden evaluator or other sessions. No network/accounts/dependency installs/commit/push. Tests and supplied source data/money_exact.py are frozen. Use Python through the local python command. Native workers, if allowed by your condition, keep inherited model/reasoning, depth one, maximum three simultaneous; no workers start workers. Workers are read-only and return concise source findings, without reviews. Do not reuse or send follow-ups to completed workers. Give each worker 60 seconds within your 300-second implementation budget; on a missing return interrupt it, check sources yourself and record the limitation. Do not run any reviewers: the operator runs the same independent review after code work in every condition. No extra review is required for text-only work. Do not create run-result.json or elaborate evidence logs; the operator captures genuine host traces and commands. Write short STATE.md with headings Rules, Verification, Limits, Next step, recording only actually observed checks. No owner business decisions or routine approvals are needed. Finish after the requested outputs and checks. The entire task budget, including external review and one optional repair, is 540 seconds; implementation gets at most 300 seconds.'''


def prepare(root, head, model, reasoning, repeats=2, seed=20261008):
    root=Path(root).resolve()
    if root.exists() and any(root.iterdir()):raise ValueError('refuse to overwrite experiment root')
    root.mkdir(parents=True,exist_ok=True)
    plan={'schema':'playbook.delegation.round2.plan.v1','experiment_id':EXPERIMENT,
          'head':head,'model':model,'reasoning':reasoning,'repeats':repeats,'seed':seed,
          'implementation_seconds':MAIN_SECONDS,'total_seconds':TOTAL_SECONDS,
          'review_seconds':REVIEW_SECONDS,'worker_seconds':60,
          'review_policy':'same blinded native Role Runner after all code implementations; maximum one repair, same feedback order',
          'cost_policy':'actual token counters; USD null without billing receipt; no pricing guess',
          'human_policy':'owner requests observable; active human minutes null without participation',
          'order':[],'rubric':{name:spec['groups'] for name,spec in cases().items()}}
    rng=random.Random(seed)
    blocks=[(name,repeat) for name in cases() for repeat in range(1,repeats+1)]
    rng.shuffle(blocks)
    for name,repeat in blocks:
        order=list('ABC');rng.shuffle(order)
        for condition in order:
            spec=cases()[name];run_id=uuid.uuid4().hex[:12];w=root/'workspaces'/run_id;w.mkdir(parents=True)
            for filename,content in spec['files'].items():
                dest=w/filename;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content)
            shutil.copyfile(HERE/'money_exact.py',w/'money_exact.py')
            if condition in 'BC':shutil.copytree(REPO/'plugins/playbook-native/skills',w/'.agents/skills')
            instruction={
              'A':'Ordinary Codex baseline: do not load/copy Playbook. Choose ordinary host behavior for task work.',
              'B':'Use the installed Playbook for task work and continuity. All implementation/research remains in this main session; no native workers. Common independent code review is performed by the operator afterwards.',
              'C':'Use Playbook and its delegation reference. Choose delegate for these independent analysis streams: start 2 or 3 read-only native workers, each assigned a distinct useful source/spec/test audit. Main remains the sole writer and integrates actual returns. Record route/scope briefly. Depth one; no reviewer or follow-up worker reuse.'}[condition]
            (w/'AGENTS.md').write_text('# Isolated task workspace\n\nWork only here. No sibling/parent reads or commit/push.\n\n'+instruction+'\n')
            (w/'TASK.md').write_text(spec['task']+'\n\nSTATE headings: Rules, Verification, Limits, Next step. Independent code review is performed externally and identically for A/B/C.\n')
            subprocess.run(['git','init','-q','-b','benchmark-round2',str(w)],check=True)
            initial={p.relative_to(w).as_posix():sha(p) for p in w.rglob('*') if p.is_file() and '.git' not in p.parts}
            write(root/'initial'/f'{run_id}.json',initial)
            plan['order'].append({'id':run_id,'case':name,'repeat':repeat,'condition':condition,'workspace':w.relative_to(root).as_posix()})
    write(root/'run-plan.json',plan)
    write(root/'source-sha256.json',{p.name:sha(p) for p in HERE.glob('round2*.py')}|{'money_exact.py':sha(HERE/'money_exact.py')})
    return {'status':'PREPARED','runs':len(plan['order']),'root':str(root)}


def review(root, item, workspace, mechanical, wrapper, label, seconds):
    """Fresh common reviewer: condition/old chat/raw worker logs not supplied."""
    target=root/'review-workspaces'/uuid.uuid4().hex;target.mkdir(parents=True)
    initial=read(root/'initial'/f'{item["id"]}.json')
    for name in initial:
        if name.startswith('.agents/') or name=='AGENTS.md':continue
        source=workspace/name
        if source.is_file():
            dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    (target/'AGENTS.md').write_text('Independent read-only code review. Do not delegate, write files, use network or accounts.\n')
    write(target/'OBSERVED_CHECKS.json',mechanical)
    request=target/'.playbook-artifacts/request.md';request.parent.mkdir()
    request.write_text('Review engine.py against TASK.md and frozen tests/money_exact.py. Inspect OBSERVED_CHECKS.json from actually executed operator tests. Look for real unmet contract, transaction/idempotency/concurrency and exact-cents defects. Check STATE claims. Do not rerun filesystem-writing tests in read-only sandbox; their captured output is available. Do not read sibling/parent workspaces or experiment condition. No writes, networking, installs or subagents. Return the Role Runner slice_review marker: PASS if no material findings; ADVISORY for minor documentation issues; STOP_SHIP for incorrect behavior, invalid evidence, or unmet contract. Keep findings concise. Budget '+str(seconds)+' seconds.\n')
    command=[sys.executable,str(REPO/'tools/run_codex_role.py'),'run','--profile','native','--root',str(target),
             '--task','blinded-code-check','--role','slice_review','--request','.playbook-artifacts/request.md',
             '--model',read(root/'run-plan.json')['model'],'--reasoning-effort',read(root/'run-plan.json')['reasoning'],
             '--timeout-seconds',str(max(1,int(seconds))),'--codex-bin',str(wrapper),'--no-publish']
    started=time.monotonic();logs=root/'logs'/item['id'];logs.mkdir(exist_ok=True)
    proc=subprocess.run(command,env=environment(wrapper.parent),capture_output=True,text=True,timeout=seconds+20)
    (logs/f'{label}.stdout.txt').write_text(proc.stdout);(logs/f'{label}.stderr.txt').write_text(proc.stderr)
    try:result=json.loads(proc.stdout)
    except ValueError:result={'status':'BLOCKED','verdict':None,'reason':proc.stderr}
    summary={'kind':'independent_review','status':result.get('status'),'verdict':result.get('verdict'),
             'exit_code':proc.returncode,'wall_seconds':round(time.monotonic()-started,3),'workspace':str(target),
             'reviewed_engine_sha256':sha(target/'engine.py')}
    if result.get('result'):
        stored=Path(result['result']);summary['result']=str(stored)
        document=stored.parent/'report.md';summary['report']=document.read_text() if document.is_file() else ''
        emitted=events(stored.parent/'codex_events.jsonl')
        summary['usage']=[e['usage'] for e in emitted if e.get('type')=='turn.completed']
        summary['thread_ids']=[e['thread_id'] for e in emitted if e.get('type')=='thread.started']
        summary['trace_sha256']=sha(stored.parent/'codex_events.jsonl')
    write(logs/f'{label}.receipt.json',summary)
    return summary


def telemetry(root, workspace, phases, qa, wrapper):
    ids=[i for phase in phases for i in phase['thread_ids']]
    captured=capture_threads(workspace,ids,root/'logs'/workspace.name/'rollouts')
    native=[x for x in captured if isinstance(x['source'],dict)]
    totals={'input_tokens':0,'output_tokens':0,'cached_input_tokens':0}
    complete=all(x['completed'] for x in phases)
    # Persistent host counters are separate per thread. No double counting CLI usage.
    for entry in captured:
        if not entry['task_completed']:complete=False
        if not entry['usage']:complete=False;continue
        for key in totals:totals[key]+=entry['usage'].get(key,0)
    if len([x for x in captured if x['id'] in ids])!=len(ids):complete=False
    for entry in qa:
        if not entry.get('usage'):complete=False
        for usage in entry.get('usage',[]):
            for key in totals:totals[key]+=usage.get(key,0)
    points=[]
    for entry in native:
        for start,end in entry['intervals']:points.extend([(start,1),(end or '9999',-1)])
    live=maximum=0
    for _,delta in sorted(points,key=lambda x:(x[0],x[1])):live+=delta;maximum=max(live,maximum)
    contexts=[x['context'] for x in captured]
    plan=read(root/'run-plan.json')
    settings_ok=bool(ids) and len([x for x in captured if x['id'] in ids])==len(ids) and all(c and c['model']==plan['model'] and c['effort']==plan['reasoning'] for c in contexts)
    return dict(totals,usage_complete=complete,settings_verified=settings_ok,
                workers=len(native),max_parallel=maximum,
                max_depth=max([x['source']['subagent']['thread_spawn']['depth'] for x in native]+[0]),
                completed_worker_reuse=sum(len(x['intervals'])>1 for x in native),
                review_sessions=len(qa),host_sessions=captured)


def run(root):
    root=Path(root).resolve();plan=read(root/'run-plan.json')
    for name,digest in read(root/'source-sha256.json').items():
        if sha(HERE/name)!=digest:raise ValueError('source changed after preregistration: '+name)
    wrapper=setup_bin(root,plan['model'],plan['reasoning'])
    for index,item in enumerate(plan['order'],1):
        output=root/'results'/f'{item["id"]}.json'
        if output.exists():continue
        workspace=root/item['workspace'];logs=root/'logs'/item['id'];logs.mkdir(parents=True,exist_ok=True)
        if (logs/'main.receipt.json').exists():raise ValueError('incomplete recorded run requires explicit recovery; never overwrite')
        begin=time.monotonic();phases=[];qa=[]
        print(f'START {index}/{len(plan["order"])} {item["case"]} {item["condition"]} repeat={item["repeat"]}',flush=True)
        phases.append(execute(workspace,logs,'main',wrapper,COMMON,MAIN_SECONDS))
        mechanical=score(item['case'],workspace,read(root/'initial'/f'{item["id"]}.json'),min(60,TOTAL_SECONDS-(time.monotonic()-begin)))
        write(logs/'first-checks.json',mechanical)
        if item['case']=='sales_import' and phases[0]['completed']:
            qa.append(review(root,item,workspace,mechanical,wrapper,'review',min(REVIEW_SECONDS,TOTAL_SECONDS-(time.monotonic()-begin)-15)))
        issue=mechanical['status']=='FAIL' or any(q.get('verdict')=='STOP_SHIP' for q in qa)
        remaining=TOTAL_SECONDS-(time.monotonic()-begin)
        if issue and remaining>90 and phases[0]['completed']:
            feedback=json.dumps(mechanical,ensure_ascii=False)+'\n'+'\n'.join(q.get('report','') for q in qa)
            (logs/'repair-feedback.txt').write_text(feedback)
            prompt=COMMON+'\nONE REPAIR PHASE: main writer only, no workers. Original implementation ended. Fix confirmed failures below; do not weaken protected tests/source data or money helper. Update STATE with real verification.\n'+feedback
            phases.append(execute(workspace,logs,'repair',wrapper,prompt,min(120,remaining-65)))
            mechanical=score(item['case'],workspace,read(root/'initial'/f'{item["id"]}.json'),min(60,TOTAL_SECONDS-(time.monotonic()-begin)))
            if item['case']=='sales_import' and phases[-1]['completed']:
                remaining=TOTAL_SECONDS-(time.monotonic()-begin)
                if remaining>10:qa.append(review(root,item,workspace,mechanical,wrapper,'review-after-repair',min(60,remaining-5)))
        data=telemetry(root,workspace,phases,qa,wrapper)
        protocol=[]
        if not data['settings_verified']:protocol.append('model/reasoning settings not verified')
        if data['max_parallel']>3 or data['max_depth']>1:protocol.append('worker parallel/depth bound')
        if item['condition']=='B' and data['workers']:protocol.append('B implementation/research delegation forbidden')
        if item['condition']=='C' and not 2<=data['workers']<=3:protocol.append('C requires 2-3 actual native read-only workers')
        if data['completed_worker_reuse']:protocol.append('completed worker reused')
        latest_qa=qa[-1] if qa else None
        qa_ok=item['case']!='sales_import' or latest_qa and latest_qa.get('status')=='validated' and latest_qa.get('verdict') in ('PASS','ADVISORY') and latest_qa.get('reviewed_engine_sha256')==sha(workspace/'engine.py')
        task_ok=all(p['completed'] for p in phases) and mechanical['status']=='PASS' and qa_ok
        result={**item,**data,'schema':'playbook.delegation.round2.run.v1','task_status':'PASS' if task_ok else 'FAIL',
                'protocol_status':'PASS' if not protocol and data['settings_verified'] else 'FAIL',
                'protocol_findings':protocol,'score':mechanical['score'],'wall_seconds':round(time.monotonic()-begin,3),
                'phases':phases,'reviews':qa,'mechanical':mechanical,'cost_usd':None,'human_minutes':None,
                'owner_requests':None,'status':'FAIL' if not task_ok or protocol else 'BLOCKED',
                'measurement_blockers':['USD billing not exposed by host','Active human minutes not measured'],
                'first_attempt_status':'PASS' if read(logs/'first-checks.json')['status']=='PASS' and phases[0]['completed'] else 'FAIL'}
        write(output,result)
        print(f'END {item["case"]} {item["condition"]}: task={result["task_status"]} protocol={result["protocol_status"]} score={result["score"]} wall={result["wall_seconds"]}',flush=True)
    return {'status':'FINISHED','runs':len(plan['order'])}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('prepare');p.add_argument('--root',type=Path,required=True);p.add_argument('--head',required=True);p.add_argument('--model',required=True);p.add_argument('--reasoning',default='high');p.add_argument('--repeats',type=int,default=2)
    p=sub.add_parser('run');p.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.root,args.head,args.model,args.reasoning,args.repeats) if args.cmd=='prepare' else run(args.root),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
