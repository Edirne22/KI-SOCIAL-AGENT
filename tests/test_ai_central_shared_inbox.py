import io
import unittest
from datetime import datetime, timezone
from scripts.ai_central_shared_inbox import parse_command, submit, recent, handle

class NotFound(Exception):
    response={"Error":{"Code":"404"}}
class Forbidden(Exception):
    response={"Error":{"Code":"403"}}
class FakeR2:
    def __init__(self):
        self.objects={}
        self.head_error=None
    def head_object(self,**kw):
        if self.head_error:raise self.head_error
        if kw["Key"] not in self.objects:raise NotFound()
        return {"ContentLength":len(self.objects[kw["Key"]])}
    def put_object(self,**kw):
        self.objects[kw["Key"]]=kw["Body"]
    def list_objects_v2(self,**kw):
        return {"Contents":[{"Key":k} for k in self.objects if k.startswith(kw["Prefix"])]}
    def get_object(self,**kw):
        return {"Body":io.BytesIO(self.objects[kw["Key"]])}
class Inbox(unittest.TestCase):
    def setUp(self):self.r2=FakeR2()
    def test_commands_do_not_intercept_existing_router(self):
        self.assertIsNone(parse_command("T1,T3"))
        self.assertEqual(parse_command("/zentrale status"),("status",None))
        self.assertEqual(parse_command("zentrale auftrag OpenChatCut prüfen"),("auftrag","OpenChatCut prüfen"))
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
    def test_no_ack_if_storage_outage(self):
        self.r2.head_error=Forbidden()
        with self.assertRaises(Forbidden):
            submit(self.r2,"private",update_id=90,chat_id="123",message="Auftrag gültig")
        self.assertFalse(self.r2.objects)
    def test_help_is_storage_independent(self):
        self.assertIn("keine automatische",handle("/zentrale hilfe",8,"1"))
if __name__=="__main__":unittest.main()
