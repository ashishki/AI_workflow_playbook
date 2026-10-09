from pathlib import Path
import json,os,sys,shutil
BASE=Path(__file__).resolve().parent;r=json.loads((BASE/'runtime.json').read_text());relay=json.loads((BASE/'private-codex-relay.json').read_text())
ROOT=Path('/srv/openclaw-you/workspace/AI_workflow_playbook');sys.path.insert(0,str(ROOT/'companion/ai_workflow_harness_lab/src'))
from ai_workflow_harness_lab.receipts import run_command_receipt
from ai_workflow_harness_lab.telemetry import execution_metrics
name,project,prompt=sys.argv[1:4];project=Path(project);output=BASE/name;output.mkdir();state=Path(r['work'])/(name+'-codex-state');state.mkdir(mode=0o700);os.chown(state,998,1000)
sandbox_mode='read-only' if len(sys.argv)>4 and sys.argv[4]=='read-only' else 'workspace-write'
sandbox=['/usr/bin/bwrap','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--die-with-parent','--new-session','--cap-drop','ALL','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--ro-bind','/bin','/bin','--ro-bind','/etc/ssl','/etc/ssl','--ro-bind','/etc/resolv.conf','/etc/resolv.conf','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--tmpfs','/home','--dir','/home/oc_you','--bind',str(project),str(project),'--bind',str(state),'/home/oc_you/.codex','--ro-bind',r['runtime_base']+'/python',r['runtime_base']+'/python','--ro-bind',str(Path(r['worker_python']).parents[1]),str(Path(r['worker_python']).parents[1]),'--chdir',str(project),'--']
options=['-c','model_provider="delivery_relay"','-c','model_providers.delivery_relay.name="Delivery original account relay"','-c','model_providers.delivery_relay.base_url='+json.dumps(relay['base_url']),'-c','model_providers.delivery_relay.env_key="DELIVERY_LOCAL_TOKEN"','-c','model_providers.delivery_relay.wire_api="responses"','-c','model_providers.delivery_relay.requires_openai_auth=false','-c','model_providers.delivery_relay.supports_websockets=false','-c','model_providers.delivery_relay.request_max_retries=0','-c','model_providers.delivery_relay.stream_max_retries=0','-c','model_reasoning_effort="medium"','-c','approval_policy="never"']
argv=['/usr/sbin/runuser','-u','oc_you','--',*sandbox,'/usr/bin/codex',*options,'exec','--ephemeral','--sandbox',sandbox_mode,'--model',relay['model'],'--json','-C',str(project),'-o',str(project/'.codex-last-message.txt'),Path(prompt).read_text()]
env={'PATH':str(Path(r['worker_python']).parent)+':/usr/bin:/bin:/usr/sbin','LANG':'C.UTF-8','DELIVERY_LOCAL_TOKEN':relay['local_ephemeral_grant']}
saved=os.environ.copy();os.environ.clear();os.environ.update(env)
try:execution=run_command_receipt(name,output/'receipt',argv,project,timeout=420,inspect_git=False)
finally:os.environ.clear();os.environ.update(saved)
shutil.copy2(execution.receipt_path.parent/'stdout.txt',output/'codex-events.jsonl')
summary={'uid':998,'model_requested':relay['model'],'effort':'medium','cli':'0.162.0','sandbox':sandbox_mode,'root_auth_copied':False,'original_global_config_changed':False,'exit_code':execution.exit_code,'timed_out':execution.timed_out}
try:
    events=[json.loads(line) for line in (output/'codex-events.jsonl').read_text().splitlines() if line.strip()]
    completed=[e for e in events if e.get('type')=='turn.completed'];failed=[e for e in events if e.get('type') in ('turn.failed','error')]
    valid=execution.exit_code==0 and not execution.timed_out and completed and not failed and (project/'.codex-last-message.txt').is_file()
    summary['status']='PASS execution only' if valid else 'FAIL';summary['telemetry']=execution_metrics(output/'codex-events.jsonl',execution.receipt_path,[])
    if (project/'.codex-last-message.txt').exists():shutil.copy2(project/'.codex-last-message.txt',output/'final.txt')
except (ValueError,TypeError,KeyError) as error:summary.update(status='FAIL',reason=str(error))
(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');shutil.rmtree(state);print(name,summary.get('status'))
