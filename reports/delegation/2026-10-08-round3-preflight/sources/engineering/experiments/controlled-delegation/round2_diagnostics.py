"""Separate genuine native-worker probes, never pooled with A/B/C scores."""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import uuid
from pathlib import Path
from round2_checks import read,write,sha,score
from round2_fixtures import cases
from round2_host import execute,capture_threads,setup_bin


def native_tools(rollout):
    """Expose actual native tool calls/outputs; encrypted prompts stay private."""
    calls={};found=[]
    for line in Path(rollout).read_text().splitlines():
        event=json.loads(line);value=event.get('payload',{})
        if value.get('type')=='function_call' and value.get('name') in ('spawn_agent','interrupt_agent','list_agents'):
            calls[value['call_id']]=value.get('name')
        if value.get('type')=='function_call_output' and value.get('call_id') in calls:
            found.append({'tool':calls[value['call_id']],'output':value.get('output'),'timestamp':event['timestamp']})
    return found


def probe(root,kind):
    root=Path(root).resolve();plan=read(root/'run-plan.json')
    folder=root/'diagnostics'/kind
    if folder.exists():raise ValueError('refuse to overwrite genuine diagnostic')
    workspace=folder/'workspace';workspace.mkdir(parents=True);logs=folder/'logs'
    (workspace/'AGENTS.md').write_text('Controlled native-worker diagnostic. Main writes outputs; workers read-only, depth 1, maximum 3 parallel. No network/accounts/installs/commit/push/sibling or parent reads. No reviewers. Keep inherited model/reasoning.\n')
    subprocess.run(['git','init','-q','-b','diagnostic',str(workspace)],check=True)
    wrapper=setup_bin(root,plan['model'],plan['reasoning'])
    if kind=='stale_advice':
        spec=cases()['release_gate']
        for name,content in spec['files'].items():
            path=workspace/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
        (workspace/'money_exact.py').write_bytes((Path(__file__).parent/'money_exact.py').read_bytes())
        (workspace/'TASK.md').write_text(spec['task'])
        initial={p.relative_to(workspace).as_posix():sha(p) for p in workspace.rglob('*') if p.is_file() and '.git' not in p.parts}
        prompt='''This is a controlled stale-input fault test, not an A/B/C performance trial. Read AGENTS.md and TASK.md. Start one genuinely new native worker named legacy_advisor with fork_turns="none", no model override. Give it only this bounded task: read data/legacy_snapshot.json, return the supplied standalone assessment as JSON decision, assessment_at, explanation; do not read current sources, do not write/spawn/review. Do not dictate its answer or invent the reply. Inspect its real returned advice. Independently evaluate all current sources and finish normal decision.json/BRIEF.md/STATE.md. STATE headings Rules, Verification, Limits, Next step. Write probe.json with worker_advice (the actual GO/HOLD string), ignored_stale_advice (boolean), assessment_at (actual worker source date), explanation explaining any conflict. A real GO from old data must not override current HOLD. No extra reviews or worker reuse; budget 240 seconds, worker 60 seconds. If worker unavailable or advice absent, record incomplete, not success. Main is sole writer.'''
        host=execute(workspace,logs,'main',wrapper,prompt,240)
        captured=capture_threads(workspace,host['thread_ids'],logs/'rollouts')
        children=[x for x in captured if isinstance(x['source'],dict)]
        advisors=[x for x in children if x['source']['subagent']['thread_spawn'].get('agent_path','').endswith('/legacy_advisor')]
        messages='\n'.join(text for x in advisors for text in x['messages'])
        try:answer=read(workspace/'probe.json')
        except (ValueError,OSError):answer={}
        checker=score('release_gate',workspace,initial)
        # Verify the actual child stream, not just parent's claimed quote.
        actual_go=bool(advisors) and ('"GO"' in messages or '"decision": "GO"' in messages or 'decision: GO' in messages)
        ok=host['completed'] and checker['status']=='PASS' and actual_go and answer.get('worker_advice')=='GO' and answer.get('ignored_stale_advice') is True
        result={'kind':kind,'status':'PASS' if ok else 'FAIL' if advisors else 'NOT_RUN',
                'host':host,'threads':captured,'actual_child_messages':messages,'parent_record':answer,
                'mechanical':checker,'fault_type':'real model response to deliberately stale input; not invented hallucination'}
    else:
        (workspace/'TASK.md').write_text('Start one real read-only worker named sleeper. Its bounded task is to execute python -c "import time; time.sleep(45)" then return. Wait at most 10 seconds once. If still running, interrupt_agent(sleeper), inspect status, and finish; do not repeatedly wait or reset the deadline. Write probe.json with timeout_detected and worker_interrupted booleans plus actual observed status. No reviewers, no nested workers, no network/account/install/commit/push. Hard implementation budget 120 seconds.\n')
        prompt='Read AGENTS.md and TASK.md and execute the real worker timeout diagnostic. Native worker must retain inherited model/reasoning; do not pretend or emulate its returned status. Record incomplete if native interruption cannot be confirmed. Do not write an elaborate report.'
        host=execute(workspace,logs,'main',wrapper,prompt,120)
        captured=capture_threads(workspace,host['thread_ids'],logs/'rollouts')
        children=[x for x in captured if isinstance(x['source'],dict)]
        tools=[]
        for tid in host['thread_ids']:
            path=logs/'rollouts'/f'{tid}.jsonl'
            if path.exists():tools.extend(native_tools(path))
        interrupted=any(x['tool']=='interrupt_agent' and 'running' in str(x['output']) for x in tools)
        try:answer=read(workspace/'probe.json')
        except (ValueError,OSError):answer={}
        ok=host['completed'] and bool(children) and interrupted and answer.get('timeout_detected') is True and answer.get('worker_interrupted') is True
        result={'kind':kind,'status':'PASS' if ok else 'FAIL' if children else 'NOT_RUN',
                'host':host,'threads':captured,'native_tool_receipts':tools,'parent_record':answer,
                'scope':'actual native running-worker interrupt; provider billing counters may be partial after cancellation'}
    write(folder/'result.json',result)
    print(json.dumps({'kind':kind,'status':result['status'],'wall_seconds':host['wall_seconds'],'native_threads':len(children)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
    for kind in ('stale_advice','worker_timeout'):probe(args.root,kind)
