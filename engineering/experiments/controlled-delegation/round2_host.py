"""Real Codex process adapter with an operator-enforced deadline and receipts."""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from round2_checks import read, write, sha

PARENT_KEYS=('CODEX_THREAD_ID','CODEX_PARENT_THREAD_ID','CODEX_INTERNAL_ORIGINATOR_OVERRIDE')


def environment(bin_dir):
    env=dict(os.environ)
    for key in PARENT_KEYS:env.pop(key,None)
    env['PATH']=str(bin_dir)+os.pathsep+env['PATH']
    env['PYTHONDONTWRITEBYTECODE']='1'
    return env


def setup_bin(root, model, reasoning):
    folder=Path(root)/'bin';folder.mkdir(exist_ok=True)
    python=folder/'python'
    if not python.exists():python.symlink_to(sys.executable)
    cli=shutil.which('codex')
    if not cli:raise RuntimeError('codex CLI unavailable; no simulation fallback')
    wrapper=folder/'codex'
    script='''#!/usr/bin/python3
import os,sys
argv=sys.argv[1:]
if argv and argv[0]=='exec':
    argv[1:1]=COMMON
    if 'read-only' in argv:argv[1:1]=['-c','features.multi_agent=false']
os.execv(BINARY,[BINARY,*argv])
'''
    common=['--ignore-user-config','--ignore-rules','-c','web_search="disabled"',
            '-c','features.apps=false','-c','features.plugins=false','-c','features.memories=false',
            '-c',f'model="{model}"','-c',f'model_reasoning_effort="{reasoning}"',
            '-c','agents.max_threads=4','-c','agents.max_depth=1','-c','approval_policy="never"']
    wrapper.write_text(script.replace('COMMON',repr(common)).replace('BINARY',repr(cli)))
    wrapper.chmod(0o755)
    return wrapper


def kill_group(process):
    # SIGTERM allows Codex to interrupt its workers before escalation.
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait(timeout=5)


def events(path):
    result=[]
    for line in Path(path).read_text().splitlines():
        try:result.append(json.loads(line))
        except json.JSONDecodeError:continue
    return result


def execute(workspace, logs, label, wrapper, prompt, seconds, sandbox='workspace-write'):
    logs=Path(logs);logs.mkdir(parents=True,exist_ok=True)
    if (logs/f'{label}.receipt.json').exists():raise RuntimeError('refuse to overwrite host evidence')
    (logs/f'{label}.prompt.txt').write_text(prompt+'\n')
    argv=[str(wrapper),'exec','--cd',str(Path(workspace).resolve()),'--sandbox',sandbox,
          '--json','--output-last-message',str((logs/f'{label}.final.txt').resolve()),'-']
    start=datetime.datetime.now(datetime.timezone.utc).isoformat();begin=time.monotonic();expired=False
    with (logs/f'{label}.events.jsonl').open('w') as out,(logs/f'{label}.stderr.txt').open('w') as err:
        process=subprocess.Popen(argv,env=environment(wrapper.parent),stdin=subprocess.PIPE,
                                 stdout=out,stderr=err,text=True,start_new_session=True)
        try:process.communicate(prompt,timeout=max(1,seconds))
        except subprocess.TimeoutExpired:expired=True;kill_group(process)
    emitted=events(logs/f'{label}.events.jsonl')
    failed=any(e.get('type') in ('turn.failed','error') for e in emitted)
    result={'label':label,'started_utc':start,'wall_seconds':round(time.monotonic()-begin,3),
            'deadline_seconds':seconds,'timeout':expired,'exit_code':process.returncode,
            'completed':process.returncode==0 and not expired and not failed and any(e.get('type')=='turn.completed' for e in emitted),
            'thread_ids':[e['thread_id'] for e in emitted if e.get('type')=='thread.started'],
            'usage':[e['usage'] for e in emitted if e.get('type')=='turn.completed'],
            'argv':argv,'events_sha256':sha(logs/f'{label}.events.jsonl')}
    write(logs/f'{label}.receipt.json',result)
    return result


def capture_threads(workspace, ids, destination):
    """Read genuine provider rollouts; capture native child counters separately."""
    workspace=Path(workspace).resolve();destination=Path(destination);destination.mkdir(exist_ok=True)
    found={}
    for path in (Path.home()/'.codex/sessions').rglob('*.jsonl'):
        try:
            with path.open() as file:first=json.loads(file.readline())
        except (ValueError,OSError):continue
        meta=first.get('payload',{})
        if meta.get('cwd')!=str(workspace):continue
        emitted=events(path);context=None;usage=None;active=None;intervals=[];messages=[];task_completed=False
        for event in emitted:
            value=event.get('payload',{})
            if event.get('type')=='turn_context':context={k:value.get(k) for k in ('model','effort','sandbox_policy','approval_policy')}
            if event.get('type')=='event_msg' and value.get('type')=='token_count' and value.get('info'):
                usage=value['info'].get('total_token_usage')
            if event.get('type')=='event_msg' and value.get('type')=='task_started' and active is None:active=event['timestamp']
            if event.get('type')=='event_msg' and value.get('type')=='task_started':task_completed=False
            if event.get('type')=='event_msg' and value.get('type') in ('task_complete','turn_aborted'):
                if active:intervals.append([active,event['timestamp']]);active=None
                task_completed=value.get('type')=='task_complete'
            if event.get('type')=='response_item' and value.get('type')=='message' and value.get('role')=='assistant':
                for item in value.get('content',[]):
                    if item.get('type') in ('output_text','text'):messages.append(item.get('text',''))
        if active:intervals.append([active,None])
        found[meta['id']]={'id':meta['id'],'source':meta.get('source'),'context':context,
                           'usage':usage,'intervals':intervals,'messages':messages,'task_completed':task_completed,'original':path}
    def parent(entry):
        source=entry['source']
        return source.get('subagent',{}).get('thread_spawn',{}).get('parent_thread_id') if isinstance(source,dict) else None
    selected=set(ids)
    while True:
        more={key for key,entry in found.items() if parent(entry) in selected}
        if more<=selected:break
        selected.update(more)
    output=[]
    for key in sorted(selected):
        if key not in found:continue
        entry=found[key];path=destination/(key+'.jsonl');shutil.copyfile(entry['original'],path)
        output.append({k:v for k,v in entry.items() if k!='original'}|{'raw_sha256':sha(path),'raw_file':str(path)})
    return output


def worker_durations(run):
    """Observed native child intervals, independent of a model's deadline claims."""
    result = []
    for thread in run.get('host_sessions', []):
        if not isinstance(thread.get('source'), dict):
            continue
        seconds = []
        for start, end in thread.get('intervals', []):
            if end:
                parse = lambda value: datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                seconds.append(round((parse(end) - parse(start)).total_seconds(), 3))
            else:
                seconds.append(None)
        result.append({'thread_id': thread['id'], 'interval_seconds': seconds,
                       'task_completed': thread.get('task_completed'),
                       'over_60_seconds': any(value is not None and value > 60 for value in seconds)})
    return result
