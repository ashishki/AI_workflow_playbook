"""OpenCode transport for existing Harness Lab. No Codex trace impersonation."""
import argparse,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path('/srv/openclaw-you/workspace/AI_workflow_playbook')
sys.path.insert(0,str(ROOT/'companion/ai_workflow_harness_lab/src'))
sys.path.insert(0,str(ROOT/'evals/native'))
from ai_workflow_harness_lab.receipts import run_command_receipt
from harness_adapter import prepare


def parse_events(raw):
    events=[json.loads(line) for line in raw.splitlines() if line.strip()]
    if any(not isinstance(e,dict) or not isinstance(e.get('type'),str) for e in events):raise ValueError('invalid_event_shape')
    errors=[e for e in events if e['type']=='error']
    finish=[e['part'] for e in events if e['type']=='step_finish' and isinstance(e.get('part'),dict)]
    if not finish or finish[-1].get('reason')!='stop' or errors:raise ValueError('incomplete_or_failed_model_turn')
    ids={e.get('sessionID') for e in events};ids.discard(None)
    if len(ids)!=1:raise ValueError('session_identity_mismatch')
    text='\n'.join(e['part']['text'] for e in events if e['type']=='text' and isinstance(e.get('part'),dict) and isinstance(e['part'].get('text'),str))
    if not text.strip():raise ValueError('empty_final_text')
    tools=[e['part'] for e in events if e['type']=='tool_use' and isinstance(e.get('part'),dict)]
    counters={'input_tokens':0,'cached_input_tokens':0,'output_tokens':0,'reasoning_output_tokens':0,'tool_call_count':len(tools)}
    cost=0.0
    for step in finish:
        tok=step.get('tokens');cache=tok.get('cache') if isinstance(tok,dict) else None
        if not isinstance(cache,dict):raise ValueError('missing_usage')
        values=[tok.get('input'),tok.get('output'),tok.get('reasoning'),cache.get('read'),cache.get('write')]
        if any(type(x)is not int or x<0 for x in values):raise ValueError('invalid_usage')
        inp,out,reasoning,read,write=values
        counters['input_tokens']+=inp+read+write;counters['cached_input_tokens']+=read
        counters['output_tokens']+=out+reasoning;counters['reasoning_output_tokens']+=reasoning
        c=step.get('cost')
        if not isinstance(c,(int,float)) or isinstance(c,bool) or c<0:raise ValueError('missing_or_invalid_reported_cost')
        cost+=c
    return text,counters,cost,next(iter(ids)),events


def main():
    ap=argparse.ArgumentParser()
    for name in ('workspace','prompt-file','output-dir'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--condition',choices=('baseline','playbook'),required=True);ap.add_argument('--task-id',required=True)
    ap.add_argument('--package',type=Path,default=ROOT/'plugins/playbook-native');ap.add_argument('--settings',type=Path,required=True)
    ap.add_argument('--timeout',type=float,default=240);args=ap.parse_args()
    if os.geteuid()==0:raise ValueError('model_worker_must_be_non_root')
    settings=json.loads(args.settings.read_text())
    summary=prepare(args.workspace,args.prompt_file,args.output_dir,args.condition,args.package if args.condition=='playbook' else None)
    summary.update(adapter='opencode-command.v1',provider='opencode-go',model=settings['model'],cli_version='1.18.34',worker_uid=os.geteuid(),evaluation='execution_validity_not_task_acceptance')
    config=settings['config'];profile=args.output_dir/'private-config';profile.mkdir(mode=0o700)
    env=dict(os.environ)
    for k in list(env):
        if k not in {'PATH','HOME','LANG','LC_ALL','SSL_CERT_FILE','SSL_CERT_DIR'}:env.pop(k,None)
    env.update(XDG_CONFIG_HOME=str(profile),OPENCODE_CONFIG_CONTENT=json.dumps(config),OPENCODE_DISABLE_CLAUDE_CODE='1',OPENCODE_DISABLE_GLOBAL_CLAUDE_MD='1')
    # Parent environment is changed for the existing receipt utility's child.
    saved=os.environ.copy();os.environ.clear();os.environ.update(env)
    prompt=args.prompt_file.read_text()
    common='This is an authorized disposable evaluation. Work only inside the current project. Do not use accounts, networks, install packages, publish, or launch nested reviewer/model processes. A separate controller performs the independent read-only review after this turn through the approved OpenCode alternative; do not fabricate Native/Codex review evidence. Python3/unittest and git are available. Preserve unrelated owner files. Finish the requested work, run meaningful checks, and state actual gaps.\n\n'
    try:
        execution=run_command_receipt(args.task_id,args.output_dir/'receipts/opencode',['opencode','run','--pure','--format','json','--model',settings['model'],'--agent','delivery-worker','--title','Delivery '+args.task_id+' '+args.condition,common+prompt],args.workspace,timeout=args.timeout,inspect_git=False)
    finally:os.environ.clear();os.environ.update(saved)
    trace=args.output_dir/'event_ledger.jsonl';shutil.copy2(execution.receipt_path.parent/'stdout.txt',trace)
    valid=False
    try:
        text,counters,cost,session,events=parse_events(trace.read_text())
        (args.output_dir/'final_message.txt').write_text(text)
        valid=execution.exit_code==0 and not execution.timed_out
        receipt=json.loads(execution.receipt_path.read_text());env_record=receipt['environment_summary']
        summary.update(turn_completed=True,execution_valid=valid,session_id=session,raw_openCode_reported_cost_usd=cost,cost_scope='CLI_model_estimate_not_invoice',usage_semantics='input includes cached/read/write; output includes text+reasoning; reasoning also explicit subset')
        summary['execution_telemetry']={'version':'opencode-execution.v1','primary':counters,'reviews':[],'total':counters,'review_count':0,'missing_review_traces':0,'latency_seconds':(env_record['end_monotonic_ns']-env_record['start_monotonic_ns'])/1e9,'cost':'unknown','scope':'OpenCode main only; separate reviewer cost must be added separately'}
    except (ValueError,KeyError,TypeError) as error:summary.update(execution_valid=False,telemetry_error=str(error))
    summary.update(exit_code=execution.exit_code,timed_out=execution.timed_out)
    (args.output_dir/'adapter_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # The local grant expires with the relay. Do not publish private configs.
    shutil.rmtree(profile)
    return 0 if valid else 1
if __name__=='__main__':raise SystemExit(main())
