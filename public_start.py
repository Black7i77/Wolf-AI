#!/usr/bin/env python3
"""Opt-in public demo launcher. Does not publish until run on the host laptop."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import threading
from http.server import ThreadingHTTPServer
import server
from public_guard import DemoLimits

def main():
    parser=argparse.ArgumentParser(description='Share Wolf AI through a temporary Cloudflare Quick Tunnel.')
    parser.add_argument('--port',type=int,default=8780)
    parser.add_argument('--model',default=os.environ.get('WOLF_PUBLIC_MODEL'))
    args=parser.parse_args()
    cloudflared=shutil.which('cloudflared')
    if not cloudflared:parser.exit(1,'cloudflared is not installed. Follow the Cloudflare download link in README.md, then run this again.\n')
    try:models=[m['name'] for m in server.ollama_request('/api/tags').get('models',[])]
    except (OSError,ValueError):parser.exit(1,'Ollama is offline. Run ollama serve in another terminal, then try again.\n')
    model=args.model or next((m for m in ('qwen2.5-coder:3b','qwen2.5-coder:7b','llama3.2:latest') if m in models),next(iter(models),None))
    if model not in models:parser.exit(1,'The selected model is not installed. Check ollama list or choose --model NAME. No model was downloaded.\n')
    try:httpd=ThreadingHTTPServer(('127.0.0.1',args.port),server.Handler)
    except OSError as exc:parser.exit(1,f'Cannot start the demo: {exc}\nTry bash start-public.sh --port 8781\n')
    httpd.daemon_threads=True;httpd.public_demo=True;httpd.public_model=model;httpd.demo_limits=DemoLimits()
    source_file=Path(__file__).resolve().parent/'.wolf-github-url'
    if not os.environ.get('WOLF_GITHUB_URL') and source_file.is_file():os.environ['WOLF_GITHUB_URL']=source_file.read_text().strip()
    worker=threading.Thread(target=httpd.serve_forever,daemon=True);worker.start()
    print(f'Wolf AI public demo uses local model: {model}\nLimits: one reply at a time; 3 messages per visitor / 10 minutes; 20 total / hour.\nShare only the https://...trycloudflare.com link printed below.\nKeep this terminal and laptop on. Press Ctrl+C to stop public access.\n',flush=True)
    process=None
    try:
        process=subprocess.Popen([cloudflared,'tunnel','--url',f'http://127.0.0.1:{httpd.server_port}'])
        process.wait()
    except KeyboardInterrupt:print('\nStopping public demo...',flush=True)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        httpd.shutdown();httpd.server_close();worker.join(timeout=5)
if __name__=='__main__':main()
