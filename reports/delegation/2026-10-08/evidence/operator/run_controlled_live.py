"""Local operator: genuine sequential Codex processes, no generated task solutions."""
import datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time

repo = pathlib.Path.cwd()
root = repo / '.playbook-artifacts/controlled-delegation'
source = repo / 'engineering/experiments/controlled-delegation'
plan = json.loads((root/'run-plan.json').read_text())
binary = pathlib.Path(shutil.which('codex')).resolve()
bindir = root/'bin'
bindir.mkdir(exist_ok=True)
(bindir/'python').symlink_to(sys.executable)
wrapper = bindir/'codex'
wrapper.write_text('''#!/usr/bin/python3
import os, sys
args=sys.argv[1:]
if args and args[0]=='exec':
    args[1:1]=['--ignore-user-config','--ignore-rules',
        '-c','web_search="disabled"','-c','features.apps=false',
        '-c','features.plugins=false','-c','features.memory_tool=false',
        '-c','model="gpt-6.1-sol"','-c','model_reasoning_effort="high"',
        '-c','agents.max_threads=4','-c','agents.max_depth=1']
os.execv(BINARY,[BINARY,*args])
'''.replace('BINARY', repr(str(binary))))
wrapper.chmod(0o755)
env = dict(os.environ)
for k in ('CODEX_THREAD_ID','CODEX_INTERNAL_ORIGINATOR_OVERRIDE','CODEX_PARENT_THREAD_ID'):
    env.pop(k, None)
env['PATH'] = str(bindir)+os.pathsep+env['PATH']
base = json.loads((root/'results.json').read_text())
base['environment'].update({'reasoning':'high','permissions':'workspace-write; approval_policy=never; reviewer read-only',
    'operator':'Codex agent; no owner task intervention measured', 'python':sys.version.split()[0],
    'budget':'600 seconds per host session; workers/review included in process lifetime; USD/token ceiling unavailable',
    'native_subagents_enabled':True,'web_search':'disabled','apps':False,'plugins':False,
    'human_measurement':'unavailable; no invented zero or time saving',
    'raw_root':str(root),'launch_options_evidence':'bin/codex'})
(root/'results.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n')

common = '''Read AGENTS.md and TASK.md and execute the assigned task autonomously. This is an authorized real A/B/C experiment. Follow the condition exactly. Work only inside this isolated workspace; do not read sibling workspaces or the parent repository. Do not commit/push, use accounts or network, or install dependencies. Native subagents are available; if you delegate use the native host tools, retain the inherited model and reasoning, max 3 simultaneous workers and depth 1; workers must not spawn workers. Independent reviewers are read-only and never delegate. Source task files and test intent are fixed. Use python (Python 3.10). For research acceptance a local identical evaluator is at .evaluation/evaluate.py: run python .evaluation/evaluate.py check-workspace --scenario {scenario} --workspace . and save the output. Save real command output and concise dispatch/return evidence under .playbook-artifacts/. Fill run-result.json using RUN_RESULT_TEMPLATE.json with observed values only. Do not invent usage, cost, human time, agent count, approvals, fresh-session evidence, or an outcome rubric: unobservable numeric values stay null. Operator captures host logs, wall time and usage after exit. A failed/denied required independent review or unavailable required evidence means BLOCKED, not PASS. No owner decisions are needed for these bounded synthetic fixtures. Do not request routine approvals. Budget is 600 seconds including workers and review; stop with evidence if blocked.'''

for index,item in enumerate(plan['order'],1):
    w = root/item['workspace']
    if (w/'.playbook-artifacts/operator-sessions.json').exists():
        raise RuntimeError(f'Refuse to overwrite {w}')
    # A local repository boundary prevents loading the real repository's AGENTS.md.
    subprocess.run(['git','init','-q','-b','experiment-baseline',str(w)],check=True)
    evdir=w/'.evaluation'; evdir.mkdir()
    for name in ('evaluate.py','experiment_core.py','experiment_checks.py','experiment_report.py','suite.json'):
        shutil.copyfile(source/name,evdir/name)
    logs=w/'.playbook-artifacts'; logs.mkdir(exist_ok=True)
    initial={p.relative_to(w).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in w.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts}
    (logs/'initial-sha256.json').write_text(json.dumps(initial,indent=2)+'\n')
    scenario=item['scenario']
    phases=(1,2) if scenario=='fresh_session' else (0,)
    sessions=[]
    print(f'START {index}/15 {scenario}/{item["condition"]}',flush=True)
    for phase in phases:
        prompt=common.format(scenario=scenario)
        if phase==1:
            prompt+='\nFRESH SESSION PHASE 1 ONLY: inspect and write STATE.json; do not implement, do not start phase 2, do not mark run PASS. End this host session after recording the state.'
        elif phase==2:
            prompt+='\nFRESH SESSION PHASE 2 ONLY: this is a newly started codex exec process, without resume/fork or phase-1 chat. Read STATE.json and workspace files, implement phase 2 and record verification. Prior phase ended; session IDs will be captured by the operator.'
        label=f'phase-{phase}' if phase else 'main'
        (logs/f'{label}-prompt.txt').write_text(prompt+'\n')
        argv=[str(wrapper),'exec','--cd',str(w),'--sandbox','workspace-write','-c','approval_policy="never"',
              '--json','--output-last-message',str(logs/f'{label}-final.txt'),'-']
        started=datetime.datetime.now(datetime.timezone.utc).isoformat(); begin=time.monotonic()
        timed_out=False
        with (logs/f'{label}-events.jsonl').open('w') as out,(logs/f'{label}-stderr.txt').open('w') as err:
            proc=subprocess.Popen(argv,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,start_new_session=True)
            try: proc.communicate(prompt,timeout=600)
            except subprocess.TimeoutExpired:
                import signal
                timed_out=True; os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        events=[]
        for line in (logs/f'{label}-events.jsonl').read_text().splitlines():
            try: events.append(json.loads(line))
            except json.JSONDecodeError: pass
        ids=[e['thread_id'] for e in events if e.get('type')=='thread.started']
        usage=[e.get('usage') for e in events if e.get('type')=='turn.completed']
        rec={'label':label,'started_utc':started,'wall_seconds':round(time.monotonic()-begin,3),
             'returncode':proc.returncode,'timeout':timed_out,'thread_ids':ids,'usage':usage,
             'argv':argv,'completed':any(e.get('type')=='turn.completed' for e in events),
             'events':f'.playbook-artifacts/{label}-events.jsonl'}
        sessions.append(rec)
        (logs/'operator-sessions.json').write_text(json.dumps(sessions,indent=2)+'\n')
        print(f'END {scenario}/{item["condition"]} {label}: exit={proc.returncode} wall={rec["wall_seconds"]} ids={ids}',flush=True)
        if proc.returncode or timed_out: break
    # Operator mechanical observation is independent of the agent's claimed status.
    check=subprocess.run([sys.executable,str(evdir/'evaluate.py'),'check-workspace','--scenario',scenario,'--workspace',str(w)],capture_output=True,text=True)
    (logs/'operator-mechanical.json').write_text(check.stdout or check.stderr)
    print(f'CHECK {scenario}/{item["condition"]}: {check.returncode}',flush=True)
print('ALL HOST RUNS FINISHED',flush=True)
