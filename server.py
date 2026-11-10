#!/usr/bin/env python3
"""Wolf AI local server. Python standard library only; bound to loopback."""
import argparse
from code_checks import check_python
import json
import mimetypes
import os
import re
from public_guard import DemoLimits
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB = Path(__file__).resolve().parent / 'web'
DEFAULT_MODEL = os.environ.get('WOLF_MODEL', 'llama3.2:latest')
OLLAMA = 'http://127.0.0.1:11434'
SYSTEM = 'You are Wolf AI, a helpful local assistant. Answer clearly and honestly. Do not claim to have executed actions or accessed files unless the conversation provides their results.'
CODE_SYSTEM = SYSTEM + " In coding mode, focus on correct, complete, runnable programs. Use fenced code blocks with a language label. Preserve Python indentation. State the filename, required dependencies and exact run command. Avoid invented APIs. Prefer the user's specified language, framework and platform. Explain assumptions briefly. Never claim code was run or tested. If unsure, state the uncertainty. Do not omit necessary imports or entry points."
GATE = threading.BoundedSemaphore(1)
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def ollama_request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(OLLAMA + path, data=data, headers={'Content-Type':'application/json'})
    with OPENER.open(request, timeout=180 if payload is not None else 5) as response:
        return json.load(response)

class Handler(BaseHTTPRequestHandler):
    @property
    def public_demo(self):return bool(getattr(self.server,'public_demo',False))
    @property
    def public_model(self):return getattr(self.server,'public_model','qwen2.5-coder:3b')
    def public_host(self):
        host=self.headers.get('Host','').lower()
        custom=os.environ.get('WOLF_PUBLIC_HOST','').lower()
        return bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com',host)) or bool(custom and host==custom)

    def log_message(self, *args):
        pass  # Never log prompts or message content.
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cache-Control','no-store')
        super().end_headers()
    def json_response(self, status, obj):
        body=json.dumps(obj).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def allowed_host(self):
        hosts={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        return self.headers.get('Host') in hosts or (self.public_demo and self.public_host())
    def do_GET(self):
        if not self.allowed_host(): return self.json_response(403,{'error':'Local access only.'})
        path=urllib.parse.urlsplit(self.path).path
        if path=='/api/site':
            github=os.environ.get('WOLF_GITHUB_URL','')
            if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+/?',github):github=''
            return self.json_response(200,{'github':github,'public_demo':self.public_demo})
        if path=='/api/status':
            try:
                result=ollama_request('/api/tags')
                models=[m['name'] for m in result.get('models',[]) if isinstance(m,dict) and isinstance(m.get('name'),str)]
                if self.public_demo:
                    available=self.public_model in models
                    return self.json_response(200,{'connected':available,'models':[self.public_model] if available else [],'model':self.public_model,'coding_model':self.public_model,'public_demo':True})
                model=DEFAULT_MODEL if DEFAULT_MODEL in models else next(iter(models),DEFAULT_MODEL)
                coding_model=next((m for name in ('qwen2.5-coder:3b','qwen2.5-coder:7b') for m in models if m==name),next((m for m in models if 'coder' in m.lower()),model))
                return self.json_response(200,{'connected':True,'models':models,'model':model,'coding_model':coding_model})
            except (OSError,ValueError):
                return self.json_response(200,{'connected':False,'models':[],'model':self.public_model if self.public_demo else DEFAULT_MODEL,'public_demo':self.public_demo,'error':'Start Ollama with: ollama serve'})
        allowed={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/format.js':'format.js','/style.css':'style.css','/assets/wolf-hero.png':'assets/wolf-hero.png','/assets/favicon.svg':'assets/favicon.svg'}
        if path not in allowed: return self.json_response(404,{'error':'Not found.'})
        file=WEB / allowed[path]
        try: body=file.read_bytes()
        except OSError: return self.json_response(404,{'error':'Website file missing. Extract the entire ZIP first.'})
        self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        origin=self.headers.get('Origin')
        allowed_origins={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if self.public_demo and self.public_host():allowed_origins.add('https://'+self.headers.get('Host','').lower())
        if not self.allowed_host() or (origin is not None and origin not in allowed_origins):
            return self.json_response(403,{'error':'Local access only.'})
        endpoints=('/api/chat',)
        if self.path not in endpoints:return self.json_response(404,{'error':'Not found.'})
        if self.headers.get_content_type()!='application/json': return self.json_response(415,{'error':'JSON required.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>(32768 if self.public_demo else 262144): raise ValueError('Request too large or empty.')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict):raise ValueError('Invalid request.')
        except (ValueError,UnicodeError) as exc:return self.json_response(400,{'error':str(exc)})
        try:
            messages=data.get('messages')
            model=data.get('model',DEFAULT_MODEL)
            if not isinstance(model,str) or not model or len(model)>200: raise ValueError('Invalid model name.')
            if not isinstance(messages,list) or not 1<=len(messages)<=64: raise ValueError('Send between 1 and 64 messages.')
            for message in messages:
                if not isinstance(message,dict) or message.get('role') not in ('user','assistant') or not isinstance(message.get('content'),str) or len(message['content'])>12000:
                    raise ValueError('Invalid chat message.')
            if messages[-1]['role']!='user' or not messages[-1]['content'].strip(): raise ValueError('A user message is required.')
        except (ValueError,UnicodeError) as exc:
            return self.json_response(400,{'error':str(exc)})
        if self.public_demo:
            if model!=self.public_model:return self.json_response(400,{'error':'This demo only offers its selected model.'})
            if len(messages)>10 or sum(len(m['content']) for m in messages)>12000 or len(messages[-1]['content'])>2000:
                return self.json_response(400,{'error':'Demo limit: 2,000 characters per message and 10 context messages.'})
        if not GATE.acquire(blocking=False): return self.json_response(429,{'error':'Wolf AI is already thinking. Wait for the current reply.'})
        try:
            if self.public_demo:
                if not hasattr(self.server,'demo_limits'):self.server.demo_limits=DemoLimits()
                # Only a loopback cloudflared connection supplies this forwarding header.
                error=self.server.demo_limits.admit(self.headers.get('CF-Connecting-IP',self.client_address[0]))
                if error:return self.json_response(429,{'error':error})
            coding=data.get('mode')=='code'
            result=ollama_request('/api/chat',{'model':model,'messages':[{'role':'system','content':CODE_SYSTEM if coding else SYSTEM}]+messages,'stream':False,'options':{'num_predict':512 if self.public_demo else (3072 if coding else 1024)}})
            reply=result.get('message',{}).get('content')
            if not isinstance(reply,str) or not reply.strip(): return self.json_response(502,{'error':'The model returned no text. Try another model.'})
            return self.json_response(200,{'reply':reply,'model':model,'checks':check_python(reply),'truncated':result.get('done_reason')=='length'})
        except urllib.error.HTTPError as exc:
            if exc.code==404: return self.json_response(503,{'error':f'Model {model} is not installed. Choose an installed model from the list.'})
            return self.json_response(503,{'error':'Ollama could not generate a reply. Check the Ollama terminal or choose a smaller model.'})
        except (OSError,ValueError):
            return self.json_response(503,{'error':'Ollama is unavailable or timed out. Run ollama serve in another terminal, then try again.'})
        finally: GATE.release()

def main():
    parser=argparse.ArgumentParser(description='Run Wolf AI locally with Ollama.')
    parser.add_argument('--port',type=int,default=8767)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    try: httpd=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as exc: parser.exit(1,f'Cannot start Wolf AI: {exc}\nTry: python3 server.py --port 8768\n')
    httpd.daemon_threads=True
    print(f'Wolf AI: http://127.0.0.1:{httpd.server_port}\nLocal Ollama: {OLLAMA}\nPress Ctrl+C to stop.',flush=True)
    if not args.no_browser: threading.Timer(.5,lambda:webbrowser.open(f'http://127.0.0.1:{httpd.server_port}')).start()
    try: httpd.serve_forever()
    except KeyboardInterrupt: print('\nWolf AI stopped.')
    finally: httpd.server_close()
if __name__=='__main__': main()
