"""Maintainer holdout CLI cases; run with non-root Python after implementation."""
import json,hashlib,subprocess,sys,tempfile,os
from pathlib import Path
PROJECT=Path(sys.argv[1]);OUT=Path(sys.argv[2]);OUT.mkdir()
if os.geteuid()==0:raise SystemExit('acceptance must be nonroot')
results=[]
with tempfile.TemporaryDirectory(prefix='receipt-acceptance-') as folder:
    base=Path(folder)
    def fresh(name,exit_code=0,timed_out=False):
        d=base/name;d.mkdir();(d/'stdout.txt').write_bytes(b'actual bounded output\n');(d/'stderr.txt').write_bytes(b'')
        receipt={'schema_version':'playbook.command_receipt.v1','exit_code':exit_code,'environment_summary':{'timed_out':timed_out},'command_argv':[sys.executable,'-c',f"from pathlib import Path;Path({str(base/'MUST_NOT_EXECUTE')!r}).write_text('bad')"],'stdout_artifact_path':'stdout.txt','stderr_artifact_path':'stderr.txt','stdout_sha256':hashlib.sha256((d/'stdout.txt').read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256(b'').hexdigest()}
        p=d/'receipt.json';p.write_text(json.dumps(receipt));return p,receipt
    def check(name,p,status,code=0):
        result=subprocess.run([sys.executable,str(PROJECT/'audit_receipt.py'),*(['--strict-exit'] if name.startswith('strict-') else []),str(p)],text=True,capture_output=True,timeout=10)
        try:obj=json.loads(result.stdout)
        except ValueError:obj={'status':'UNPARSEABLE','stdout':result.stdout,'stderr':result.stderr}
        passed=result.returncode==code and obj.get('status')==status
        results.append({'id':name,'status':'PASS' if passed else 'FAIL','expected':status,'observed':obj,'cli_exit':result.returncode})
    p,r=fresh('pass');check('realvalidpass',p,'PASS')
    p,r=fresh('failed',7);check('genuinefailure',p,'FAIL')
    p,r=fresh('timeout',0,True);check('timeoutnotpass',p,'FAIL')
    p,r=fresh('missing');(p.parent/'stdout.txt').unlink();check('missingnotrun',p,'NOT_RUN')
    p,r=fresh('changed');(p.parent/'stdout.txt').write_bytes(b'tampered');check('changedinvalid',p,'INVALID',2)
    p,r=fresh('escape');r['stdout_artifact_path']='../pass/stdout.txt';p.write_text(json.dumps(r));check('escapedenied',p,'INVALID',2)
    p,r=fresh('absolute');r['stdout_artifact_path']=str(base/'pass/stdout.txt');p.write_text(json.dumps(r));check('absoluteartifactdenied',p,'INVALID',2)
    p,r=fresh('symlink');(p.parent/'stdout.txt').unlink();(p.parent/'stdout.txt').symlink_to(base/'pass/stdout.txt');check('symlinkdenied',p,'INVALID',2)
    p,r=fresh('hardlink');(p.parent/'stdout.txt').unlink();os.link(base/'pass/stdout.txt',p.parent/'stdout.txt');check('hardlinkdenied',p,'INVALID',2)
    p,r=fresh('bool');r['exit_code']=False;p.write_text(json.dumps(r));check('boolnotinteger',p,'INVALID',2)
    p,r=fresh('oversized');(p.parent/'stdout.txt').write_bytes(b'x'*(1024*1024+1));r['stdout_sha256']=hashlib.sha256((p.parent/'stdout.txt').read_bytes()).hexdigest();p.write_text(json.dumps(r));check('sizebound',p,'INVALID',2)
    p,r=fresh('strictpass');check('strict-pass',p,'PASS',0)
    p,r=fresh('strictfail',7);check('strict-fail',p,'FAIL',1)
    p,r=fresh('strictmissing');(p.parent/'stdout.txt').unlink();check('strict-missing',p,'NOT_RUN',3)
    p,r=fresh('strictinvalid');(p.parent/'stdout.txt').write_bytes(b'changed');check('strict-invalid',p,'INVALID',2)
    assert not (base/'MUST_NOT_EXECUTE').exists()
    results.append({'id':'commandargvdataonly','status':'PASS'})
summary={'status':'PASS' if all(x['status']=='PASS' for x in results) else 'FAIL','checks':results,'uid':os.geteuid(),'source_sha256':hashlib.sha256((PROJECT/'audit_receipt.py').read_bytes()).hexdigest()}
(OUT/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
