"""R2 ledger negative/positive/restart/concurrency tests; no platform calls."""
import io
import json
import threading
import unittest

from content_factory_core import ProductionJob, JobStatus
from content_factory_control_center import PublishReceipt, ControlCenterError
from content_factory_r2_publish_ledger import R2PublishLedger
from content_factory_publish_ledger import AmbiguousPublication


class R2Failure(Exception):
    def __init__(self, code):
        self.response={"Error":{"Code":code}}


class FakeR2:
    def __init__(self):
        self.objects={}
        self.lock=threading.Lock()
        self.fail_after_write=False
        self.block_reads=False
    def get_object(self, *, Bucket, Key):
        if self.block_reads:
            raise ConnectionError("lost connection")
        with self.lock:
            if (Bucket,Key) not in self.objects:
                raise R2Failure("NoSuchKey")
            body=self.objects[(Bucket,Key)]
        return {"Body":io.BytesIO(body)}
    def put_object(self, *, Bucket, Key, Body, ContentType, IfNoneMatch):
        assert IfNoneMatch=="*" and ContentType=="application/json"
        with self.lock:
            if (Bucket,Key) in self.objects:
                raise R2Failure("PreconditionFailed")
            self.objects[(Bucket,Key)]=bytes(Body)
        if self.fail_after_write:
            raise ConnectionError("server committed but response lost")
        return {"ETag":"hash"}


class Store:
    bucket="shared-private-test"
    def __init__(self,client):
        self.client=client


def approved():
    job=ProductionJob("verified editorial test, not a real social post")
    job.status=JobStatus.READY_FOR_HUMAN
    job.publish_payload={"caption":"Offline unit-test caption"}
    job.transition(JobStatus.APPROVED,actor="human")
    job.publish_handoff()
    return job


class R2LedgerTests(unittest.TestCase):
    def setUp(self):
        self.client=FakeR2()
        self.storage=Store(self.client)
        self.ledger=R2PublishLedger(self.storage)
        self.job=approved()
        self.key=self.job.publish_handoff_key

    def test_atomic_claim_across_independent_workers(self):
        self.assertIsNone(self.ledger.reserve(self.job,"instagram"))
        restarted=R2PublishLedger(self.storage)
        with self.assertRaises(AmbiguousPublication):
            restarted.reserve(self.job,"instagram")

    def test_concurrent_race_only_one_claim(self):
        outcomes=[]
        def attempt():
            try:
                self.ledger.reserve(self.job,"instagram")
                outcomes.append("reserved")
            except AmbiguousPublication:
                outcomes.append("blocked")
        threads=[threading.Thread(target=attempt) for _ in range(6)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertCountEqual(outcomes,["reserved"]+["blocked"]*5)

    def test_real_receipt_survives_restart_with_no_second_post(self):
        self.ledger.reserve(self.job,"instagram")
        proof=PublishReceipt(self.key,"instagram","real-proof-id","verified-platform-evidence")
        self.assertEqual(self.ledger.record_receipt(self.key,"instagram",proof),proof)
        next_worker=R2PublishLedger(self.storage)
        self.assertEqual(next_worker.reserve(self.job,"instagram"),proof)

    def test_cross_platform_has_separate_claims(self):
        self.assertIsNone(self.ledger.reserve(self.job,"instagram"))
        self.assertIsNone(self.ledger.reserve(self.job,"facebook"))

    def test_unapproved_tampered_or_cross_revision_job_refused(self):
        job=approved()
        job.human_approved_at=None
        with self.assertRaises(ControlCenterError):
            self.ledger.reserve(job,"instagram")
        job=self.job
        job.publish_payload["caption"]="modified"
        with self.assertRaises(ControlCenterError):
            self.ledger.reserve(job,"instagram")
        self.assertEqual(self.client.objects,{})

    def test_unknown_write_after_actual_commit_blocks_repeat(self):
        self.client.fail_after_write=True
        with self.assertRaises(AmbiguousPublication):
            self.ledger.reserve(self.job,"facebook")
        self.client.fail_after_write=False
        with self.assertRaises(AmbiguousPublication):
            self.ledger.reserve(self.job,"facebook")

    def test_network_read_error_is_never_treated_as_missing(self):
        self.client.block_reads=True
        with self.assertRaises(AmbiguousPublication):
            self.ledger.reserve(self.job,"facebook")
        self.assertFalse(self.client.objects)

    def test_receipt_without_claim_and_cross_platform_rejected(self):
        proof=PublishReceipt(self.key,"instagram","provider-id","verified")
        with self.assertRaises(AmbiguousPublication):
            self.ledger.record_receipt(self.key,"instagram",proof)
        self.ledger.reserve(self.job,"instagram")
        with self.assertRaises(ControlCenterError):
            self.ledger.record_receipt(self.key,"instagram",
                PublishReceipt(self.key,"facebook","provider-id","verified"))

    def test_simulated_receipt_is_never_accepted_as_real(self):
        self.ledger.reserve(self.job,"instagram")
        with self.assertRaises(ControlCenterError):
            self.ledger.record_receipt(self.key,"instagram",
                PublishReceipt(self.key,"instagram","sim-123","SIMULATED_PUBLISH_PROOF"))

    def test_conflicting_receipt_and_corrupt_receipt_fail_closed(self):
        self.ledger.reserve(self.job,"instagram")
        first=PublishReceipt(self.key,"instagram","id-1","platform-proof")
        self.ledger.record_receipt(self.key,"instagram",first)
        with self.assertRaises(AmbiguousPublication):
            self.ledger.record_receipt(self.key,"instagram",
                PublishReceipt(self.key,"instagram","id-2","platform-proof"))
        _,receipt_key=self.ledger._paths(self.key,"instagram")
        self.client.objects[(self.storage.bucket,receipt_key)]=b"{not json"
        with self.assertRaises(AmbiguousPublication):
            self.ledger.receipt(self.key,"instagram")


if __name__=="__main__":
    unittest.main()
