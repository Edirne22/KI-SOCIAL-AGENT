import datetime as dt
import io
import json
import unittest
from scripts.ai_central_reviewed_inbox_dispatch import select_draft
from scripts.ai_central_shared_inbox import parse_command, start_reviewed

DAY="2026-10-01"
ID="1234567890abcdef"
KEY="ai-central/v1/inbox/"+DAY+"/example.json"
def approved(scope):
    return {"schema":"AI-INBOX-V1","id":ID,"created_at":DAY+"T12:00:00Z",
            "channel":"telegram","kind":"message","message":"Find actual cause of Cloudflare MCP timeout",
            "status":"QUEUED_FREE_REVIEW","auto_dispatch":False,
            "approved_at":DAY+"T12:05:00Z","dispatch_target":"ai-central-inbox-agent.yml",
            "inference_scope":scope}
class R2:
    def __init__(self, entry):
        self.objects={KEY:json.dumps(entry).encode()}
        self.etags={KEY:"v1"}
    def list_objects_v2(self,**kw):
        return {"Contents":[{"Key":KEY}],"IsTruncated":False}
    def get_object(self,**kw):
        return {"Body":io.BytesIO(self.objects[kw["Key"]]),"ETag":self.etags[kw["Key"]]}
    def put_object(self,**kw):
        if kw.get("IfMatch")!=self.etags[kw["Key"]]:
            raise ValueError("invalid optimistic lock")
        self.objects[kw["Key"]]=kw["Body"]
        self.etags[kw["Key"]]="v2"
        return {"ETag":"v2"}
class TeamContract(unittest.TestCase):
    def test_one_approved_scope_cannot_be_replayed_in_other_mode(self):
        for scope,mode,wrong in (("nvidia/free-team","free-team","free-only"),
                                 ("openrouter/free","free-only","free-team")):
            c=R2(approved(scope))
            good=select_draft(c,"private",date=DAY,task_id=ID,require_queued=True,mode=mode)
            self.assertEqual(good["inbox_id"],ID)
            with self.assertRaisesRegex(ValueError,"explicitly approved"):
                select_draft(c,"private",date=DAY,task_id=ID,require_queued=True,mode=wrong)
    def test_telegram_requires_explicit_team_command_and_scopes_single_dispatch(self):
        self.assertEqual(parse_command("/zentrale team "+ID),("team",ID))
        self.assertEqual(parse_command("/zentrale starten "+ID),("starten",ID))
        calls=[]
        class Accepted: status_code=204
        c=R2({"schema":"AI-INBOX-V1","id":ID,"created_at":DAY+"T12:00:00Z",
              "channel":"telegram","kind":"message","message":"Review MCP logs",
              "status":"DRAFT_REQUIRES_REVIEW","auto_dispatch":False})
        msg=start_reviewed(c,"private",ID,"FAKE",post=lambda *a,**kw:(calls.append(kw),Accepted())[1],mode="free-team")
        self.assertIn("angenommen",msg)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0]["json"]["inputs"]["team_mode"],"free-team")
        self.assertEqual(json.loads(c.objects[KEY])["inference_scope"],"nvidia/free-team")
        with self.assertRaises(ValueError):
            start_reviewed(c,"private",ID,"FAKE",post=lambda *a,**kw:self.fail("duplicate"),mode="free-team")
    def test_invalid_mode_never_calls_github(self):
        c=R2(approved("openrouter/free"))
        with self.assertRaisesRegex(ValueError,"Modus"):
            start_reviewed(c,"private",ID,"FAKE",post=lambda *a,**kw:self.fail("unsafe"),mode="paid")
if __name__=="__main__":unittest.main()
