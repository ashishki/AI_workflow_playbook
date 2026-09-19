import json,queue,subprocess,threading,time
from pathlib import Path
p=subprocess.Popen(['/codex','app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
q=queue.Queue()
def reader():
 for line in p.stdout:
  try:q.put(json.loads(line))
  except ValueError:pass
threading.Thread(target=reader,daemon=True).start()
def call(i,method,params):
 p.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':method,'params':params})+'\n');p.stdin.flush()
 deadline=time.monotonic()+30
 while True:
  msg=q.get(timeout=max(.01,deadline-time.monotonic()))
  if msg.get('id')==i:return msg
try:
 call(1,'initialize',{'clientInfo':{'name':'starter_discovery','version':'0.1'}})
 p.stdin.write('{"jsonrpc":"2.0","method":"initialized","params":{}}\n');p.stdin.flush()
 result=call(2,'skills/list',{'cwds':['/workspace'],'forceReload':True})
 allskills=[s for row in result['result']['data'] for s in row['skills']]
 actual=[s for s in allskills if s['name'].startswith('playbook')]
 assert sorted(s['name'] for s in actual)==['playbook','playbook-frontend'],actual
 assert all(s['enabled'] and s['path'].startswith('/workspace/.agents/skills/') for s in actual),actual
 assert not Path('/workspace/.git').exists()
 print(json.dumps({'passed':True,'git_required':False,'skills':actual},ensure_ascii=False,indent=2))
finally:p.terminate();p.wait(timeout=10)
