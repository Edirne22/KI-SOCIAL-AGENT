"""Review ACK red-team: cross-store ordering, lost ACK and replay recovery."""
import unittest
from uuid import uuid4

from content_factory_dashboard_review_applier import apply_review_request
from content_factory_dashboard_review_ack import acknowledge_persisted_review, AmbiguousReviewAck
from content_factory_r2_job_repository import R2JobRepository
from tests.test_content_factory_r2_job_repository import Storage, ready_job


class ReviewAckTests(unittest.TestCase):
    def setUp(self):
        self.storage=Storage()
        self.repo=R2JobRepository(self.storage)
        self.job=ready_job()
        self.repo.register_job(self.job)
        self.preview_id=str(uuid4())
        self.request_id=str(uuid4())
        m=self.job.media[0]
        manifest=self.job.approval_manifest()
        review={"schema":"FACTORY-REVIEW-INTENT-V1","request_id":self.request_id,
            "preview_id":self.preview_id,"job_id":self.job.job_id,"revision":1,
            "manifest":manifest,"actor":"authenticated_dashboard_owner",
            "status":"PENDING_FACTORY_APPLICATION","action":"change",
            "text":"Please update the opening"}
        state={"schema":"FACTORY-PREVIEW-STATE-V1","job_id":self.job.job_id,
            "preview_id":None,"revision":1,"manifest":manifest,
            "state":"REVIEW_REQUESTED","review":review}
        preview={"schema":"FACTORY-MEDIA-PREVIEW-V1","preview_id":self.preview_id,
            "job_id":self.job.job_id,"revision":1,"manifest":manifest,
            "qm_passed":True,"state":"READY_FOR_HUMAN",
            "caption":self.job.publish_payload["caption"],
            "media":{"media_id":m.media_id,"key":m.uri.removeprefix("r2://private-factory-test/"),
                     "size_bytes":m.size_bytes,"sha256":m.sha256,"mime_type":m.mime_type}}
        self.key="ai-central/v1/preview-state/"+self.job.job_id+".json"
        self.storage.client.seed(self.storage.bucket,self.key,state)
        self.storage.client.seed(self.storage.bucket,
            "ai-central/v1/previews/"+self.preview_id+".json",preview)

    def read(self):
        import json
        return json.loads(self.storage.client.get_object(
            Bucket=self.storage.bucket,Key=self.key)["Body"].read())

    def ack(self):
        return acknowledge_persisted_review(self.job.job_id,storage=self.storage,repository=self.repo)

    def test_ack_only_after_real_persistent_job_update(self):
        with self.assertRaises(Exception):
            self.ack()
        self.assertEqual(self.read()["state"],"REVIEW_REQUESTED")
        apply_review_request(self.job.job_id,storage=self.storage,repository=self.repo)
        self.assertEqual(self.ack(),"ACKNOWLEDGED")
        self.assertEqual(self.read()["state"],"REVIEW_APPLIED")
        self.assertEqual(self.read()["review"]["status"],"APPLIED_TO_FACTORY")
        self.assertEqual(self.ack(),"ALREADY_ACKNOWLEDGED")

    def test_lost_ack_response_is_reconciled_not_reapplied(self):
        apply_review_request(self.job.job_id,storage=self.storage,repository=self.repo)
        self.storage.client.fail_after_commit=True
        with self.assertRaises(AmbiguousReviewAck):
            self.ack()
        self.storage.client.fail_after_commit=False
        self.assertEqual(self.ack(),"ALREADY_ACKNOWLEDGED")
        self.assertEqual(self.repo.get_job(self.job.job_id).job.revision,2)

    def test_unapplied_or_untrusted_state_must_never_be_accepted(self):
        self.assertEqual(self.read()["state"],"REVIEW_REQUESTED")
        self.storage.client.seed(self.storage.bucket,
            "ai-central/v1/preview-state/"+str(uuid4())+".json",{"schema":"FAKE"})
        with self.assertRaises(Exception):
            self.ack()


if __name__=="__main__":
    unittest.main()
