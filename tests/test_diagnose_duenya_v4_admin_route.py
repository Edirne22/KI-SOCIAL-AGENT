import contextlib
import io
import os
import runpy
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

SCRIPT = "scripts/diagnose_duenya_v4_admin_route.py"
TOKEN = "synthetic-do-not-log"


class Response:
    status = 200
    headers = {"content-type": "application/json", "server": "cloudflare"}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, *args): raise AssertionError("Body must not be read or logged")


class DiagnosticTests(unittest.TestCase):
    def run_script(self, results, token=TOKEN):
        calls = []
        def request(req, **kwargs):
            calls.append(req)
            result = results[len(calls)-1]
            if isinstance(result, Exception): raise result
            return result
        output = io.StringIO()
        with patch.dict(os.environ, {"PRIVATE_ASR_INTERNAL_TOKEN": token}), patch("urllib.request.urlopen", request), contextlib.redirect_stdout(output):
            runpy.run_path(SCRIPT, run_name="__main__")
        self.assertNotIn(TOKEN, output.getvalue())
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(r.get_method() == "GET" and r.data is None for r in calls))
        self.assertEqual([r.full_url for r in calls], ["https://edirne22-private-asr.butupeli.workers.dev"+p for p in ("/health", "/admin/container-restart")])
        return output.getvalue()

    def test_expected_health_and_method_guard(self):
        result = self.run_script([Response(), HTTPError("",405,"",Response.headers,None)])
        self.assertIn("EXPECTED_HEALTH", result)
        self.assertIn("EXPECTED_WORKER_METHOD_GUARD", result)

    def test_403_is_suspected_not_claimed_as_proven(self):
        result = self.run_script([HTTPError("",403,"",{"content-type":"text/html"},None), Response()])
        self.assertIn("HTTP_403 TYPE_text/html", result)
        self.assertIn("EDGE_OR_DEPLOYMENT_MISMATCH_SUSPECTED", result)

    def test_network_error_has_no_raw_exception(self):
        result = self.run_script([URLError(TOKEN), Response()])
        self.assertIn("NETWORK_ERROR", result)

    def test_missing_token_stops_before_network(self):
        with patch.dict(os.environ, {"PRIVATE_ASR_INTERNAL_TOKEN":""}), patch("urllib.request.urlopen") as request:
            with self.assertRaisesRegex(SystemExit,"DIAG_BLOCKED_MISSING"):
                runpy.run_path(SCRIPT, run_name="__main__")
            request.assert_not_called()
