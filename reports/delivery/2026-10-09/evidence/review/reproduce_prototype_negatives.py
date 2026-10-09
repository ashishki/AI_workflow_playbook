import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,tempfile,os,json,hashlib,subprocess,shutil,datetime
from unittest.mock import patch
ROOT=Path.cwd(); P=ROOT/'reports/delivery/2026-10-09'; OUT=ROOT/'.playbook-artifacts/delivery-acceptance-20261009/review'; OUT.mkdir(parents=True,exist_ok=True)
source_paths=[P/'outputs'/n/'app.py'for n in ('initial-app','transfer-app')]
probes=[]
for source in source_paths:
 spec=importlib.util.spec_from_file_location('probe_app_'+source.parent.name.replace('-','_'),source); app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
 with tempfile.TemporaryDirectory(prefix='delivery-prototype-review-fsync-')as d:
  data=Path(d)/'bookings.json';store=app.Store(data);real_fsync=os.fsync;calls=[0]
  def fail_directory_once(fd):
   calls[0]+=1
   if calls[0]==2:raise OSError('injected directory fsync failure AFTER real os.replace')
   return real_fsync(fd)
  observed_error=None
  try:
   with patch.object(app.os,'fsync',side_effect=fail_directory_once):store.create('anna',{'request_id':'first','student':'First committed','date':'2026-10-09','slot':'09:00'})
  except OSError as e:observed_error=str(e)
  disk_before=json.loads(data.read_text());memory_before=store.document.copy()
  store.create('anna',{'request_id':'second','student':'Second','date':'2026-10-09','slot':'10:00'});disk_after=json.loads(data.read_text())
  probes.append({'kind':'directory_fsync_after_replace','source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fault':'one-shot injected directory-fsync OSError; real file creation/replacement/fsync path executed','error':observed_error,'disk_committed_before_second_request':disk_before,'memory_before_second_request':memory_before,'disk_after_successful_other_request':disk_after,'confirmed':'first committed booking lost'})
 with tempfile.TemporaryDirectory(prefix='delivery-prototype-review-retire-')as d:
  data=Path(d)/'bookings.json';data.write_text('{"version":1,"bookings":[]}');export=Path(str(data)+'.retired')
  argv=[sys.executable,'-B',str(source),'retire','--data',str(data),'--output',str(export)];r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
  raw=export.read_text();parse_error=None
  try:json.loads(raw)
  except ValueError as e:parse_error=str(e)
  probes.append({'kind':'retire_export_reserved_metadata_alias','source':str(source.relative_to(ROOT)),'argv':argv,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'export_bytes':raw,'json_parse_error':parse_error,'confirmed':'successful retire destroys its JSON export by overwriting it with marker text'})
for name in ['initial-app','transfer-app']:
 with tempfile.TemporaryDirectory(prefix='delivery-published-copy-review-')as d:
  target=Path(d)/name;shutil.copytree(P/'outputs'/name,target)
  argv=[sys.executable,'-B','-m','unittest','test_app.LifecycleTests.test_existing_files_preserved'];r=subprocess.run(argv,cwd=target,capture_output=True,text=True,timeout=30)
  (OUT/(name+'-published-preservation.stdout.txt')).write_text(r.stdout);(OUT/(name+'-published-preservation.stderr.txt')).write_text(r.stderr)
  probes.append({'kind':'published_copy_preservation','source':str((P/'outputs'/name).relative_to(ROOT)),'argv':argv,'working_directory':'reviewer-owned temporary copy of published output','exit_code':r.returncode,'raw_stdout':name+'-published-preservation.stdout.txt','raw_stderr':name+'-published-preservation.stderr.txt','confirmed':'.agents required by original preservation baseline is absent from published copy'})
value={'schema':'playbook.independent-platform-review.v1','status':'CHANGES_REQUESTED','scope':'Final technical prototype/evidence packaging review; core source7f36b90 remains unaffected','reviewer':'/root/delivery_final_review','adapter':'platform_collaboration_read_only','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths},'reviewed_doc_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [P/'REPORT_RU.md',P/'results.json',P/'evidence-index.json']},'findings':[{'id':'DELIVERY-P2-03','severity':'P2','file':str(source_paths[0].relative_to(ROOT)),'line':159,'title':'Post-replace fsync failure leaves stale Store cache that overwrites a committed booking on next request','also_affects':'transfer-app/app.py','fix':'Reconcile cache from validated persisted state after uncertain write failure or fail closed; do not continue writing from old cache. Preserve old frozen source and make new corrected output.'},{'id':'DELIVERY-P2-04','severity':'P2','file':str(source_paths[0].relative_to(ROOT)),'line':269,'title':'retire export path may equal reserved retirement marker and success destroys JSON export','also_affects':'transfer-app/app.py','fix':'Reject reserved lifecycle output aliases before mutation, preserve data/metadata/any output bytes on refusal.'},{'id':'DELIVERY-P2-05','severity':'P2','file':'reports/delivery/2026-10-09/outputs','title':'Published project snapshots omit .agents required by preserved baselines/instructions; documented full tests fail on copies','fix':'Preserve exact archival prerequisites or explicitly label partial snapshots/reconstruction gaps and their observed FAIL. Do not weaken frozen tests/baselines.'}],'probes':probes,'previous_bounded_positive_checks_still_valid':True,'limits':['Real source/files exercised with a deliberately injected fsync failure; this is not observed physical hardware failure.','Old normal-path HTTP/browser/recovery/export PASS remain genuine; new failures extend fault coverage.','Synthetic local prototype, no production credentials/users/public endpoint.','No source edits, model API, account login, external sends or recursive reviewer.']}
(OUT/'prototype-negative.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');(OUT/'prototype-negative.md').write_text('''# Final prototype review — preserved negative findings\n\nCHANGES REQUESTED for three confirmed P2 issues. Native/Desktop runtime7f36b90 is unaffected.\n\n1. A one-shot injected directory-fsync failure after actual JSON replacement leaves Store memory stale. A different next successful booking erases the first already written booking. Both initial/transfer sources reproduce this on reviewer-owned data.\n2. Successful retire with export path equal to `<data>.retired` overwrites the new JSON export with marker text. Both sources reproduce exit0 with unreadable export.\n3. Published initial/transfer snapshots omit their required .agents directory. Exact preservation checks on temporary copies fail (initial31 missing-file errors; transfer1 file-set failure). Historical original checks are not rewritten or invalidated.\n\nSee prototype-negative.json for source/doc SHA256, actual commands, fault type and outcomes. Preserve frozen outputs and earlier genuine positive observations; correct a new copy and recheck. The new fault check does not claim a real device failure, live external integration, field pilot or release approval.\n''')
print(OUT/'prototype-negative.json')
