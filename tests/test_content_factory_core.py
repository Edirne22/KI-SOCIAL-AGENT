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
        self.assertTrue(key.startswith(f"{job.job_id}:r1:"))
        self.assertIn(job.human_approved_manifest[:16], key)
        retry_key = job.publish_handoff()
        self.assertEqual(key, retry_key)

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



    def test_approval_blocks_caption_changed_after_human_signoff(self):
        job = ProductionJob("make reel", status=JobStatus.READY_FOR_HUMAN)
        job.publish_payload["caption"] = "Freigegebener Text"
        job.publish_payload["platforms"] = ["instagram"]
        job.transition(JobStatus.APPROVED, actor="human")
        job.publish_payload["caption"] = "Manipulierter Text"
        with self.assertRaises(PermissionError):
            job.publish_handoff()

    def test_approval_blocks_platform_changed_after_human_signoff(self):
        job = ProductionJob("make reel", status=JobStatus.READY_FOR_HUMAN)
        job.publish_payload["caption"] = "Final"
        job.publish_payload["platforms"] = ["instagram"]
        job.transition(JobStatus.APPROVED, actor="human")
        job.publish_payload["platforms"] = ["instagram", "facebook"]
        with self.assertRaises(PermissionError):
            job.publish_handoff()

    def test_approval_blocks_future_publish_field_changed_after_signoff(self):
        job = ProductionJob("make reel", status=JobStatus.READY_FOR_HUMAN)
        job.publish_payload.update({
            "caption": "Final",
            "platforms": ["instagram"],
            "future_platform_option": {"cover_frame_ms": 1200},
        })
        job.transition(JobStatus.APPROVED, actor="human")
        job.publish_payload["future_platform_option"]["cover_frame_ms"] = 2400
        with self.assertRaises(PermissionError):
            job.publish_handoff()

    def test_approval_blocks_media_changed_after_human_signoff(self):
        job = ProductionJob("make reel", status=JobStatus.READY_FOR_HUMAN)
        media = MediaRef("final", "scratch://x/final.mp4", hashlib.sha256(b"a").hexdigest(), 1, "video/mp4", "render")
        job.media.append(media)
        job.transition(JobStatus.APPROVED, actor="human")
        job.media.append(MediaRef("swap", "scratch://x/swap.mp4", hashlib.sha256(b"b").hexdigest(), 1, "video/mp4", "attack"))
        with self.assertRaises(PermissionError):
            job.publish_handoff()


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

    def test_idempotency_key_conflict_is_blocked(self):
        service = InMemoryJobService()
        service.create_job("first command", idempotency_key="same")
        with self.assertRaises(ValueError):
            service.create_job("different command", idempotency_key="same")


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


    def test_noncanonical_input_is_blocked(self):
        from content_factory_handoff import HandoffError, ToolResult, ToolTask, run_machine
        job = ProductionJob("handoff")
        canonical = self._ref("source", b"real")
        job.media.append(canonical)
        forged = MediaRef("source", canonical.uri, hashlib.sha256(b"forged").hexdigest(), 6, "video/mp4", "attack")
        class Machine:
            name = "supoclip-adapter"
            def run(self, task):
                return ToolResult(task.job_id, task.revision, task.task_id, [], self.name)
        with self.assertRaises(HandoffError):
            run_machine(job, Machine(), ToolTask(job.job_id, job.revision, "forged", [forged]))

    def test_machine_cannot_spoof_provenance(self):
        from content_factory_handoff import HandoffError, ToolResult, ToolTask, run_machine
        job = ProductionJob("handoff")
        class Machine:
            name = "pollo-adapter"
            def run(self, task):
                return ToolResult(task.job_id, task.revision, task.task_id, [], "trusted-other-machine")
        with self.assertRaises(HandoffError):
            run_machine(job, Machine(), ToolTask(job.job_id, job.revision, "spoof"))

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



