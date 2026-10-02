"""Block 8: real persistent ACK is the only authority for immutable edit tickets."""
from concurrent.futures import ThreadPoolExecutor
import json
import unittest
from unittest.mock import patch
from uuid import uuid4

from content_factory_core import JobStatus
from content_factory_dashboard_review_applier import apply_review_request
from content_factory_dashboard_review_ack import acknowledge_persisted_review
from content_factory_revision_intake import (
    derive_canonical_edit_request, AmbiguousRevisionIntake, RevisionIntakeError, PREFIX,
)
from content_factory_r2_job_repository import R2JobRepository
from tests.test_content_factory_r2_job_repository import Storage, ready_job


class RevisionIntakeTests(unittest.TestCase):
    def setUp(self):
        self.storage = Storage()
        self.repo = R2JobRepository(self.storage)
        self.job = ready_job()
        self.repo.register_job(self.job)
        self.preview_id = str(uuid4())
        self.request_id = str(uuid4())
        manifest = self.job.approval_manifest()
        media = self.job.media[0]
        self.review = {
            "schema": "FACTORY-REVIEW-INTENT-V1",
            "request_id": self.request_id,
            "preview_id": self.preview_id,
            "job_id": self.job.job_id,
            "revision": 1,
            "manifest": manifest,
            "actor": "authenticated_dashboard_owner",
            "status": "PENDING_FACTORY_APPLICATION",
            "action": "change",
            "text": "Please update the opening",
        }
        self.state = {
            "schema": "FACTORY-PREVIEW-STATE-V1",
            "job_id": self.job.job_id,
            "revision": 1,
            "manifest": manifest,
            "preview_id": None,
            "state": "REVIEW_REQUESTED",
            "review": self.review,
        }
        preview = {
            "schema": "FACTORY-MEDIA-PREVIEW-V1",
            "preview_id": self.preview_id,
            "job_id": self.job.job_id,
            "revision": 1,
            "manifest": manifest,
            "state": "READY_FOR_HUMAN",
            "qm_passed": True,
            "caption": self.job.publish_payload["caption"],
            "media": {
                "media_id": media.media_id,
                "key": media.uri.removeprefix("r2://private-factory-test/"),
                "sha256": media.sha256,
                "size_bytes": media.size_bytes,
                "mime_type": media.mime_type,
            },
        }
        self.state_key = "ai-central/v1/preview-state/" + self.job.job_id + ".json"
        self.ticket_key = f"{PREFIX}{self.job.job_id}/r2-{self.request_id}.json"
        self.storage.client.seed(self.storage.bucket, self.state_key, self.state)
        self.storage.client.seed(self.storage.bucket,
            "ai-central/v1/previews/" + self.preview_id + ".json", preview)

    def write_state(self):
        current = self.storage.client.get_object(
            Bucket=self.storage.bucket, Key=self.state_key,
        )
        self.storage.client.put_object(
            Bucket=self.storage.bucket, Key=self.state_key,
            Body=json.dumps(self.state).encode(),
            ContentType="application/json", IfMatch=current["ETag"],
        )

    def ack(self):
        apply_review_request(self.job.job_id, storage=self.storage, repository=self.repo)
        self.assertEqual(
            acknowledge_persisted_review(self.job.job_id, storage=self.storage, repository=self.repo),
            "ACKNOWLEDGED",
        )

    def ticket(self):
        result = self.storage.client.get_object(
            Bucket=self.storage.bucket, Key=self.ticket_key,
        )
        return json.loads(result["Body"].read())

    def test_authenticated_change_generates_one_private_nonrendering_ticket(self):
        self.ack()
        status, key = derive_canonical_edit_request(
            self.job.job_id, storage=self.storage, repository=self.repo,
        )
        self.assertEqual(status, "QUEUED_AWAITING_CREATIVE_PLAN")
        self.assertEqual(key, self.ticket_key)
        ticket = self.ticket()
        self.assertEqual(ticket["state"], "AWAITING_CREATIVE_PLAN")
        self.assertEqual(ticket["source_revision"], 1)
        self.assertEqual(ticket["revision"], 2)
        self.assertEqual(ticket["request_id"], self.request_id)
        self.assertEqual(ticket["human_request"], "Please update the opening")
        self.assertFalse(ticket["render_approved"])
        self.assertFalse(ticket["publish_approved"])
        self.assertEqual(ticket["source_media"]["sha256"], self.job.media[0].sha256)
        self.assertEqual(
            derive_canonical_edit_request(self.job.job_id, storage=self.storage, repository=self.repo),
            ("ALREADY_QUEUED", self.ticket_key),
        )

    def test_before_ack_or_forged_ack_does_not_create_ticket(self):
        with self.assertRaises(RevisionIntakeError):
            derive_canonical_edit_request(self.job.job_id, storage=self.storage, repository=self.repo)
        self.state["state"] = "REVIEW_APPLIED"
        self.review.update(status="APPLIED_TO_FACTORY", canonical_store_version=2)
        self.write_state()
        with self.assertRaises(RevisionIntakeError):
            derive_canonical_edit_request(self.job.job_id, storage=self.storage, repository=self.repo)
        self.assertNotIn((self.storage.bucket, self.ticket_key), self.storage.client.objects)

    def test_discard_never_generates_edit_or_publish(self):
        self.review.update(action="discard", text="")
        self.write_state()
        self.ack()
        self.assertEqual(self.repo.get_job(self.job.job_id).job.status, JobStatus.REJECTED)
        with self.assertRaises(RevisionIntakeError):
            derive_canonical_edit_request(self.job.job_id, storage=self.storage, repository=self.repo)

    def test_stale_changed_canonical_revision_fails_closed(self):
        self.ack()
        stored = self.repo.get_job(self.job.job_id)
        job = stored.job
        job.revision += 1
        self.repo.save_job(job, expected_store_version=stored.store_version)
        with self.assertRaisesRegex(RevisionIntakeError, "canonical changed revision"):
            derive_canonical_edit_request(self.job.job_id, storage=self.storage, repository=self.repo)

    def test_conflicting_existing_ticket_is_not_overwritten(self):
        self.ack()
        self.storage.client.seed(self.storage.bucket, self.ticket_key,
                                 {"schema": "FAKE-EDIT", "publish_approved": True})
        with self.assertRaisesRegex(AmbiguousRevisionIntake, "conflicts"):
            derive_canonical_edit_request(self.job.job_id, storage=self.storage, repository=self.repo)
        self.assertEqual(self.ticket()["schema"], "FAKE-EDIT")

    def test_lost_s3_write_response_is_reconciled_without_republish(self):
        self.ack()
        self.storage.client.fail_after_commit = True
        try:
            status, _ = derive_canonical_edit_request(
                self.job.job_id, storage=self.storage, repository=self.repo,
            )
        finally:
            self.storage.client.fail_after_commit = False
        self.assertEqual(status, "RECOVERED_AFTER_UNCERTAIN_WRITE")
        self.assertEqual(len([key for _, key in self.storage.client.objects if key.startswith(PREFIX)]), 1)

    def test_parallel_retries_create_only_one_ticket(self):
        self.ack()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: derive_canonical_edit_request(
                self.job.job_id, storage=self.storage, repository=self.repo,
            ), range(8)))
        self.assertEqual({key for _, key in results}, {self.ticket_key})
        self.assertEqual(len([key for _, key in self.storage.client.objects if key.startswith(PREFIX)]), 1)

    def test_real_consumer_restart_repairs_ack_to_ticket_gap(self):
        from scripts.block8_apply_dashboard_review import run
        with patch("scripts.block8_apply_dashboard_review.R2Storage.from_env", return_value=self.storage):
            self.assertEqual(run(self.job.job_id), "ACKNOWLEDGED")
            self.assertEqual(run(self.job.job_id), "ALREADY_ACKNOWLEDGED")
        self.assertFalse(self.ticket()["render_approved"])

    def test_human_whitespace_not_interpreted_as_extra_instruction(self):
        self.review["text"] = "  Please update the opening  "
        self.write_state()
        self.ack()
        status, _ = derive_canonical_edit_request(
            self.job.job_id, storage=self.storage, repository=self.repo,
        )
        self.assertEqual(status, "QUEUED_AWAITING_CREATIVE_PLAN")
        self.assertEqual(self.ticket()["human_request"], "Please update the opening")


if __name__ == "__main__":
    unittest.main()
