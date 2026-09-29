import hashlib
import tempfile
import unittest
from pathlib import Path

from content_factory_core import JobStatus, MediaRef, ProductionJob
from content_factory_service import InMemoryJobService
from media_storage import LocalScratchStorage


class ProductionJobTests(unittest.TestCase):
    def test_illegal_skip_to_approval_is_blocked(self):
        job = ProductionJob("make reel")
        with self.assertRaises(ValueError):
            job.transition(JobStatus.APPROVED, actor="human")

    def test_ai_cannot_approve_or_reject_human_job(self):
        job = ProductionJob("make reel", status=JobStatus.READY_FOR_HUMAN)
        with self.assertRaises(PermissionError):
            job.transition(JobStatus.APPROVED, actor="system")
        with self.assertRaises(PermissionError):
            job.transition(JobStatus.REJECTED, actor="system")

    def test_human_approval_allows_one_idempotent_handoff(self):
        job = ProductionJob("make reel", status=JobStatus.READY_FOR_HUMAN)
        job.transition(JobStatus.APPROVED, actor="human")
        key = job.publish_handoff()
        self.assertEqual(JobStatus.PUBLISH_QUEUED, job.status)
        self.assertEqual(f"{job.job_id}:r1", key)
        with self.assertRaises(PermissionError):
            job.publish_handoff()

    def test_human_change_request_creates_new_revision(self):
        job = ProductionJob("make reel", status=JobStatus.READY_FOR_HUMAN)
        job.transition(JobStatus.CHANGES_REQUESTED, actor="human")
        self.assertEqual(2, job.revision)
        self.assertEqual(JobStatus.CHANGES_REQUESTED, job.status)
        self.assertIsNone(job.human_approved_revision)

    def test_positive_control_valid_pipeline_reaches_human_gate(self):
        job = ProductionJob("make reel")
        for status in (
            JobStatus.INGESTING, JobStatus.TRANSCRIBING, JobStatus.RESEARCHING,
            JobStatus.WRITING, JobStatus.STORYBOARDING, JobStatus.RENDERING,
            JobStatus.QM, JobStatus.READY_FOR_HUMAN,
        ):
            job.transition(status)
        self.assertEqual(JobStatus.READY_FOR_HUMAN, job.status)


class StorageRedTeamTests(unittest.TestCase):
    def test_media_ref_rejects_fake_hash(self):
        with self.assertRaises(ValueError):
            MediaRef("x", "scratch://x/a", "fake", 1, "text/plain", "test")

    def test_scratch_storage_sanitizes_name_and_checks_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scratch"
            srcdir = Path(tmp) / "input"
            srcdir.mkdir()
            src = srcdir / "clip ü test.txt"
            src.write_text("trusted", encoding="utf-8")
            store = LocalScratchStorage(root)
            ref = store.put_file(src, provenance="unit-test")
            resolved = store.resolve_local(ref)
            self.assertTrue(resolved.is_file())
            self.assertNotIn("ü", resolved.name)
            resolved.write_text("tampered", encoding="utf-8")
            with self.assertRaises(ValueError):
                store.resolve_local(ref)

    def test_scratch_storage_blocks_foreign_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalScratchStorage(Path(tmp))
            digest = hashlib.sha256(b"x").hexdigest()
            ref = MediaRef("x", "file:///etc/passwd", digest, 1, "text/plain", "attack")
            with self.assertRaises(ValueError):
                store.resolve_local(ref)


class ServiceTests(unittest.TestCase):
    def test_create_job_is_idempotent(self):
        service = InMemoryJobService()
        first = service.create_job("make reel", idempotency_key="request-1")
        second = service.create_job("make reel", idempotency_key="request-1")
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.job.job_id, second.job.job_id)


if __name__ == "__main__":
    unittest.main()
