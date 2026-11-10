import unittest
from unittest.mock import patch
from public_guard import DemoLimits
class DemoLimitTests(unittest.TestCase):
    def test_hourly_cap_across_visitors(self):
        limits=DemoLimits()
        for index in range(20):self.assertIsNone(limits.admit('192.0.2.'+str(index+1)))
        self.assertIn('hourly',limits.admit('192.0.2.25'))
    def test_visitor_allowance_recovers(self):
        limits=DemoLimits()
        with patch('public_guard.time.monotonic',return_value=100):
            for _ in range(3):self.assertIsNone(limits.admit('192.0.2.1'))
            self.assertIsNotNone(limits.admit('192.0.2.1'))
        with patch('public_guard.time.monotonic',return_value=701):self.assertIsNone(limits.admit('192.0.2.1'))
if __name__=='__main__':unittest.main()
