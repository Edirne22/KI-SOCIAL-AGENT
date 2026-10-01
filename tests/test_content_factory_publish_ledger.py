"""Block 9 durable publish-gate tests with simulated, never real publishers."""
import tempfile
import unittest
from pathlib import Path

from content_factory_core import JobStatus, ProductionJob
from content_factory_control_center import ContractPublisher, ControlCenterError, PublishReceipt
from content_factory_publish_ledger import AmbiguousPublication, DurablePublisherBridge, FilePublishLedger


def queued():
    job = ProductionJob("human-approved racing test")
    job.status = JobStatus.READY_FOR_HUMAN
    job.publish_payload = {"caption": "Sample; no real platform publishing"}
    job.transition(JobStatus.APPROVED, actor="human")
    job.publish_handoff()
    return job


class CountingPublisher(ContractPublisher):
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def publish(self, job, platform, handoff_key):
        self.calls += 1
        if self.fail:
            raise TimeoutError("outcome unknown")
        return super().publish(job, platform, handoff_key)


class DurablePublishTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.ledger = FilePublishLedger(self.path)
        self.job = queued()

    def test_approved_pub_records_proof(self):
        p = CountingPublisher()
        result = DurablePublisherBridge(self.ledger).publish(self.job, platform="instagram", publisher=p)
        self.assertEqual(1, p.calls)
        self.assertEqual("SIMULATED_PUBLISH_PROOF", result.proof)
        self.assertEqual(result, self.ledger.receipt(self.job.publish_handoff_key, "instagram"))

    def test_restart_reuses_receipt_without_reposting(self):
        p = CountingPublisher()
        first = DurablePublisherBridge(self.ledger).publish(self.job, platform="instagram", publisher=p)
        second = DurablePublisherBridge(FilePublishLedger(self.path)).publish(self.job, platform="instagram", publisher=p)
        self.assertEqual(first, second)
        self.assertEqual(1, p.calls)

    def test_cross_platform_independent_claim(self):
        p = CountingPublisher()
        bridge = DurablePublisherBridge(self.ledger)
        ig = bridge.publish(self.job, platform="instagram", publisher=p)
        fb = bridge.publish(self.job, platform="facebook", publisher=p)
        self.assertEqual(2, p.calls)
        self.assertNotEqual(ig.external_id, fb.external_id)

    def test_no_human_approval_no_claim(self):
        job = ProductionJob("unapproved")
        with self.assertRaises(ControlCenterError):
            self.ledger.reserve(job, "instagram")
        self.assertEqual([], list(self.path.glob("*.intent.json")))

    def test_cross_revision_approval_blocked(self):
        self.job.revision += 1
        with self.assertRaises(ControlCenterError):
            self.ledger.reserve(self.job, "instagram")

    def test_media_change_after_human_approval_blocked(self):
        self.job.publish_payload["caption"] = "changed"
        with self.assertRaises(ControlCenterError):
            self.ledger.reserve(self.job, "instagram")

    def test_crash_after_reservation_never_retries(self):
        self.assertIsNone(self.ledger.reserve(self.job, "instagram"))
        restarted = FilePublishLedger(self.path)
        with self.assertRaises(AmbiguousPublication):
            DurablePublisherBridge(restarted).publish(self.job, platform="instagram", publisher=CountingPublisher())

    def test_timeout_never_blind_retries(self):
        bad = CountingPublisher(fail=True)
        with self.assertRaises(AmbiguousPublication):
            DurablePublisherBridge(self.ledger).publish(self.job, platform="instagram", publisher=bad)
        good = CountingPublisher()
        with self.assertRaises(AmbiguousPublication):
            DurablePublisherBridge(FilePublishLedger(self.path)).publish(self.job, platform="instagram", publisher=good)
        self.assertEqual(0, good.calls)

    def test_reconcile_existing_claim_and_resume_without_repost(self):
        self.ledger.reserve(self.job, "instagram")
        proof = PublishReceipt(self.job.publish_handoff_key, "instagram", "external-existing", "provider-verification")
        self.ledger.record_receipt(self.job.publish_handoff_key, "instagram", proof)
        p = CountingPublisher()
        result = DurablePublisherBridge(FilePublishLedger(self.path)).publish(self.job, platform="instagram", publisher=p)
        self.assertEqual(proof, result)
        self.assertEqual(0, p.calls)

    def test_forged_or_cross_platform_receipt_blocked(self):
        self.ledger.reserve(self.job, "instagram")
        bad = PublishReceipt(self.job.publish_handoff_key, "facebook", "123", "provider-proof")
        with self.assertRaises(ControlCenterError):
            self.ledger.record_receipt(self.job.publish_handoff_key, "instagram", bad)
        self.assertIsNone(self.ledger.receipt(self.job.publish_handoff_key, "instagram"))

    def test_receipt_without_claim_rejected(self):
        r = PublishReceipt(self.job.publish_handoff_key, "instagram", "123", "verified-proof")
        with self.assertRaises(ControlCenterError):
            self.ledger.record_receipt(self.job.publish_handoff_key, "instagram", r)

    def test_conflicting_reconciliation_blocked(self):
        self.ledger.reserve(self.job, "instagram")
        first = PublishReceipt(self.job.publish_handoff_key, "instagram", "123", "proof1")
        second = PublishReceipt(self.job.publish_handoff_key, "instagram", "456", "proof2")
        self.ledger.record_receipt(self.job.publish_handoff_key, "instagram", first)
        with self.assertRaises(AmbiguousPublication):
            self.ledger.record_receipt(self.job.publish_handoff_key, "instagram", second)

    def test_bad_ledger_receipt_requires_manual_check(self):
        self.ledger.reserve(self.job, "instagram")
        _, path = self.ledger._paths(self.job.publish_handoff_key, "instagram")
        path.write_text("{bad json")
        with self.assertRaises(AmbiguousPublication):
            self.ledger.reserve(self.job, "instagram")

    def test_platform_no_name_rejected(self):
        with self.assertRaises(ControlCenterError):
            self.ledger.reserve(self.job, "")


if __name__ == "__main__":
    unittest.main()
