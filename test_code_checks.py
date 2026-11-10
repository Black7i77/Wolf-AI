import unittest
from code_checks import check_python
class CodeChecksTests(unittest.TestCase):
    def test_valid_python(self):
        result=check_python('```python\nclass App:\n    def run(self):\n        print("ok")\n```')
        self.assertTrue(result[0]['valid']);self.assertIn('not executed',result[0]['message'].lower())
    def test_invalid_indentation(self):
        r=check_python('```python\nif True:\nprint("broken")\n```')[0]
        self.assertFalse(r['valid']);self.assertEqual(r['line'],2)
    def test_never_executes_code(self):
        self.assertTrue(check_python('```python\nraise RuntimeError("not executed")\n```')[0]['valid'])
    def test_other_languages_ignored(self):self.assertEqual(check_python('```javascript\nlet x = 1;\n```'),[])
    def test_partial_fence(self):self.assertFalse(check_python('```python\ndef x(')[0]['valid'])
if __name__=='__main__':unittest.main()
