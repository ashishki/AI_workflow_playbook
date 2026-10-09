from pathlib import Path
import json,os,subprocess,sys,hashlib
base=Path(__file__).resolve().parent;r=json.loads((base/'runtime.json').read_text());root=Path('/srv/openclaw-you/workspace/AI_workflow_playbook');work=Path(r['work']);stage=sys.argv[1]
command=f'"{r["worker_python"]}" "{base / "opencode_adapter.py"}" --workspace "{{workspace}}" --prompt-file "{{prompt_file}}" --output-dir "{{output_dir}}" --condition {{condition}} --task-id {{task_id}} --settings "{work / "private-settings.json"}" --package "{root / "plugins/playbook-native"}" --timeout 240'
env={'PATH':(str(work/'fake-bin')+':' if stage=='mechanism' else '')+str(Path(r['worker_python']).parent)+':/usr/bin:/bin:/usr/sbin','LANG':'C.UTF-8','PYTHONPATH':str(root/'companion/ai_workflow_harness_lab/src')}
results=[]
for condition in ('baseline','playbook'):
    output=work/(stage+'-'+condition)
    argv=['/usr/sbin/runuser','-u','oc_you','--',r['worker_python'],'-m','ai_workflow_harness_lab.cli','run','--suite',str(root/'evals/native/harness'),'--task-id','backend','--task-id','plan','--adapter','command','--command-template',command,'--adapter-timeout','260','--condition',condition,'--trials','1','--output',str(output),'--fail-on-invalid-run']
    if stage=='real':argv+=['--empirical-comparison','--provider','opencode-go','--model-id','deepseek-v4.1-flash','--cli-version','1.18.34','--reasoning-profile','provider-default','--permission-policy','workspace-tools-no-external-deny','--delivery-profile','native-repo-skills-opencode-v1']
    with (base/(stage+'-'+condition+'.stdout.txt')).open('w') as out,(base/(stage+'-'+condition+'.stderr.txt')).open('w') as err:
        result=subprocess.run(argv,cwd=root,env=env,stdout=out,stderr=err,timeout=600)
    results.append({'condition':condition,'exit_code':result.returncode,'output':str(output),'argv':argv})
    print(stage,condition,'actualexit',result.returncode,flush=True)
    if result.returncode!=0:break
if len(results)==2:
    argv=['/usr/sbin/runuser','-u','oc_you','--',r['worker_python'],'-m','ai_workflow_harness_lab.cli','compare','--baseline',str(work/(stage+'-baseline')),'--candidate',str(work/(stage+'-playbook')),'--output',str(work/(stage+'-comparison')),'--min-trials-per-task','1','--fail-on-invalid-run','--fail-on-hard-gate']
    if stage=='real':argv+=['--require-empirical']
    with (base/(stage+'-comparison.stdout.txt')).open('w') as out,(base/(stage+'-comparison.stderr.txt')).open('w') as err:
        result=subprocess.run(argv,cwd=root,env=env,stdout=out,stderr=err,timeout=60)
    results.append({'comparison_exit':result.returncode,'argv':argv})
    print(stage,'comparison actualexit',result.returncode,flush=True)
(base/(stage+'-dispatch.json')).write_text(json.dumps({'stage':stage,'uid':998,'command_template':command,'results':results},indent=2)+'\n')
