import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import server

class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.port = cls.httpd.server_port
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.thread.join()
    def request(self, method, path, data=None, origin=None):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        c.request(method,path,json.dumps(data) if data is not None else None,headers)
        r=c.getresponse(); result=(r.status,r.read()); c.close(); return result
    def test_home_serves_approved_interface(self):
        code, body=self.request('GET','/')
        self.assertEqual(code,200); self.assertIn(b'What will you create today?',body)
    def test_chat_returns_ollama_reply(self):
        with patch('server.ollama_request',create=True,return_value={'message':{'content':'Hello there'}}):
            code,body=self.request('POST','/api/chat',{'model':'llama3.2:latest','messages':[{'role':'user','content':'Hello'}]})
        self.assertEqual(code,200); self.assertEqual(json.loads(body)['reply'],'Hello there')
    def test_cross_origin_chat_is_rejected(self):
        code,_=self.request('POST','/api/chat',{},origin='https://unrelated.example')
        self.assertEqual(code,403)
    def test_invalid_message_role_is_rejected(self):
        code,_=self.request('POST','/api/chat',{'messages':[{'role':'tool','content':'bad'}]})
        self.assertEqual(code,400)
    def test_offline_ollama_gives_useful_error(self):
        with patch('server.ollama_request',create=True,side_effect=OSError('offline')):
            code,body=self.request('POST','/api/chat',{'messages':[{'role':'user','content':'Hi'}]})
        self.assertEqual(code,503); self.assertIn(b'ollama serve',body)
    def test_status_lists_local_models(self):
        with patch('server.ollama_request',create=True,return_value={'models':[{'name':'llama3.2:latest'}]}):
            code,body=self.request('GET','/api/status')
        self.assertEqual(code,200); self.assertEqual(json.loads(body)['models'],['llama3.2:latest'])
    def test_source_is_not_exposed(self):
        code,_=self.request('GET','/../server.py')
        self.assertEqual(code,404)
if __name__=='__main__': unittest.main()
