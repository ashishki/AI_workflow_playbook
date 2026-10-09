#!/tmp/playbook-model-worker-wzb191rs/work/venv/bin/python
from pathlib import Path
import json,os,sys
base=Path("/srv/openclaw-you/workspace/AI_workflow_playbook/.playbook-artifacts/delivery-model-workflows-20261009")
r=json.loads((base/'runtime.json').read_text());relay=json.loads((base/'private-codex-relay.json').read_text())
if os.geteuid()==0:raise SystemExit('model_worker_must_be_nonroot')
project=Path.cwd();state=project/'.playbook-artifacts/codex-runtime-state';state.mkdir(parents=True,exist_ok=True)
env=dict(os.environ);env['DELIVERY_LOCAL_TOKEN']=relay['local_ephemeral_grant'];env['PATH']=str(Path(r['worker_python']).parent)+':/usr/bin:/bin:/usr/sbin'
opts=['-c','model_provider="delivery_relay"','-c','model_providers.delivery_relay.name="Original-account ephemeral relay"','-c','model_providers.delivery_relay.base_url='+json.dumps(relay['base_url']),'-c','model_providers.delivery_relay.env_key="DELIVERY_LOCAL_TOKEN"','-c','model_providers.delivery_relay.wire_api="responses"','-c','model_providers.delivery_relay.requires_openai_auth=false','-c','model_providers.delivery_relay.supports_websockets=false','-c','model_providers.delivery_relay.request_max_retries=0','-c','model_providers.delivery_relay.stream_max_retries=0']
if sys.argv[1:]==['--version']:os.execve('/usr/bin/codex',['codex','--version'],env)
box=['/usr/bin/bwrap','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--die-with-parent','--new-session','--cap-drop','ALL','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--ro-bind','/bin','/bin','--ro-bind','/etc/ssl','/etc/ssl','--ro-bind','/etc/resolv.conf','/etc/resolv.conf','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--tmpfs','/home','--dir','/home/oc_you','--bind',str(project),str(project),'--bind',str(state),'/home/oc_you/.codex','--ro-bind',r['runtime_base']+'/python',r['runtime_base']+'/python','--ro-bind',str(Path(r['worker_python']).parents[1]),str(Path(r['worker_python']).parents[1]),'--chdir',str(project),'--','/usr/bin/codex',*( ['exec',*opts,*sys.argv[2:]] if sys.argv[1:2]==['exec'] else [*opts,*sys.argv[1:]] )]
os.execve('/usr/bin/bwrap',box,env)
