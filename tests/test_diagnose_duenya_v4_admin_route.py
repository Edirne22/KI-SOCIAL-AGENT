import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from scripts.diagnose_duenya_v4_admin_route import main, NoRedirect

TOKEN = "synthetic-do-not-log"


class Response:
    def __init__(self, status=200, body=b'{"ready":true}', headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {"content-type":"application/json", "server":"cloudflare"}
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,limit): return self.body[:limit]


class DiagnosticTests(unittest.TestCase):
    def run_script(self, results):
        calls = []
        def request(req, **kwargs):
            calls.append(req)
            result = results[(len(calls)-1) % len(results)]
            if isinstance(result, Exception): raise result
            return result
        output = io.StringIO()
        with patch.dict(os.environ, {"PRIVATE_ASR_INTERNAL_TOKEN":TOKEN}), contextlib.redirect_stdout(output):
            main(request)
        self.assertNotIn(TOKEN,output.getvalue())
        self.assertEqual(len(calls),4)
        self.assertTrue(all(r.get_method()=="GET" and r.data is None for r in calls))
        self.assertEqual([r.full_url for r in calls], ["https://edirne22-private-asr.butupeli.workers.dev"+p for p in ("/health","/admin/container-restart")]*2)
        self.assertIsNone(calls[0].get_header("User-agent"))
        self.assertEqual(calls[2].get_header("User-agent"),"Edirne22-Runtime-Diagnostic/1.0")
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def test_expected_health_and_method_guard(self):
        result=self.run_script([Response(),Response(405,b'{"error":"method"}')])
        self.assertTrue(result[0]["ready"])
        self.assertTrue(result[1]["worker_method_guard"])

    def test_403_does_not_expose_body_or_header_values(self):
        result=self.run_script([Response(403,json.dumps({"error":TOKEN}).encode(),{"content-type":TOKEN,"server":TOKEN})])
        self.assertEqual(result[0]["status"],403)
        self.assertEqual(result[0]["known_error"],"other")
        self.assertEqual(result[0]["type"],"other")

    def test_network_error_has_no_raw_exception(self):
        self.assertEqual(self.run_script([URLError(TOKEN)])[0]["status"],"NETWORK_ERROR")

    def test_missing_token_stops_before_network(self):
        with patch.dict(os.environ,{"PRIVATE_ASR_INTERNAL_TOKEN":""}):
            with self.assertRaisesRegex(SystemExit,"DIAG_BLOCKED_MISSING"):
                main(lambda *a,**k:self.fail("network called"))

    def test_redirects_cannot_forward_credentials(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,"",{},"https://other.example"))

    def test_http_error_is_classified(self):
        result=self.run_script([HTTPError("",403,"",{"content-type":"application/json"},io.BytesIO(b'{"error":"forbidden"}')) for _ in range(4)])
        self.assertEqual(result[0]["known_error"],"forbidden")
