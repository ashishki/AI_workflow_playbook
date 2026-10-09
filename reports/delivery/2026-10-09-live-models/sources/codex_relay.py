"""Ephemeral Responses relay; original Codex auth remains outside worker."""
import hashlib,hmac,json,os,secrets,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError
BASE=Path(__file__).resolve().parent
UPSTREAM='https://chatgpt.com/backend-api/codex/responses'
NONCE=secrets.token_urlsafe(32);LOCK=threading.Lock();COUNT=max([json.loads(x)["request"] for x in (BASE/"codex-provider-ledger.jsonl").read_text().splitlines()] or [0])
class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('redirect_denied')
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,code,text):
        data=json.dumps({'error':{'message':text}}).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        global COUNT
        if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+NONCE):return self.reply(403,'local_scope_denied')
        if self.path!='/v1/responses':return self.reply(404,'unsupported_route')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=1048576:raise ValueError()
            raw=self.rfile.read(length)
            model='gpt-6.1-sol';encoding=self.headers.get('Content-Encoding')
            if not encoding:
                obj=json.loads(raw)
                if obj.get('model')!=model:raise ValueError()
                obj['store']=False;raw=json.dumps(obj).encode()
        except (ValueError,OSError):return self.reply(400,'invalid_request')
        with LOCK:
            if COUNT>=48:return self.reply(429,'experiment_request_limit')
            COUNT+=1;number=COUNT
        auth=json.loads(Path('/root/.codex/auth.json').read_text())['tokens']
        headers={'Authorization':'Bearer '+auth['access_token'],'ChatGPT-Account-Id':auth['account_id'],'Content-Type':'application/json','Accept':'text/event-stream','Accept-Encoding':'identity'}
        for k in ('User-Agent','OpenAI-Beta','originator','Version','x-codex-session-id','x-codex-conversation-id'):
            if self.headers.get(k):headers[k]=self.headers[k]
        if encoding:headers['Content-Encoding']=encoding
        record={'request':number,'expected_model':model,'input_sha256':hashlib.sha256(raw).hexdigest(),'input_bytes':len(raw),'encoding':encoding,'model_body_verified':not bool(encoding),'start':time.time(),'broker_uid':0,'role':'credential relay only','worker_uid':998,'root_auth_copied':False}
        try:
            with build_opener(NoRedirects()).open(Request(UPSTREAM,data=raw,headers=headers,method='POST'),timeout=300) as response:
                self.send_response(response.status);self.send_header('Content-Type',response.headers.get('Content-Type','text/event-stream'));self.end_headers();capture=bytearray();deadline=time.monotonic()+300
                sock=response.fp.raw._sock
                while True:
                    remaining=deadline-time.monotonic()
                    if remaining<=0:raise TimeoutError()
                    sock.settimeout(remaining);chunk=response.read1(65536)
                    if not chunk:break
                    if len(capture)+len(chunk)>16*1024*1024:raise ValueError('response_bound')
                    capture.extend(chunk);self.wfile.write(chunk);self.wfile.flush()
                record['http_status']=response.status;observed=[]
                for line in bytes(capture).splitlines():
                    if line.startswith(b'data: '):
                        try:item=json.loads(line[6:])
                        except ValueError:continue
                        response_meta=item.get('response',{})
                        if isinstance(response_meta,dict) and response_meta.get('model'):observed.append(response_meta['model'])
                        if isinstance(response_meta,dict) and response_meta.get('usage'):record['usage']=response_meta['usage']
                        if item.get('type')=='response.completed':record['completed_event']=True
                record['model_observed']=list(dict.fromkeys(observed))
        except HTTPError as error:
            record['http_status']=error.code
            # Keep only a redacted bounded diagnosis; never echo an OAuth token.
            detail=error.read(4096).decode(errors='replace').replace(auth['access_token'],'[REDACTED]')
            record['provider_error']=detail[:600]
            self.reply(error.code,'upstream_denied_'+str(error.code))
        except (OSError,ValueError) as error:
            record['error_type']=type(error).__name__
            try:self.reply(502,'transport_failure')
            except OSError:pass
        finally:
            record['end']=time.time()
            with LOCK:
                with (BASE/'codex-provider-ledger.jsonl').open('a') as stream:stream.write(json.dumps(record)+'\n')
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
p=BASE/'private-codex-relay.json';p.write_text(json.dumps({'base_url':f'http://127.0.0.1:{server.server_port}/v1','local_ephemeral_grant':NONCE,'model':'gpt-6.1-sol','effort':'xhigh','upstream':UPSTREAM,'request_cap':48}));p.chmod(0o600);os.chown(p,998,1000)
print('CODEX_RELAY_READY '+str(server.server_port),flush=True)
try:server.serve_forever()
finally:server.server_close()
