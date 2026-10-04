import io
import json
import os
import unittest
from datetime import datetime, timezone
from scripts.ai_central_shared_inbox import parse_command, submit, recent, handle, start_reviewed, result_summary

class NotFound(Exception):
    response={"Error":{"Code":"404"}}
class Forbidden(Exception):
    response={"Error":{"Code":"403"}}
class Conflict(Exception):
    response={"Error":{"Code":"PreconditionFailed"}}
class FakeR2:
    def __init__(self):
        self.objects={}
        self.etags={}
        self.serial=0
        self.head_error=None
    def head_object(self,**kw):
        if self.head_error:raise self.head_error
        if kw["Key"] not in self.objects:raise NotFound()
        return {"ContentLength":len(self.objects[kw["Key"]])}
    def put_object(self,**kw):
        if "IfMatch" in kw and kw["IfMatch"]!=self.etags.get(kw["Key"]):raise Conflict()
        self.objects[kw["Key"]]=kw["Body"]
        self.serial+=1
        self.etags[kw["Key"]]=f"etag-{self.serial}"
        return {"ETag":self.etags[kw["Key"]]}
    def list_objects_v2(self,**kw):
        return {"Contents":[{"Key":k} for k in self.objects if k.startswith(kw["Prefix"])]}
    def get_object(self,**kw):
        if kw["Key"] not in self.objects:raise NotFound()
        return {"Body":io.BytesIO(self.objects[kw["Key"]]),"ETag":self.etags[kw["Key"]]}
