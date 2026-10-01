import io, json, os, unittest
from unittest.mock import patch
from ai_central_inbox import make_request,save_telegram_message,SCHEMA

class Missing(Exception):
    response={"Error":{"Code":"NoSuchKey"}}
class FakeR2:
    def __init__(self):self.files={}
    def get_object(self,*,Bucket,Key):
        if Key not in self.files:raise Missing()
        return {"Body":io.BytesIO(self.files[Key])}
    def put_object(self,*,Bucket,Key,Body,ContentType):
        self.files[Key]=Body
class InboxTests(unittest.TestCase):
    def test_schema_and_rejected_control_text(self):
        d=make_request("Prüfe meinen Bericht",channel="web")
        self.assertEqual(d["schema"],SCHEMA)
        self.assertEqual(d["status"],"PENDING_REVIEW")
        for invalid in ("", "a"*2501, "hi\\x00"):
            with self.assertRaises(ValueError):make_request(invalid,channel="telegram")
        with self.assertRaises(ValueError):make_request("good",channel="agent")
    def test_duplicate_telegram_id_no_second_write(self):
        r=FakeR2()
        env={"R2_ACCOUNT_ID":"test","R2_ACCESS_KEY_ID":"test","R2_SECRET_ACCESS_KEY":"test","R2_BUCKET_NAME":"private"}
        with patch.dict(os.environ,env):
            first=save_telegram_message("Nur Diagnose",123,client=r)
            second=save_telegram_message("Nur Diagnose",123,client=r)
        self.assertEqual(first,second)
        self.assertEqual(len(r.files),1)
        data=json.loads(next(iter(r.files.values())))
        self.assertEqual(data["channel"],"telegram")
        self.assertEqual(data["status"],"PENDING_REVIEW")
    def test_missing_credentials_fails_closed(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(RuntimeError):save_telegram_message("Auftrag",123,client=FakeR2())
    def test_id_validation(self):
        with self.assertRaises(ValueError):make_request("hi",channel="telegram",source_id="../../bad")

if __name__=="__main__":unittest.main()
