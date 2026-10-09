import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,tempfile,os,json,hashlib,subprocess,shutil
from unittest.mock import patch
ROOT=Path.cwd();OUT=ROOT/'.playbook-artifacts/delivery-acceptance-20261009/review';SOURCE=ROOT/'.playbook-artifacts/delivery-acceptance-20261009/journeys/corrected-transfer-app'
source=SOURCE/'app.py';sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha=='82d0417f3fab4923e82e768bf5121ba60dfc2f6c4519195544bf7e8bcf291788'
spec=importlib.util.spec_from_file_location('review_corrected_app',source);app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app);results=[]
with tempfile.TemporaryDirectory(prefix='delivery-independent-corrected-fault-')as d:
 data=Path(d)/'bookings.json';store=app.Store(data);real=os.fsync;calls=[0]
 def fail_directory_once(fd):
  calls[0]+=1
  if calls[0]==2:raise OSError('reviewer injected directory fsync AFTER real os.replace')
  return real(fd)
 payload={'request_id':'first','student':'First committed','date':'2026-10-09','slot':'09:00'}
 try:
  with patch.object(app.os,'fsync',side_effect=fail_directory_once):store.create('anna',payload)
  raise AssertionError('Fault did not fail')
 except app.APIError as e:assert e.status==503;message=e.message
 before=json.loads(data.read_text());first=before['bookings'][0];replayed,created=store.create('anna',payload);assert not created and replayed==first
 store.create('anna',{'request_id':'second','student':'Second','date':'2026-10-09','slot':'10:00'});after=json.loads(data.read_text());assert [r['request_id']for r in after['bookings']]==['first','second'];assert store.get('anna',first['id'])==first
 results.append({'case':'post_replace_directory_fsync','status':'PASS','http_status':503,'message':message,'same_id_replay':True,'later_different_request_keeps_both':True})
with tempfile.TemporaryDirectory(prefix='delivery-independent-closed-fault-')as d:
 data=Path(d)/'bookings.json';store=app.Store(data)
 def invalid_disk(path,doc):path.write_text('{invalid');raise OSError('commit outcome uncertain; disk reload invalid')
 try:
  with patch.object(app,'atomic_json',side_effect=invalid_disk):store.create('anna',payload)
  raise AssertionError('Fault did not fail')
 except app.APIError as e:assert e.status==503
 before=data.read_bytes();closed=[]
 for action,fn in [('list',lambda:store.list('anna')),('get',lambda:store.get('anna','missing')),('create',lambda:store.create('anna',payload))]:
  try:fn();raise AssertionError('Store did not fail closed')
  except app.APIError as e:assert e.status==503;closed.append(action)
 assert store.document is None and not store.available and data.read_bytes()==before
 results.append({'case':'invalid_reload','status':'PASS','closed':closed,'no_stale_cache':True,'bytes_preserved_on_subsequent_attempts':True})
for suffix in ['.retired','.lock','.before-restore-review.json']:
 for operation in ['export','backup','retire']:
  with tempfile.TemporaryDirectory(prefix='delivery-independent-reserved-')as d:
   data=Path(d)/'bookings.json';data.write_text('{"version":1,"bookings":[]}');output=Path(str(data)+suffix);before={p.name:p.read_bytes()for p in Path(d).iterdir()}
   argv=[sys.executable,'-B',str(source),operation,'--data',str(data),'--output',str(output)];r=subprocess.run(argv,capture_output=True,text=True,timeout=30);after={p.name:p.read_bytes()for p in Path(d).iterdir()};assert r.returncode==1 and before==after
   results.append({'case':operation+'_reserved_'+suffix,'status':'PASS','argv':argv,'exit_code':r.returncode,'all_file_bytes_and_set_preserved':True})
with tempfile.TemporaryDirectory(prefix='delivery-independent-corrected-copy-')as d:
 target=Path(d)/'copy';shutil.copytree(SOURCE,target);argv=[sys.executable,'-B','-m','unittest','-v','test_app','test_corrections'];r=subprocess.run(argv,cwd=target,capture_output=True,text=True,timeout=180);assert r.returncode==0
 (OUT/'corrected-full.stdout.txt').write_text(r.stdout);(OUT/'corrected-full.stderr.txt').write_text(r.stderr);results.append({'case':'fullsuite_corrected_temporary_copy','status':'PASS','argv':argv,'exit_code':r.returncode,'stdout':'corrected-full.stdout.txt','stderr':'corrected-full.stderr.txt','tail':r.stderr[-600:]})
value={'schema':'playbook.independent-platform-prototype-recheck.v1','status':'PASS','scope':'corrected local synthetic prototype, not production/field acceptance','source':str(SOURCE),'app_sha256':sha,'findings':[{'id':'DELIVERY-P2-03','status':'FIXED'},{'id':'DELIVERY-P2-04','status':'FIXED'},{'id':'DELIVERY-P2-05','status':'FIXED; packaging-recheck.json'}],'results':results,'probes':'Actual temp files/real os.replace with one-shot injected directory fsync error; not physical device failure','limits':['No source editing; temporary copies/data only.','No model CLI/API, account login, human participant or recursive reviewer.']}
(OUT/'prototype-recheck.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','app_sha256':sha,'independent_groups':len(results)},indent=2))
