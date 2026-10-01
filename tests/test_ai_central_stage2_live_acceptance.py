"""Offline controls for the one-shot live acceptance script: no actual network."""
import unittest
from unittest.mock import patch
import requests
from scripts import ai_central_stage2_live_acceptance as a

class Reply:
    def __init__(self,code,obj=None,text=""):
        self.status_code=code;self.obj=obj or {};self.text=text
    def json(self):return self.obj

class Acceptance(unittest.TestCase):
    def test_auth_failure_cannot_create_or_dispatch_task(self):
        calls=[]
        def get(url,**kw):
            calls.append(("GET",url))
            return Reply(200)
        with patch.object(a,"TOKEN","unit-test-long-dashboard-token-xyz"),patch.object(a.requests,"get",side_effect=get),patch.object(a.requests,"post",side_effect=AssertionError("POST forbidden")):
            with self.assertRaisesRegex(RuntimeError,"UNAUTHENTICATED"):
                a.main()
        self.assertEqual(len(calls),1)
    def test_synthetic_happy_path_and_no_duplicate_dispatch(self):
        calls=[]
        identifier="synthetic-proof-1234567890"
        def get(url,**kw):
            calls.append(("GET",url))
            if url.endswith("/inbox"):return Reply(401)
            if url.endswith("/health"):return Reply(200,{"truth":"WORKER_AND_R2_BINDING_PRESENT"})
            if url==a.BASE:return Reply(200,text="NVIDIA-Team starten")
            if url.endswith("/task"):return Reply(200,{"id":identifier,"status":"PENDING_REVIEW",
                    "truth":"R2_ARCHIVED_REPORT","run_id":"12345",
                    "roles":[{"role":"research","status":"ANSWER"},{"role":"diagnosis","status":"ANSWER"},{"role":"challenge","status":"UNAVAILABLE"}]})
            raise AssertionError(url)
        def post(url,**kw):
            calls.append(("POST",url,kw.get("json")))
            if url.endswith("/inbox"):return Reply(202,{"id":identifier,"created_at":"2026-10-01T10:00:00Z"})
            if url.endswith("/dispatch"):
                self.assertEqual(kw["json"]["mode"],"free-team")
                return Reply(202)
            raise AssertionError(url)
        with patch.object(a,"TOKEN","unit-test-long-dashboard-token-xyz"),patch.object(a.requests,"get",side_effect=get),patch.object(a.requests,"post",side_effect=post),patch.dict(a.os.environ,{"TELEGRAM_BOT_TOKEN":"","TELEGRAM_CHAT_ID":""},clear=True):
            a.main()
        self.assertEqual(sum(x[0]=="POST" and x[1].endswith("/dispatch") for x in calls),1)
    def test_rejected_dispatch_never_retries(self):
        identifier="synthetic-proof-1234567890";calls=[]
        def get(url,**kw):
            if url.endswith("/inbox"):return Reply(401)
            if url.endswith("/health"):return Reply(200,{"truth":"WORKER_AND_R2_BINDING_PRESENT"})
            if url==a.BASE:return Reply(200,text="NVIDIA-Team starten")
            raise AssertionError(url)
        def post(url,**kw):
            calls.append(url)
            if url.endswith("/inbox"):return Reply(202,{"id":identifier,"created_at":"2026-10-01T10:00:00Z"})
            return Reply(502)
        with patch.object(a,"TOKEN","unit-test-long-dashboard-token-xyz"),patch.object(a.requests,"get",side_effect=get),patch.object(a.requests,"post",side_effect=post):
            with self.assertRaisesRegex(RuntimeError,"TEAM_DISPATCH_REJECTED"):
                a.main()
        self.assertEqual(sum(url.endswith("/dispatch") for url in calls),1)
    def test_telegram_network_exception_never_leaks_secret(self):
        with patch.dict(a.os.environ,{"TELEGRAM_BOT_TOKEN":"unit-secret-telegram","TELEGRAM_CHAT_ID":"unit-chat"},clear=True),patch.object(a.requests,"post",side_effect=requests.ConnectionError("secret-bearing URL")):
            a.notify_telegram("safe-synthetic-task",{"challenge":"ANSWER"})

if __name__=="__main__":unittest.main()
