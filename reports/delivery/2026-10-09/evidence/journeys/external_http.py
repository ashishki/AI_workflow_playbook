from pathlib import Path
import concurrent.futures, hashlib, json, re, subprocess, sys, tempfile, urllib.request, urllib.error, shutil, time
BASE=Path(__file__).resolve().parent
PROJECT=BASE/'booking-project'
OUT=BASE/'external-http'
OUT.mkdir(exist_ok=True)
DATA=OUT/'bookings.json'
if DATA.exists(): raise RuntimeError('Refuse reuse of acceptance state')
checks=[]
process=None

def start():
    global process, url
    process=subprocess.Popen([sys.executable,str(PROJECT/'app.py'),'serve','--port','0','--data',str(DATA)],stdout=subprocess.PIPE,stderr=(OUT/'server.log').open('ab'),text=True)
    line=process.stdout.readline()
    found=re.search(r'http://127\.0\.0\.1:\d+',line)
    assert found, line
    url=found.group()
    return url

def stop():
    global process
    if process and process.poll() is None:
        process.terminate();process.wait(timeout=10)

def call(method,path='/api/bookings', teacher='anna', payload=None, raw=None):
    body=raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
    headers={'Content-Type':'application/json'}
    if teacher is not None: headers['X-Teacher']=teacher
    request=urllib.request.Request(url+path,data=body,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=15) as response: return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error: return error.code,json.loads(error.read())

def record(name):
    checks.append({'id':name,'status':'PASS'}); print('PASS',name,flush=True)

try:
    start()
    for t in (None,'eve'):
        assert call('GET',teacher=t)[0]==403
    record('missing_and_unknown_identity_denied')
    payload={'student':'Synthetic Anna private','date':'2027-03-01','slot':'09:15','request_id':'golden-anna','teacher':'boris'}
    code,data=call('POST',payload=payload);assert code==201,data
    golden=data['booking']; assert golden['teacher']=='anna'
    assert call('POST',payload=payload)==(200,{'booking':golden,'replayed':True})
    record('identity_from_header_and_idempotent_retry')
    assert call('GET','/api/bookings/'+golden['id'],'boris')[0]==404
    assert 'Synthetic Anna private' not in json.dumps(call('GET',teacher='boris')[1])
    code,b=call('POST',teacher='boris',payload={**payload,'student':'Synthetic Boris private','request_id':'golden-boris'});assert code==201,b
    assert b['booking']['teacher']=='boris'
    record('teacher_list_and_id_isolation')
    assert call('POST',payload={**payload,'request_id':'conflict'})[0]==409
    record('occupied_slot_conflict')
    for bad in ({'date':'2027-02-29'},{'date':'2027-3-01'},{'slot':'24:00'},{'slot':'09:60'},{'student':''},{'request_id':''}):
        assert call('POST',payload={**payload,**bad})[0]==400,bad
    assert call('POST',raw=b'{bad json')[0]==400
    record('invalid_calendar_time_empty_fields_and_json')
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        responses=list(pool.map(lambda n:call('POST',payload={**payload,'slot':'10:00','request_id':f'race-{n}'}),range(8)))
    assert sorted(code for code,_ in responses)==[201]+[409]*7,responses
    record('eight_way_concurrent_conflict_has_one_winner')
    before=call('GET')[1]
    stop();start()
    assert call('GET')[1]==before
    assert call('POST',payload=payload)==(200,{'booking':golden,'replayed':True})
    record('restart_preserves_data_and_retry_identity')
    stop()
    backup=OUT/'backup.json';export=OUT/'export.json'
    def cli(action,*args,expected=0):
        result=subprocess.run([sys.executable,str(PROJECT/'app.py'),action,'--data',str(DATA),*map(str,args)],capture_output=True,text=True,timeout=15)
        print(json.dumps({'action':action,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr},ensure_ascii=False),flush=True)
        assert result.returncode==expected,result.stderr
    cli('backup','--output',backup)
    expected=DATA.read_bytes();DATA.write_bytes(b'{broken')
    cli('restore','--input',backup)
    assert json.loads(DATA.read_bytes())==json.loads(expected)
    assert any(p.read_bytes()==b'{broken' for p in OUT.glob('bookings.json.before-restore-*.json'))
    start();assert call('GET')[1]==before;stop()
    record('real_backup_corrupt_copy_restore_and_preserve_bad_bytes')
    cli('retire','--output',export)
    assert json.loads(export.read_bytes())==json.loads(DATA.read_bytes())
    cli('serve','--port','0',expected=1)
    cli('resume')
    record('readable_export_and_local_retired_off_state')
    plan=json.loads((BASE/'plan.json').read_text())
    for name,sha in plan['files'].items(): assert hashlib.sha256((PROJECT/name).read_bytes()).hexdigest()==sha,name
    record('original_task_instructions_owner_note_preserved')
    (OUT/'golden-booking.json').write_text(json.dumps(golden,indent=2)+'\n')
    result={'status':'PASS','checks':checks,'scope':'technical synthetic local HTTP; not real users/login/external API','data':str(DATA),'created_at':time.time(),'app_sha256':hashlib.sha256((PROJECT/'app.py').read_bytes()).hexdigest()}
except BaseException as error:
    result={'status':'FAIL','checks':checks,'error':repr(error),'scope':'technical synthetic local HTTP'}
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');raise
finally:
    stop()
(OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
