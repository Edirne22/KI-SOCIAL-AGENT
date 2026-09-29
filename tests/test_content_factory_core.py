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


class FactoryHandoffTests(unittest.TestCase):
    def _ref(self, name: str, payload: bytes) -> MediaRef:
        return MediaRef(
            media_id=name,
            uri=f"scratch://{name}/{name}.mp4",
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
            mime_type="video/mp4",
            provenance="handoff-test",
        )

    def test_first_user_command_can_flow_machine_to_machine(self):
        from content_factory_handoff import ToolResult, ToolTask, run_machine

        class FakeMachine:
            def __init__(self, name, output):
                self.name, self.output = name, output
            def run(self, task):
                return ToolResult(task.job_id, task.revision, task.task_id, [self.output], self.name)

        service = InMemoryJobService()
        created = service.create_job(
            "Nimm mein Video, finde die besten Stellen und baue ein Reel",
            idempotency_key="buelent-command-1",
        )
        job = created.job
        source = self._ref("source", b"raw-video")
        job.media.append(source)

        clip = self._ref("supoclip-output", b"vertical-clip")
        task1 = ToolTask(job.job_id, job.revision, "clip-1", [source])
        result1 = run_machine(job, FakeMachine("supoclip-adapter", clip), task1)

        master = self._ref("edit-output", b"edited-master")
        task2 = ToolTask(job.job_id, job.revision, "edit-1", result1.outputs)
        result2 = run_machine(job, FakeMachine("openchatcut-adapter", master), task2)

        self.assertEqual([clip], result1.outputs)
        self.assertEqual([master], result2.outputs)
        self.assertEqual({"source", "supoclip-output", "edit-output"}, {m.media_id for m in job.media})

    def test_cross_job_output_is_blocked(self):
        from content_factory_handoff import HandoffError, ToolResult, ToolTask, run_machine

        job = ProductionJob("job one")
        output = self._ref("foreign", b"x")

        class EvilMachine:
            name = "evil"
            def run(self, task):
                return ToolResult("another-job", task.revision, task.task_id, [output], self.name)

        with self.assertRaises(HandoffError):
            run_machine(job, EvilMachine(), ToolTask(job.job_id, job.revision, "attack"))

    def test_stale_revision_is_blocked(self):
        from content_factory_handoff import HandoffError, ToolResult, ToolTask, run_machine

        job = ProductionJob("revision test", status=JobStatus.READY_FOR_HUMAN)
        old_revision = job.revision
        job.transition(JobStatus.CHANGES_REQUESTED, actor="human")
        output = self._ref("stale", b"x")

        class StaleMachine:
            name = "slow-renderer"
            def run(self, task):
                return ToolResult(job.job_id, old_revision, task.task_id, [output], self.name)

        with self.assertRaises(HandoffError):
            run_machine(job, StaleMachine(), ToolTask(job.job_id, old_revision, "stale"))


if __name__ == "__main__":
    unittest.main()
