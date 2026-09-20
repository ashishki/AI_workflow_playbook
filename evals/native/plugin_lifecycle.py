#!/usr/bin/env python3
"""Offline native-plugin lifecycle probe, inside the documented disposable container.

Expected mounts: /codex binary, /input plugin, /creator official helper scripts,
/out writable evidence. Never run this directly against a user's home directory.
"""
import hashlib,json,subprocess,shutil,threading,queue,time
from pathlib import Path
if not (Path('/.dockerenv').is_file() and
        Path('/run/playbook-eval-container').is_file() and
        Path.home() == Path('/root')):
 raise SystemExit('Refusing to run outside the documented disposable evaluation container')
if (Path.home()/'.agents/plugins').exists() or (Path.home()/'plugins').exists():
 raise SystemExit('Refusing to use an existing plugin installation; start a fresh container')
out=Path('/out/lifecycle');out.mkdir()
records=[]
def run(label,args,ok=True):
 r=subprocess.run(args,text=True,capture_output=True,timeout=60)
 (out/(label+'.stdout')).write_text(r.stdout);(out/(label+'.stderr')).write_text(r.stderr)
 records.append({'step':label,'argv':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 if ok and r.returncode:raise RuntimeError(label+': '+r.stderr)
 return r

def skills(label):
 stderr=(out/(label+'.stderr')).open('w')
 p=subprocess.Popen(['/codex','app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True)
 q=queue.Queue()
 def read():
  for line in p.stdout:
   try:q.put(json.loads(line))
   except ValueError:pass
 threading.Thread(target=read,daemon=True).start()
 def call(i,method,params):
  p.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':method,'params':params})+'\n');p.stdin.flush()
  deadline=time.monotonic()+40
  while time.monotonic()<deadline:
   msg=q.get(timeout=max(.1,deadline-time.monotonic()))
   if msg.get('id')==i:return msg
  raise TimeoutError(method)
 try:
  init=call(1,'initialize',{'clientInfo':{'name':'playbook_trial','version':'0.1'}})
  p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'initialized','params':{}})+'\n');p.stdin.flush()
  data=call(2,'skills/list',{'cwds':['/workspace'],'forceReload':True})
  (out/(label+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  assert 'error' not in data,data
  allskills=[s for row in data['result']['data'] for s in row['skills']]
  native=[{'name':s['name'],'path':s.get('path'),'enabled':s.get('enabled')} for s in allskills if s['name'].startswith('playbook')]
  records.append({'step':label,'native_skills':native});return native
 finally:p.terminate();p.wait(timeout=10);stderr.close()

def hashes(path):return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}
try:
 workspace=Path('/workspace');(workspace/'AGENTS.md').write_text('My project instructions. Preserve my work.\n');(workspace/'user.txt').write_text('Uncommitted user work.\n');before=hashes(workspace)
 run('scaffold',['python3','/creator/create_basic_plugin.py','playbook-native','--with-skills','--with-marketplace'])
 source=Path.home()/'plugins/playbook-native';shutil.copytree('/input',source,dirs_exist_ok=True)
 run('validate-marketplace',['python3','/creator/read_marketplace_name.py'])
 run('install',['/codex','plugin','add','playbook-native@personal','--json'])
 initial=skills('fresh-session-after-install');assert sorted(s['name'] for s in initial)==['playbook-native:playbook','playbook-native:playbook-frontend'],initial
 assert all(s['enabled'] for s in initial),'installed skills are disabled'
 cache=Path(initial[0]['path']).parents[2];snapshot=hashes(cache)
 run('reinstall',['/codex','plugin','add','playbook-native@personal','--json'])
 repeated=skills('fresh-session-after-reinstall');assert len(repeated)==2
 assert hashes(cache)==snapshot,'reinstall changed installed contents'
 sentinel='\n<!-- lifecycle update probe -->\n';f=source/'skills/playbook/SKILL.md';f.write_text(f.read_text()+sentinel)
 run('cachebuster',['python3','/creator/update_plugin_cachebuster.py',str(source)])
 updated_version=json.loads((source/'.codex-plugin/plugin.json').read_text())['version']
 run('update',['/codex','plugin','add','playbook-native@personal','--json'])
 updated=skills('fresh-session-after-update');entry=next(s for s in updated if s['name']=='playbook-native:playbook');assert sentinel in Path(entry['path']).read_text()
 run('remove',['/codex','plugin','remove','playbook-native@personal','--json'])
 assert skills('fresh-session-after-remove')==[]
 assert hashes(workspace)==before,'plugin lifecycle changed project files'
 result={'passed':True,'project_preserved':True,'updated_version':updated_version,'steps':records}
except Exception as e:
 result={'passed':False,'error':repr(e),'steps':records}
finally:
 (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='steps'},ensure_ascii=False),flush=True)
raise SystemExit(0 if result['passed'] else 1)
