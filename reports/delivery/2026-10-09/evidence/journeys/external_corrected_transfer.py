from pathlib import Path
import subprocess,json,hashlib,sys,re,urllib.request,urllib.error,shutil
base=Path(__file__).resolve().parent;project=base/'corrected-transfer-app';out=base/'corrected-transfer-http';out.mkdir()
data=out/'bookings.json';shutil.copy2(project/'data/bookings.json',data)
original_sha=hashlib.sha256((project/'data/bookings.json').read_bytes()).hexdigest()
golden=json.loads((base/'external-http/golden-booking.json').read_bytes())
process=None;checks=[]
try:
    process=subprocess.Popen([sys.executable,str(project/'app.py'),'serve','--port','0','--data',str(data)],stdout=subprocess.PIPE,stderr=(out/'server.log').open('w'),text=True)
    url=re.search(r'http://127\.0\.0\.1:\d+',process.stdout.readline()).group()
    def call(method,path='/api/bookings',payload=None,teacher='anna'):
        request=urllib.request.Request(url+path,data=json.dumps(payload).encode() if payload else None,headers={'Content-Type':'application/json','X-Teacher':teacher},method=method)
        try:
            with urllib.request.urlopen(request,timeout=10) as response:return response.status,json.loads(response.read())
        except urllib.error.HTTPError as error:return error.code,json.loads(error.read())
    code,value=call('GET','/api/bookings/'+golden['id']);assert code==200 and value['booking']==golden
    assert call('POST',payload={k:golden[k] for k in ('student','date','slot','request_id')})==(200,{'booking':golden,'replayed':True})
    checks.append('old09:15readandreplayunchanged')
    payload={k:golden[k] for k in ('student','date','slot','request_id')};payload.update(date='2027-03-04',slot='09:45',request_id='new-invalid')
    code,value=call('POST',payload=payload);assert code==400 and ('00' in value['error'] and '30' in value['error']),value
    checks.append('new09:45rejectedwithclearnewrule')
    code,value=call('POST',payload={**payload,'slot':'09:30','request_id':'new-valid'});assert code==201,value
    assert call('GET','/api/bookings/'+golden['id'],'',teacher='boris')[0]==404
    checks.append('new09:30acceptedandoldisolationpreserved')
    process.terminate();process.wait(timeout=10)
    backup=out/'backup.json'
    result=subprocess.run([sys.executable,str(project/'app.py'),'backup','--data',str(data),'--output',str(backup)],capture_output=True,text=True,timeout=10);assert result.returncode==0,result.stderr
    data.write_bytes(b'{corrupt-after-transfer')
    result=subprocess.run([sys.executable,str(project/'app.py'),'restore','--data',str(data),'--input',str(backup)],capture_output=True,text=True,timeout=10);assert result.returncode==0,result.stderr
    assert any(b['id']==golden['id'] and b==golden for b in json.loads(data.read_bytes())['bookings'])
    checks.append('reallegacybackupandrestoreafternewrule')
    assert hashlib.sha256((project/'data/bookings.json').read_bytes()).hexdigest()==original_sha
    checks.append('transferredprojectdatabytesunchangedbyacceptance')
    result={'status':'PASS','checks':checks,'adapter':'freshplatformagentfork_none + primary external HTTP/CLI verification','project_data_sha256':original_sha,'app_sha256':hashlib.sha256((project/'app.py').read_bytes()).hexdigest(),'scope':'syntheticfresh-sessionchange; notrealownerreturn'}
except BaseException as error:
    result={'status':'FAIL','checks':checks,'error':repr(error)}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');raise
finally:
    if process and process.poll() is None:process.terminate();process.wait(timeout=10)
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
