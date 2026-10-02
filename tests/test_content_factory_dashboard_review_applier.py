"""Negative, positive and restart tests for durable dashboard review application."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from content_factory_core import JobStatus, MediaRef
from content_factory_repository import SQLiteJobRepository
from content_factory_dashboard_review_applier import apply_review_request, ReviewApplyError


class FakeClient:
    def __init__(self):
        self.records={}
    def get_object(self, *, Bucket, Key):
        return {"Body": io.BytesIO(json.dumps(self.records[(Bucket,Key)]).encode())}


class FakeStorage:
    bucket="private-unit"
    def __init__(self):
        self.client=FakeClient()


class DurableReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"factory.sqlite"
        self.repo=SQLiteJobRepository(self.path)
        initial,_=self.repo.create_job("legitimate private preview",idempotency_key=str(uuid4()))
        job=initial.job
        self.ref=MediaRef(media_id=str(uuid4()),
            uri=f"r2://private-unit/media/{uuid4()}/test.mp4",
            sha256="a"*64,size_bytes=128,mime_type="video/mp4",provenance="ffmpeg:render:r1")
        job.media=[self.ref]
        job.publish_payload={"caption":"A privately verified test caption","creative_revision":1}
        job.status=JobStatus.READY_FOR_HUMAN
        self.stored=self.repo.save_job(job,expected_store_version=initial.store_version)
        self.job_id=job.job_id
        self.manifest=job.approval_manifest()
        self.preview_id=str(uuid4())
        self.request_id=str(uuid4())
        self.storage=FakeStorage()
        key=self.ref.uri[len("r2://private-unit/"):]
        self.preview={
            "schema":"FACTORY-MEDIA-PREVIEW-V1","preview_id":self.preview_id,
            "job_id":self.job_id,"revision":1,"manifest":self.manifest,
            "state":"READY_FOR_HUMAN","qm_passed":True,
            "caption":job.publish_payload["caption"],
            "media":{"media_id":self.ref.media_id,"key":key,"sha256":self.ref.sha256,
                     "size_bytes":128,"mime_type":"video/mp4"}}
        self.review={"schema":"FACTORY-REVIEW-INTENT-V1","request_id":self.request_id,
           "preview_id":self.preview_id,"job_id":self.job_id,"revision":1,
           "manifest":self.manifest,"actor":"authenticated_dashboard_owner",
           "status":"PENDING_FACTORY_APPLICATION","action":"change",
           "text":"Please alter the title"}
        self.state={"schema":"FACTORY-PREVIEW-STATE-V1","job_id":self.job_id,
                    "revision":1,"manifest":self.manifest,"preview_id":None,
                    "state":"REVIEW_REQUESTED","review":self.review}
        self._write()

    def _write(self):
        self.storage.client.records[(self.storage.bucket,
            "ai-central/v1/preview-state/"+self.job_id+".json")]=self.state
        self.storage.client.records[(self.storage.bucket,
            "ai-central/v1/previews/"+self.preview_id+".json")]=self.preview

    def apply(self):
        return apply_review_request(self.job_id,storage=self.storage,repository=self.repo)

    def test_change_saves_new_revision_once_and_survives_restart(self):
        first=self.apply()
        self.assertEqual(first.result,"APPLIED_TO_PERSISTENT_FACTORY_PENDING_R2_ACK")
        persisted=SQLiteJobRepository(self.path).get_job(self.job_id).job
        self.assertEqual(persisted.status,JobStatus.CHANGES_REQUESTED)
        self.assertEqual(persisted.revision,2)
        self.assertEqual(persisted.metadata["human_change:r1"],"Please alter the title")
        repeat=self.apply()
        self.assertEqual(repeat.result,"ALREADY_APPLIED")
        self.assertEqual(repeat.store_version,first.store_version)

    def test_discard_only_rejects_job_and_never_queues_publisher(self):
        self.review.update(action="discard",text="")
        first=self.apply()
        self.assertEqual(first.decision,"discard")
        job=self.repo.get_job(self.job_id).job
        self.assertEqual(job.status,JobStatus.REJECTED)
        self.assertIsNone(job.publish_handoff_key)
        self.assertEqual(self.apply().result,"ALREADY_APPLIED")

    def test_post_is_never_an_accepted_review_intent(self):
        self.review.update(action="post",text="")
        with self.assertRaises(ReviewApplyError):
            self.apply()
        self.assertEqual(self.repo.get_job(self.job_id).job.status,JobStatus.READY_FOR_HUMAN)

    def test_stale_revision_and_tampered_media_are_blocked(self):
        self.state["revision"]=2
        with self.assertRaises(ReviewApplyError):
            self.apply()
        self.state["revision"]=1
        self.preview["media"]["sha256"]="b"*64
        with self.assertRaises(ReviewApplyError):
            self.apply()
        self.assertEqual(self.repo.get_job(self.job_id).job.revision,1)

    def test_fake_request_actor_or_mismatched_manifest_is_blocked(self):
        self.review["actor"]="unknown"
        with self.assertRaises(ReviewApplyError):
            self.apply()
        self.review["actor"]="authenticated_dashboard_owner"
        self.preview["manifest"]="b"*64
        with self.assertRaises(ReviewApplyError):
            self.apply()
        self.assertEqual(self.repo.get_job(self.job_id).job.status,JobStatus.READY_FOR_HUMAN)

    def test_altered_payload_replay_after_apply_fails_closed(self):
        self.apply()
        self.review["text"]="Different change after approval"
        with self.assertRaises(ReviewApplyError):
            self.apply()

    def test_store_corruption_is_not_an_authorized_request(self):
        self.state["state"]="READY_FOR_HUMAN"
        with self.assertRaises(ReviewApplyError):
            self.apply()
        self.assertEqual(self.repo.get_job(self.job_id).job.revision,1)


if __name__=="__main__":
    unittest.main()
