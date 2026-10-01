import datetime as dt
import io
import json
import unittest
from scripts.ai_central_reviewed_inbox_dispatch import select_draft

class FakeR2:
    def __init__(self, drafts):
        self.drafts=drafts
    def list_objects_v2(self, **kw):
        prefix=kw["Prefix"]
        return {"Contents":[{"Key":k} for k in self.drafts if k.startswith(prefix)],"IsTruncated":False}
    def get_object(self, **kw):
        return {"Body":io.BytesIO(json.dumps(self.drafts[kw["Key"]]).encode())}

DAY="2026-10-01"
KEY="ai-central/v1/inbox/2026-10-01/example.json"
ID="1234567890abcdef"
def draft(**kw):
    x={"schema":"AI-INBOX-V1","id":ID,"created_at":"2026-10-01T12:00:00Z",
       "channel":"telegram","kind":"message","message":"Investigate startup readiness with real logs",
       "status":"DRAFT_REQUIRES_REVIEW","auto_dispatch":False}
    x.update(kw)
    return x

class ReviewBridgeTests(unittest.TestCase):
    def test_user_draft_maps_to_existing_guarded_task(self):
        result=select_draft(FakeR2({KEY:draft()}),"private",date=DAY,task_id=ID)
        self.assertEqual(result["task"]["question"],draft()["message"])
        self.assertIn("Require verifiable evidence",result["task"]["evidence"])
    def test_block_premature_auto_dispatch_and_file_tasks(self):
        for updates in ({"auto_dispatch":True},{"kind":"file"},{"status":"RUNNING"},{"message":"API_KEY=secretfoo"}):
            with self.subTest(updates=updates),self.assertRaises(ValueError):
                select_draft(FakeR2({KEY:draft(**updates)}),"private",date=DAY,task_id=ID)
    def test_missing_or_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            select_draft(FakeR2({}),"private",date=DAY,task_id=ID)
        other=KEY.replace("example","another")
        with self.assertRaises(ValueError):
            select_draft(FakeR2({KEY:draft(),other:draft()}),"private",date=DAY,task_id=ID)
    def test_invalid_date_and_id(self):
        for date,identifier in (("2026-19-01",ID),(DAY,"../../secret")):
            with self.assertRaises(ValueError):
                select_draft(FakeR2({KEY:draft()}),"private",date=date,task_id=identifier)
    def test_no_implicit_cross_date_scan(self):
        with self.assertRaises(ValueError):
            select_draft(FakeR2({KEY:draft()}),"private",date="2026-10-02",task_id=ID)
if __name__=="__main__":unittest.main()
