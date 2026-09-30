import tempfile
import unittest
from pathlib import Path

from content_factory_core import JobStatus, MediaRef
import hashlib
from content_factory_repository import (
    AttemptState, ConcurrentUpdateError, IdempotencyConflictError, SQLiteJobRepository,
)
from r2_storage import R2Storage


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.uploads = 0
        self.tamper_download = False

    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        self.uploads += 1
        self.objects[(bucket, key)] = Path(filename).read_bytes()

    def download_file(self, bucket, key, filename):
        data = self.objects[(bucket, key)]
        if self.tamper_download:
            data += b"tamper"
        Path(filename).write_bytes(data)


class SQLiteRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "factory.sqlite3"
        self.repo = SQLiteJobRepository(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_job_survives_repository_restart(self):
        stored, created = self.repo.create_job("build reel", idempotency_key="telegram:1")
        self.assertTrue(created)
        stored.job.transition(JobStatus.INGESTING)
        saved = self.repo.save_job(stored.job, expected_store_version=stored.store_version)

        restarted = SQLiteJobRepository(self.db)
        loaded = restarted.get_job(stored.job.job_id)
        self.assertEqual(JobStatus.INGESTING, loaded.job.status)
        self.assertEqual(saved.store_version, loaded.store_version)

    def test_create_idempotency_survives_restart(self):
        first, created = self.repo.create_job("build reel", idempotency_key="event:42")
        self.assertTrue(created)
        restarted = SQLiteJobRepository(self.db)
        second, created = restarted.create_job("build reel", idempotency_key="event:42")
        self.assertFalse(created)
        self.assertEqual(first.job.job_id, second.job.job_id)

    def test_idempotency_conflict_is_blocked(self):
        self.repo.create_job("one", idempotency_key="same")
        with self.assertRaises(IdempotencyConflictError):
            self.repo.create_job("two", idempotency_key="same")

    def test_stale_concurrent_write_is_blocked(self):
        first, _ = self.repo.create_job("build", idempotency_key="cas")
        a = self.repo.get_job(first.job.job_id)
        b = self.repo.get_job(first.job.job_id)
        a.job.transition(JobStatus.INGESTING)
        self.repo.save_job(a.job, expected_store_version=a.store_version)
        b.job.transition(JobStatus.INGESTING)
        with self.assertRaises(ConcurrentUpdateError):
            self.repo.save_job(b.job, expected_store_version=b.store_version)

    def test_attempt_retry_does_not_duplicate_external_execution_slot(self):
        stored, _ = self.repo.create_job("render", idempotency_key="render-job")
        a, claimed = self.repo.begin_attempt(
            job_id=stored.job.job_id, revision=1, step="render", idempotency_key="render:r1"
        )
        self.assertTrue(claimed)
        b, claimed = self.repo.begin_attempt(
            job_id=stored.job.job_id, revision=1, step="render", idempotency_key="render:r1"
        )
        self.assertFalse(claimed)
        self.assertEqual(a, b)

    def test_crash_marks_running_attempt_reconcile_not_retry(self):
        stored, _ = self.repo.create_job("render", idempotency_key="crash")
        self.repo.begin_attempt(
            job_id=stored.job.job_id, revision=1, step="external-render",
            idempotency_key="external:r1",
        )
        restarted = SQLiteJobRepository(self.db)
        self.assertEqual(1, restarted.mark_interrupted_attempts_for_reconciliation(stale_after_seconds=0))
        attempt = restarted.get_attempt(
            job_id=stored.job.job_id, revision=1, step="external-render",
            idempotency_key="external:r1",
        )
        self.assertEqual(AttemptState.RECONCILE, attempt.state)
        retry, claimed = restarted.begin_attempt(
            job_id=stored.job.job_id, revision=1, step="external-render",
            idempotency_key="external:r1",
        )
        self.assertFalse(claimed)
        self.assertEqual(AttemptState.RECONCILE, retry.state)

    def test_recovery_does_not_steal_fresh_running_attempt(self):
        stored, _ = self.repo.create_job("render", idempotency_key="fresh")
        self.repo.begin_attempt(
            job_id=stored.job.job_id, revision=1, step="external-render",
            idempotency_key="fresh:r1",
        )
        restarted = SQLiteJobRepository(self.db)
        self.assertEqual(0, restarted.mark_interrupted_attempts_for_reconciliation(stale_after_seconds=3600))
        attempt = restarted.get_attempt(
            job_id=stored.job.job_id, revision=1, step="external-render",
            idempotency_key="fresh:r1",
        )
        self.assertEqual(AttemptState.RUNNING, attempt.state)

    def test_stale_revision_attempt_is_blocked(self):
        stored, _ = self.repo.create_job("revise", idempotency_key="rev")
        stored.job.status = JobStatus.READY_FOR_HUMAN
        stored.job.transition(JobStatus.CHANGES_REQUESTED, actor="human")
        saved = self.repo.save_job(stored.job, expected_store_version=stored.store_version)
        self.assertEqual(2, saved.job.revision)
        with self.assertRaises(ConcurrentUpdateError):
            self.repo.begin_attempt(
                job_id=saved.job.job_id, revision=1, step="render", idempotency_key="stale"
            )

    def test_approval_survives_restart_but_publish_requires_explicit_handoff(self):
        stored, _ = self.repo.create_job("publish", idempotency_key="approval")
        stored.job.status = JobStatus.READY_FOR_HUMAN
        stored.job.publish_payload = {"caption": "approved", "platforms": ["instagram"]}
        stored.job.transition(JobStatus.APPROVED, actor="human")
        saved = self.repo.save_job(stored.job, expected_store_version=stored.store_version)

        restarted = SQLiteJobRepository(self.db)
        loaded = restarted.get_job(saved.job.job_id)
        self.assertEqual(JobStatus.APPROVED, loaded.job.status)
        self.assertIsNone(loaded.job.publish_handoff_key)
        key = loaded.job.publish_handoff()
        self.assertEqual(JobStatus.PUBLISH_QUEUED, loaded.job.status)
        self.assertTrue(key)

    def test_media_and_approval_manifest_survive_restart_exactly(self):
        stored, _ = self.repo.create_job("media approval", idempotency_key="media-approval")
        media = MediaRef(
            "asset-1", "r2://bucket/job/final.mp4", hashlib.sha256(b"final").hexdigest(),
            5, "video/mp4", "render:final",
        )
        stored.job.media.append(media)
        stored.job.status = JobStatus.READY_FOR_HUMAN
        stored.job.publish_payload = {"caption": "Final", "platforms": ["instagram"]}
        stored.job.transition(JobStatus.APPROVED, actor="human")
        manifest = stored.job.human_approved_manifest
        self.repo.save_job(stored.job, expected_store_version=stored.store_version)

        loaded = SQLiteJobRepository(self.db).get_job(stored.job.job_id)
        self.assertEqual([media], loaded.job.media)
        self.assertEqual(manifest, loaded.job.approval_manifest())
        self.assertEqual(manifest, loaded.job.human_approved_manifest)

    def test_concurrent_human_change_cannot_overwrite_approved_revision(self):
        stored, _ = self.repo.create_job("human race", idempotency_key="human-race")
        stored.job.status = JobStatus.READY_FOR_HUMAN
        self.repo.save_job(stored.job, expected_store_version=stored.store_version)

        approval = self.repo.get_job(stored.job.job_id)
        change = self.repo.get_job(stored.job.job_id)
        approval.job.transition(JobStatus.APPROVED, actor="human")
        self.repo.save_job(approval.job, expected_store_version=approval.store_version)

        change.job.transition(JobStatus.CHANGES_REQUESTED, actor="human")
        with self.assertRaises(ConcurrentUpdateError):
            self.repo.save_job(change.job, expected_store_version=change.store_version)

        final = self.repo.get_job(stored.job.job_id)
        self.assertEqual(JobStatus.APPROVED, final.job.status)
        self.assertEqual(1, final.job.revision)

    def test_full_persistent_staffellauf_survives_restart_before_publish(self):
        stored, _ = self.repo.create_job("autonomous racing reel", idempotency_key="story:toprak")
        job = stored.job
        for status in (
            JobStatus.INGESTING, JobStatus.TRANSCRIBING, JobStatus.RESEARCHING,
            JobStatus.WRITING, JobStatus.STORYBOARDING, JobStatus.RENDERING,
            JobStatus.QM, JobStatus.READY_FOR_HUMAN,
        ):
            job.transition(status)
        job.publish_payload = {"caption": "Final", "platforms": ["instagram"]}
        job.transition(JobStatus.APPROVED, actor="human")
        saved = self.repo.save_job(job, expected_store_version=stored.store_version)

        restarted = SQLiteJobRepository(self.db)
        loaded = restarted.get_job(job.job_id)
        self.assertEqual(JobStatus.APPROVED, loaded.job.status)
        self.assertEqual(job.human_approved_manifest, loaded.job.human_approved_manifest)
        self.assertIsNone(loaded.job.publish_handoff_key)

        handoff = loaded.job.publish_handoff()
        queued = restarted.save_job(
            loaded.job, expected_store_version=loaded.store_version
        )
        self.assertEqual(JobStatus.PUBLISH_QUEUED, queued.job.status)

        restarted_again = SQLiteJobRepository(self.db)
        final = restarted_again.get_job(job.job_id)
        self.assertEqual(handoff, final.job.publish_handoff())
        self.assertEqual(JobStatus.PUBLISH_QUEUED, final.job.status)


class R2StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.client = FakeS3()
        self.storage = R2Storage(
            self.client, bucket="edirne22-test", scratch_root=self.root / "scratch",
            max_size_bytes=64,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_round_trip_preserves_integrity(self):
        source = self.root / "video.mp4"
        source.write_bytes(b"video-data")
        media = self.storage.put_file(source, provenance="test")
        resolved = self.storage.resolve_local(media)
        self.assertEqual(b"video-data", resolved.read_bytes())
        self.assertTrue(media.uri.startswith("r2://edirne22-test/"))

    def test_tampered_download_is_rejected_and_deleted(self):
        source = self.root / "video.mp4"
        source.write_bytes(b"clean")
        media = self.storage.put_file(source, provenance="test")
        self.client.tamper_download = True
        with self.assertRaises(ValueError):
            self.storage.resolve_local(media)
        target_dir = self.root / "scratch" / media.media_id
        self.assertFalse(any(target_dir.iterdir()))

    def test_foreign_bucket_uri_is_rejected(self):
        source = self.root / "x.bin"
        source.write_bytes(b"x")
        media = self.storage.put_file(source, provenance="test")
        attacked = type(media)(
            media.media_id, media.uri.replace("edirne22-test", "attacker"),
            media.sha256, media.size_bytes, media.mime_type, media.provenance,
            media.version, media.created_at,
        )
        with self.assertRaises(ValueError):
            self.storage.resolve_local(attacked)

    def test_size_limit_blocks_upload(self):
        source = self.root / "large.bin"
        source.write_bytes(b"x" * 65)
        with self.assertRaises(ValueError):
            self.storage.put_file(source, provenance="test")
        self.assertEqual(0, self.client.uploads)


if __name__ == "__main__":
    unittest.main()
