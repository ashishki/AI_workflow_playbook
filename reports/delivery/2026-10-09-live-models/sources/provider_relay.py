"""Ephemeral credential relay: no provider key enters model worker/profile."""
import hashlib,hmac,json,os,secrets,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError

BASE=Path(__file__).resolve().parent
GO_URL='https://opencode.ai/zen/go/v1/chat/completions'
MODELS={'deepseek-v4.1-flash','glm-5.3','mimo-v2.6-pro'}
MAX_REQUESTS=96
MAX_INPUT_BYTES=262144
MAX_OUTPUT_TOKENS=8192
AUTH=json.loads(Path('/root/.local/share/opencode/auth.json').read_text())['opencode-go']
KEY=AUTH['key']
NONCE=secrets.token_urlsafe(32)
LOCK=threading.Lock();COUNT=0
class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('provider_redirect_denied')
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,status,body):
        data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        global COUNT
        if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+NONCE):return self.reply(403,{'error':{'message':'local_scope_denied'}})
        if self.path not in {'/v1/chat/completions','/chat/completions'}:return self.reply(404,{'error':{'message':'unsupported_route'}})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=MAX_INPUT_BYTES:raise ValueError('input_bound')
            self.connection.settimeout(20)
            raw=self.rfile.read(length);data=json.loads(raw)
            if not isinstance(data,dict) or data.get('model') not in MODELS or not isinstance(data.get('messages'),list):raise ValueError('model_or_messages')
            cap=data.get('max_tokens',data.get('max_completion_tokens'))
            if type(cap) is not int or not 1<=cap<=MAX_OUTPUT_TOKENS:raise ValueError('output_bound')
        except (ValueError,OSError):return self.reply(400,{'error':{'message':'invalid_bounded_request'}})
        with LOCK:
            if COUNT>=MAX_REQUESTS:return self.reply(429,{'error':{'message':'experiment_request_limit'}})
            COUNT+=1;number=COUNT
        started=time.time();session=self.headers.get('x-opencode-session','')
        headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json','User-Agent':'playbook-bounded-relay/1.0'}
        if session and len(session)<128:headers['x-opencode-session']=session
        request=Request(GO_URL,data=raw,headers=headers,method='POST')
        record={'request':number,'model_requested':data['model'],'input_sha256':hashlib.sha256(raw).hexdigest(),'input_bytes':len(raw),'output_cap':cap,'started':started,'broker_uid':os.geteuid(),'broker_role':'credential relay only; model process runs uid998','root_key_forwarded_to_worker':False}
        try:
            with build_opener(NoRedirects()).open(request,timeout=240) as response:
                self.send_response(response.status);self.send_header('Content-Type',response.headers.get('Content-Type','application/json'));self.end_headers()
                captured=bytearray()
                while True:
                    chunk=response.read1(65536)
                    if not chunk:break
                    if len(captured)+len(chunk)>16*1024*1024:raise ValueError('response_bound')
                    captured.extend(chunk);self.wfile.write(chunk);self.wfile.flush()
                record['http_status']=response.status
                if data.get('stream'):
                    items=[]
                    for line in bytes(captured).splitlines():
                        if line.startswith(b'data: ') and line!=b'data: [DONE]':
                            try:items.append(json.loads(line[6:]))
                            except ValueError:pass
                    record['model_observed']=list(dict.fromkeys(x.get('model') for x in items if x.get('model')))
                    record['usage']=[x['usage'] for x in items if isinstance(x.get('usage'),dict)]
                    record['finish_reasons']=[c.get('finish_reason') for x in items for c in x.get('choices',[]) if c.get('finish_reason')]
                    record['terminal_done']=b'data: [DONE]' in captured
                else:
                    obj=json.loads(captured);record['model_observed']=obj.get('model');record['usage']=obj.get('usage');record['finish_reasons']=[c.get('finish_reason') for c in obj.get('choices',[])]
        except HTTPError as error:
            record['http_status']=error.code;self.reply(error.code,{'error':{'message':'provider_request_denied','status':error.code}})
        except (OSError,ValueError) as error:
            record['error_type']=type(error).__name__
            try:self.reply(502,{'error':{'message':'relay_transport_failure'}})
            except OSError:pass
        finally:
            record['end']=time.time()
            with LOCK:
                with (BASE/'provider-request-ledger.jsonl').open('a') as stream:stream.write(json.dumps(record)+'\n')

server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
record={'base_url':f'http://127.0.0.1:{server.server_port}/v1','local_ephemeral_grant':NONCE,'allowed_models':sorted(MODELS),'maximum_requests':MAX_REQUESTS,'actual_go_key_location':'original root profile, not copied','worker_uid':998}
p=BASE/'private-relay-config.json';p.write_text(json.dumps(record));p.chmod(0o600);os.chown(p,998,1000)
print('BOUNDED_RELAY_READY '+str(server.server_port),flush=True)
try:server.serve_forever()
finally:server.server_close()
