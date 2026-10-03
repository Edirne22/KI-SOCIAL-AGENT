"""Red-team: no early Telegram message, no duplicates, no discard notice."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from scripts.block89_notify_revision_ready import notify_verified_revision

class FakeStorage:
    bucket = "private"
    def __init__(self):
        self.claims = set()
        self.client = self
    def put_object(self, **kw):
        key = kw["Key"]
        if key in self.claims:
            exc = RuntimeError("precondition")
            exc.response = {"Error": {"Code": "PreconditionFailed"}}
            raise exc
        self.claims.add(key)

class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.id = str(uuid4())
        self.preview = str(uuid4())
        self.storage = FakeStorage()
        self.sent = []
        run = {"state":"READY_FOR_HUMAN", "revision":2, "request_id":str(uuid4()),
               "preview":{"preview_id":self.preview,"manifest":"verified"}}
        self.job = SimpleNamespace(revision=2,status=SimpleNamespace(value="ready_for_human"),
                                   metadata={"revision_render":run})
        self.repo = SimpleNamespace(get_job=lambda _: SimpleNamespace(job=self.job))
        self.state = {"state":"READY_FOR_HUMAN","revision":2,"preview_id":self.preview,
                      "manifest":"verified"}
    def call(self):
        with patch("scripts.block89_notify_revision_ready._read_state",
                   return_value=(self.state, "etag")), patch(
                   "content_factory_revision_render._deliver", return_value="READY_FOR_HUMAN"):
            return notify_verified_revision(self.id, storage=self.storage,
                        repository=self.repo, sender=self.sent.append)
    def test_success_then_idempotent_replay(self):
        self.assertEqual(self.call(),"SENT")
        self.assertEqual(self.call(),"ALREADY_ATTEMPTED")
        self.assertEqual(len(self.sent),1)
        self.assertIn("Keine automatische Veröffentlichung",self.sent[0])
    def test_unverified_revision_cannot_notify(self):
        self.state["revision"]=1
        with self.assertRaises(ValueError): self.call()
        self.assertEqual(self.sent,[])
        self.assertFalse(self.storage.claims)
    def test_discard_never_notifies(self):
        self.state={"state":"REVIEW_APPLIED","review":{"action":"discard"}}
        self.assertEqual(self.call(),"SKIPPED_DISCARDED")
        self.assertEqual(self.sent,[])
    def test_missing_private_delivery_never_notifies(self):
        with patch("scripts.block89_notify_revision_ready._read_state",
                   return_value=(self.state, "etag")), patch(
                   "content_factory_revision_render._deliver", side_effect=ValueError("bad sha")):
            with self.assertRaises(ValueError):
                notify_verified_revision(self.id,storage=self.storage,
                    repository=self.repo,sender=self.sent.append)
        self.assertFalse(self.storage.claims)

if __name__=="__main__": unittest.main()
