"""No redirects or ambiguous POST retries may weaken the live acceptance guard."""
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from scripts.block8_revision_smoke import dashboard_request, verify_dashboard
class HttpAcceptanceTests(unittest.TestCase):
    def test_redirect_is_returned_without_forwarding_owner_token(self):
        calls=[]
        class Response:
            status_code=302
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def iter_content(self,size):return iter([b'redirect'])
        def request(*args,**kwargs):
            calls.append((args,kwargs))
            return Response()
        with patch.dict('sys.modules',{'requests':SimpleNamespace(request=request)}):
            self.assertEqual(dashboard_request('/api/health','synthetic-owner-token')[0],302)
        self.assertEqual(len(calls),1)
        self.assertFalse(calls[0][1]['allow_redirects'])
        self.assertEqual(calls[0][1]['headers']['User-Agent'],'Edirne22-Synthetic-Acceptance/1.0')
    def test_ambiguous_post_is_not_retried(self):
        calls=[]
        def request(*args,**kwargs):
            calls.append(args)
            raise ConnectionError('response lost')
        with patch.dict('sys.modules',{'requests':SimpleNamespace(request=request)}):
            with self.assertRaises(ConnectionError):
                dashboard_request('/api/upload','synthetic',body=b'synthetic',mime='video/mp4')
        self.assertEqual(len(calls),1)
    def test_edge_denial_does_not_count_as_passed_owner_authentication(self):
        with patch.dict('os.environ',{'AI_DASHBOARD_TOKEN':'synthetic-long-token-for-test'}):
            with patch('scripts.block8_revision_smoke.dashboard_request',return_value=(403,b'edge denial')):
                with self.assertRaisesRegex(RuntimeError,'HTTP_403'):
                    verify_dashboard(SimpleNamespace(job_id='synthetic'),'request',{},None,'old')
if __name__=='__main__':unittest.main()
