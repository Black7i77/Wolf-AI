"""In-memory allowances for a small public demonstration, not paid hosting."""
import hashlib
import hmac
import ipaddress
import secrets
import threading
import time
from collections import deque

class DemoLimits:
    def __init__(self):
        self.lock=threading.Lock();self.visitors={};self.global_hits=deque();self.secret=secrets.token_bytes(32)
    def admit(self,address):
        try:address=str(ipaddress.ip_address(address))
        except ValueError:address='unknown'
        key=hmac.new(self.secret,address.encode(),hashlib.sha256).digest()
        now=time.monotonic()
        with self.lock:
            while self.global_hits and self.global_hits[0]<now-3600:self.global_hits.popleft()
            for k in list(self.visitors):
                while self.visitors[k] and self.visitors[k][0]<now-600:self.visitors[k].popleft()
                if not self.visitors[k]:del self.visitors[k]
            history=self.visitors.get(key,deque())
            if len(history)>=3:return 'Demo limit: 3 messages per visitor every 10 minutes. Please try again later.'
            if len(self.global_hits)>=20:return 'The public demo has reached its hourly allowance. Please try again later.'
            if key not in self.visitors and len(self.visitors)>=256:return 'The public demo is busy. Please try again later.'
            history.append(now);self.visitors[key]=history;self.global_hits.append(now)
        return None
