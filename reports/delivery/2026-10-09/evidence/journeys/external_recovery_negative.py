from pathlib import Path
import hashlib,json,subprocess,sys
base=Path(__file__).resolve().parent
app=base/'booking-project/app.py';data=base/'external-http/bookings.json'
before=hashlib.sha256(data.read_bytes()).hexdigest();results=[]
invalid=base/'external-http/corrupt-backup.json';invalid.write_bytes(b'{invalid backup')
for target in (base/'external-http/nonexistent-backup.json',invalid):
    result=subprocess.run([sys.executable,str(app),'restore','--data',str(data),'--input',str(target)],capture_output=True,text=True,timeout=15)
    assert result.returncode==1,result.stdout
    assert hashlib.sha256(data.read_bytes()).hexdigest()==before
    results.append({'input':target.name,'exit_code':result.returncode,'stderr':result.stderr.strip(),'data_unchanged':True,'status':'PASS for refusal, not restoration'})
(base/'external-http/recovery-negative.json').write_text(json.dumps({'checks':results,'status':'PASS','scope':'bounded local synthetic data'},indent=2)+'\n');print(json.dumps(results))
