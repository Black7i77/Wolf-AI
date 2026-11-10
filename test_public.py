import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import server

class PublicDemoTests(unittest.TestCase):
    def setUp(self):
        self.httpd=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.httpd.public_demo=True
        self.httpd.public_model='qwen2.5-coder:3b'
        self.thread=threading.Thread(target=self.httpd.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.httpd.shutdown();self.httpd.server_close();self.thread.join()
    def request(self,path='/',data=None,origin='https://wolf-example.trycloudflare.com',host='wolf-example.trycloudflare.com'):
        c=http.client.HTTPConnection('127.0.0.1',self.httpd.server_port,timeout=5)
        c.request('POST' if data is not None else 'GET',path,json.dumps(data) if data is not None else None,{'Host':host,'Origin':origin,'Content-Type':'application/json'})
        r=c.getresponse();body=r.read();status=r.status;c.close();return status,body
    def payload(self,**extra):return {'model':'qwen2.5-coder:3b','messages':[{'role':'user','content':'Hello'}],**extra}
    def test_cloudflare_hostname_serves_ui(self):self.assertEqual(self.request()[0],200)
    def test_unrelated_hostname_rejected(self):self.assertEqual(self.request(host='unrelated.example')[0],403)
    def test_cross_origin_chat_rejected(self):self.assertEqual(self.request('/api/chat',self.payload(),origin='https://unrelated.example')[0],403)
    def test_public_model_list_is_fixed(self):
        with patch('server.ollama_request',return_value={'models':[{'name':'qwen2.5-coder:3b'},{'name':'private-model:latest'}]}):
            code,body=self.request('/api/status')
        self.assertEqual(code,200);self.assertEqual(json.loads(body)['models'],['qwen2.5-coder:3b'])
    def test_other_models_cannot_be_requested(self):
        self.assertEqual(self.request('/api/chat',self.payload(model='huge-model:latest'))[0],400)
    def test_public_prompt_limit(self):
        self.assertEqual(self.request('/api/chat',self.payload(messages=[{'role':'user','content':'x'*2001}]))[0],400)
    def test_public_replies_work_then_throttle(self):
        with patch('server.ollama_request',return_value={'message':{'content':'Hello'}}):
            statuses=[self.request('/api/chat',self.payload())[0] for _ in range(4)]
        self.assertEqual(statuses,[200,200,200,429])
if __name__=='__main__':unittest.main()