class AutonomousEditorialTests(unittest.TestCase):
    def test_event_trigger_autonomously_creates_production_but_not_approval(self):
        from autonomous_editorial import AutonomousEditorialDesk, EditorialTrigger, TriggerKind
        service = InMemoryJobService()
        desk = AutonomousEditorialDesk(service)
        trigger = EditorialTrigger(
            "news-ai-ogura-1", TriggerKind.EVENT, "New Ai Ogura interview",
            "MotoGP", ["https://example.invalid/source"], rider="Ai Ogura",
            relevance=92, requested_formats=["reel", "instagram-post"],
        )
        decision = desk.consider(trigger)
        job = service.get_job(decision.job_id)
        self.assertEqual("produce", decision.action)
        self.assertTrue(decision.created)
        self.assertEqual(JobStatus.CREATED, job.status)
        self.assertTrue(job.metadata["human_approval_required"])
        self.assertIsNone(job.human_approved_revision)

    def test_same_discovery_does_not_create_duplicate_production(self):
        from autonomous_editorial import AutonomousEditorialDesk, EditorialTrigger, TriggerKind
        service = InMemoryJobService()
        desk = AutonomousEditorialDesk(service)
        trigger = EditorialTrigger("same-news", TriggerKind.EVENT, "Toprak update", "WorldSBK", rider="Toprak", relevance=90)
        first = desk.consider(trigger)
        second = desk.consider(trigger)
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.job_id, second.job_id)

    def test_low_relevance_discovery_is_not_produced(self):
        from autonomous_editorial import AutonomousEditorialDesk, EditorialTrigger, TriggerKind
        service = InMemoryJobService()
        desk = AutonomousEditorialDesk(service, production_threshold=70)
        decision = desk.consider(EditorialTrigger("noise", TriggerKind.EVENT, "Old duplicate", "MotoGP", relevance=20))
        self.assertEqual("skip", decision.action)
        self.assertIsNone(decision.job_id)

    def test_race_weekend_schedule_creates_preproduction_job(self):
        from autonomous_editorial import AutonomousEditorialDesk, EditorialTrigger, TriggerKind
        service = InMemoryJobService()
        desk = AutonomousEditorialDesk(service)
        trigger = EditorialTrigger(
            "motogp-weekend-2026-x", TriggerKind.SCHEDULE, "Upcoming race weekend",
            "MotoGP", event_name="Race Weekend", relevance=100,
            requested_formats=["schedule-carousel", "weekend-preview-reel"],
        )
        decision = desk.consider(trigger)
        job = service.get_job(decision.job_id)
        self.assertEqual("schedule", job.metadata["trigger_kind"])
        self.assertIn("schedule-carousel", job.metadata["requested_formats"])
        self.assertEqual(JobStatus.CREATED, job.status)


class AutonomousStaffellaufTests(unittest.TestCase):
    def test_discovery_to_human_approval_to_publish_handoff(self):
        from autonomous_editorial import AutonomousEditorialDesk, EditorialTrigger, TriggerKind
        from content_factory_handoff import ToolResult, ToolTask, run_machine

        class Machine:
            def __init__(self, name, output):
                self.name, self.output = name, output
            def run(self, task):
                return ToolResult(task.job_id, task.revision, task.task_id, [self.output], self.name)

        service = InMemoryJobService()
        desk = AutonomousEditorialDesk(service)
        decision = desk.consider(EditorialTrigger(
            "toprak-interview-nightshift", TriggerKind.EVENT,
            "Toprak interview discovered overnight", "WorldSBK",
            rider="Toprak", relevance=98, requested_formats=["reel"],
        ))
        job = service.get_job(decision.job_id)

        source = MediaRef("source-video", "scratch://source/video.mp4", hashlib.sha256(b"source").hexdigest(), 6, "video/mp4", "discovery")
        job.media.append(source)
        job.transition(JobStatus.INGESTING)
        job.transition(JobStatus.TRANSCRIBING)
        job.transition(JobStatus.RESEARCHING)
        job.transition(JobStatus.WRITING)
        job.transition(JobStatus.STORYBOARDING)

        clip = MediaRef("clip", "scratch://supoclip/clip.mp4", hashlib.sha256(b"clip").hexdigest(), 4, "video/mp4", "supoclip")
        clip_result = run_machine(job, Machine("supoclip-adapter", clip), ToolTask(job.job_id, job.revision, "clip-task", [source]))

        broll = MediaRef("broll", "scratch://pollo/broll.mp4", hashlib.sha256(b"broll").hexdigest(), 5, "video/mp4", "pollo")
        run_machine(job, Machine("pollo-adapter", broll), ToolTask(job.job_id, job.revision, "broll-task", clip_result.outputs))

        job.transition(JobStatus.RENDERING)
        job.transition(JobStatus.QM)
        job.transition(JobStatus.READY_FOR_HUMAN)
        with self.assertRaises(PermissionError):
            job.publish_handoff()

        job.transition(JobStatus.APPROVED, actor="human")
        handoff = job.publish_handoff()
        self.assertEqual(JobStatus.PUBLISH_QUEUED, job.status)
        self.assertEqual(handoff, job.publish_handoff())
        self.assertIn(job.human_approved_manifest[:16], handoff)


if __name__ == "__main__":
    unittest.main()