class Inbox(unittest.TestCase):
    def setUp(self):self.r2=FakeR2()
    def test_commands_do_not_intercept_existing_router(self):
        self.assertIsNone(parse_command("T1,T3"))
        self.assertEqual(parse_command("/zentrale status"),("status",None))
        self.assertEqual(parse_command("/zentrale SOFORTAUFTRAG – PRIVATE VIDEOPRODUKTION\nDünya wird 12 Jahre alt. Geburtstag im Trampolinpark."),("auftrag","SOFORTAUFTRAG – PRIVATE VIDEOPRODUKTION\nDünya wird 12 Jahre alt. Geburtstag im Trampolinpark."))
        self.assertEqual(parse_command("zentrale auftrag OpenChatCut prüfen"),("auftrag","OpenChatCut prüfen"))
        self.assertEqual(parse_command("/zentrale starten 1234567890abcdef"),("starten","1234567890abcdef"))
        self.assertEqual(parse_command("/zentrale ergebnis 1234567890abcdef"),("ergebnis","1234567890abcdef"))
        with self.assertRaises(ValueError):
            parse_command("/zentrale auftrag api_key=secret-secret")
    def test_telegram_web_schema_and_idempotent_retry(self):
        now=datetime(2026,10,1,12,0,tzinfo=timezone.utc)
        one=submit(self.r2,"private",update_id=81,chat_id="123",message="Prüfe OpenChatCut",now=now)
        two=submit(self.r2,"private",update_id=81,chat_id="123",message="Prüfe OpenChatCut",now=now)
        self.assertFalse(one["duplicate"])
        self.assertTrue(two["duplicate"])
        self.assertEqual(len(self.r2.objects),1)
        self.assertEqual(recent(self.r2,"private")[0]["status"],"DRAFT_REQUIRES_REVIEW")
        self.assertIn("Telegram",handle("/zentrale status",82,"123",client=self.r2,bucket="private").replace("telegram","Telegram"))
    def test_explicit_telegram_start_dispatches_exact_free_workflow_once(self):
        now=datetime(2026,10,1,12,0,tzinfo=timezone.utc)
        draft=submit(self.r2,"private",update_id=81,chat_id="123",message="Analyse OpenChatCut",now=now)
        import json
        calls=[]
        def fake_post(url,**kw):
            calls.append((url,kw))
            class Success:
                status_code=204
            return Success()
        reply=start_reviewed(self.r2,"private",draft["id"],"fake-github-actions-token",post=fake_post)
        self.assertIn("angenommen",reply)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][1]["json"]["inputs"],{"inbox_date":"2026-10-01","inbox_id":draft["id"]})
        key=next(iter(self.r2.objects))
        self.assertEqual(json.loads(self.r2.objects[key])["status"],"QUEUED_FREE_REVIEW")
        with self.assertRaises(ValueError):
            start_reviewed(self.r2,"private",draft["id"],"fake-github-actions-token",post=fake_post)
        self.assertEqual(len(calls),1)
    def test_private_video_start_routes_to_container_not_github(self):
        now=datetime(2026,10,4,16,0,tzinfo=timezone.utc)
        draft=submit(self.r2,"private",update_id=188,chat_id="123",
            message="SOFORTAUFTRAG – PRIVATE VIDEOPRODUKTION\nDünya wird 12. Geburtstag im Trampolinpark.",now=now)
        calls=[]
        def fake_post(url,**kw):
            calls.append((url,kw))
            class Accepted:status_code=202
            return Accepted()
        old_url=os.environ.get("PRIVATE_MEDIA_RUNTIME_URL")
        old_token=os.environ.get("PRIVATE_ASR_INTERNAL_TOKEN")
        os.environ["PRIVATE_MEDIA_RUNTIME_URL"]="https://private-runtime.example/private-video/jobs"
        os.environ["PRIVATE_ASR_INTERNAL_TOKEN"]="runtime-test-token"
        try:
            reply=start_reviewed(self.r2,"private",draft["id"],"github-token",post=fake_post)
        finally:
            if old_url is None:os.environ.pop("PRIVATE_MEDIA_RUNTIME_URL",None)
            else:os.environ["PRIVATE_MEDIA_RUNTIME_URL"]=old_url
            if old_token is None:os.environ.pop("PRIVATE_ASR_INTERNAL_TOKEN",None)
            else:os.environ["PRIVATE_ASR_INTERNAL_TOKEN"]=old_token
        self.assertIn("Container angenommen",reply)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0],"https://private-runtime.example/private-video/jobs")
        self.assertEqual(calls[0][1]["json"],{"task_id":draft["id"]})
        key=next(k for k in self.r2.objects if k.startswith("ai-central/v1/inbox/"))
        self.assertEqual(json.loads(self.r2.objects[key])["status"],"QUEUED_PRIVATE_VIDEO")
        self.assertNotIn("api.github.com",calls[0][0])
        status_key=f"ai-central/v1/private-video/{draft['id']}/status.json"
        self.r2.put_object(Bucket="private",Key=status_key,Body=json.dumps({
            "schema":"PRIVATE-VIDEO-STATUS-V1","task_id":draft["id"],"status":"RUNNING"}).encode())
        self.assertIn("RUNNING",result_summary(self.r2,"private",draft["id"]))

    def test_failed_telegram_start_restores_draft(self):
        now=datetime(2026,10,1,12,0,tzinfo=timezone.utc)
        draft=submit(self.r2,"private",update_id=89,chat_id="123",message="Container untersuchen",now=now)
        class Failure:status_code=403
        with self.assertRaises(RuntimeError):
            start_reviewed(self.r2,"private",draft["id"],"test-token",post=lambda *a,**kw:Failure())
        self.assertEqual(recent(self.r2,"private")[0]["status"],"DRAFT_REQUIRES_REVIEW")
    def test_ambiguous_network_timeout_does_not_rollback_or_duplicate(self):
        import requests,json
        now=datetime(2026,10,1,12,0,tzinfo=timezone.utc)
        task=submit(self.r2,"private",update_id=93,chat_id="123",message="Read actual MCP errors",now=now)
        def timeout(*args,**kwargs):
            raise requests.Timeout("upstream accepted? unknown")
        with self.assertRaisesRegex(RuntimeError,"unklar"):
            start_reviewed(self.r2,"private",task["id"],"fake-token",post=timeout)
        key=next(iter(self.r2.objects))
        self.assertEqual(json.loads(self.r2.objects[key])["status"],"QUEUED_FREE_REVIEW")
        with self.assertRaises(ValueError):
            start_reviewed(self.r2,"private",task["id"],"fake-token",post=timeout)
    def test_conflicting_etag_prevents_second_dispatch(self):
        now=datetime(2026,10,1,12,0,tzinfo=timezone.utc)
        task=submit(self.r2,"private",update_id=94,chat_id="123",message="Read actual container status",now=now)
        old_put=self.r2.put_object
        def competing(**kw):
            if "IfMatch" in kw:
                # Simulate a concurrent browser claim between GET and conditional PUT.
                self.r2.etags[kw["Key"]]="newer-concurrent-etag"
            return old_put(**kw)
        self.r2.put_object=competing
        with self.assertRaisesRegex(ValueError,"bereits"):
            start_reviewed(self.r2,"private",task["id"],"fake-token",post=lambda *a,**k:self.fail("should not dispatch"))
    def test_no_ack_if_storage_outage(self):
        self.r2.head_error=Forbidden()
        with self.assertRaises(Forbidden):
            submit(self.r2,"private",update_id=90,chat_id="123",message="Auftrag gültig")
        self.assertFalse(self.r2.objects)
    def test_result_summary_real_r2_lifecycle_and_report(self):
        task="1234567890abcdef"
        run="12345678"
        status_key=f"ai-central/v1/tasks/{task}/status.json"
        report_key=f"ai-central/v1/tasks/{task}/runs/{run}/report.json"
        self.assertIn("kein GitHub-Laufbericht",result_summary(self.r2,"private",task))
        self.r2.put_object(Bucket="private",Key=status_key,Body=json.dumps({
            "schema":"AI-CENTRAL-TASK-STATUS-V1","task_id":task,"github_run_id":run,
            "status":"RUNNING"}).encode())
        self.assertIn("RUNNING",handle(f"/zentrale ergebnis {task}",42,"123",client=self.r2,bucket="private"))
        self.r2.put_object(Bucket="private",Key=status_key,Body=json.dumps({
            "schema":"AI-CENTRAL-TASK-STATUS-V1","task_id":task,"github_run_id":run,
            "status":"PENDING_REVIEW"}).encode())
        self.r2.put_object(Bucket="private",Key=report_key,Body=json.dumps({
            "schema":"CLOUD-AI-CENTRAL-V1","task_id":task,"run_id":run,
            "status":"PENDING_REVIEW","results":[{"role":"research","status":"UNAVAILABLE"},
            {"role":"challenge","status":"ANSWER","attempts":[{"text":"private analysis content"}]}]
        }).encode())
        outcome=result_summary(self.r2,"private",task)
        self.assertIn("research: UNAVAILABLE",outcome)
        self.assertIn("challenge: ANSWER",outcome)
        self.assertIn("\n",outcome)
        self.assertNotIn("private analysis content",outcome)
        self.assertNotIn("Bearer",outcome)

    def test_result_tampering_and_cross_task_is_denied(self):
        task="1234567890abcdef";run="12345678"
        key=f"ai-central/v1/tasks/{task}/status.json"
        self.r2.put_object(Bucket="private",Key=key,Body=json.dumps({
            "schema":"AI-CENTRAL-TASK-STATUS-V1","task_id":"different-123456",
            "github_run_id":run,"status":"PENDING_REVIEW"}).encode())
        with self.assertRaises(ValueError):result_summary(self.r2,"private",task)
        with self.assertRaises(ValueError):result_summary(self.r2,"private","../../bad")
        with self.assertRaises(ValueError):parse_command("/zentrale ergebnis")
    def test_help_is_storage_independent(self):
        self.assertIn("keine automatische",handle("/zentrale hilfe",8,"1"))
if __name__=="__main__":unittest.main()
