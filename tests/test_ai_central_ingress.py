import unittest
from ai_central_ingress import parse,handle,SCHEMA,DISPATCH_URL
class Response:
    def __init__(self,status,data=None):
        self.status_code=status
        self._data=data or {}
    def json(self):return self._data
class Tests(unittest.TestCase):
    def test_parse_only_explicit_prefix(self):
        self.assertEqual(parse("/ki openchatcut")["action"],"openchatcut")
        self.assertEqual(parse("ki status")["action"],"status")
        self.assertIsNone(parse("openchatcut"))
        self.assertIsNone(parse("ki post"))
        self.assertIsNone(parse("ki openchatcut; rm -rf /"))
    def test_help_no_credentials_no_network(self):
        self.assertIn("/ki status",handle(parse("/ki"),token=""))
    def test_dispatch_allowlisted_task_only(self):
        calls=[]
        def send(url,**kw):
            calls.append((url,kw))
            return Response(204)
        reply=handle(parse("/ki openchatcut"),token="fixture",dispatch=send)
        self.assertIn("angefordert",reply)
        self.assertEqual(calls[0][0],DISPATCH_URL)
        self.assertEqual(calls[0][1]["json"],{"ref":"main","inputs":{"task":"openchatcut-stability"}})
        self.assertEqual(calls[0][1]["timeout"],12)
    def test_dispatch_error_never_reports_success(self):
        with self.assertRaises(RuntimeError):
            handle(parse("/ki openchatcut"),token="fixture",dispatch=lambda *a,**kw:Response(403))
    def test_no_unknown_action(self):
        with self.assertRaises(ValueError):
            handle({"schema":SCHEMA,"action":"post"},token="fixture")
    def test_status_returns_only_real_run(self):
        fetch=lambda *a,**kw:Response(200,{"workflow_runs":[{"status":"completed","conclusion":"success","html_url":"https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/123"}]})
        msg=handle(parse("/ki status"),token="fixture",transport=fetch)
        self.assertIn("success",msg)
        self.assertIn("/123",msg)
if __name__=="__main__":unittest.main()
