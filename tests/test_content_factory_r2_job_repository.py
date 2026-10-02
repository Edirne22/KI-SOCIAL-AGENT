"""Private R2 canonical job CAS + restart + attached review application tests."""
import io
import json
import threading
import unittest
from uuid import uuid4

from content_factory_core import ProductionJob, JobStatus, MediaRef
from content_factory_dashboard_review_applier import apply_review_request, ReviewApplyError
from content_factory_repository import ConcurrentUpdateError
from content_factory_r2_job_repository import R2JobRepository, AmbiguousJobWrite


class S3Error(Exception):
    def __init__(self, code):
        self.response={"Error":{"Code":code}}


class FakeS3:
    def __init__(self):
        self.objects={}
        self.n=0
        self.lock=threading.Lock()
        self.fail_after_commit=False
    def put_object(self, *, Bucket, Key, Body, ContentType, IfMatch=None, IfNoneMatch=None):
        assert ContentType=="application/json"
        with self.lock:
            old=self.objects.get((Bucket,Key))
            if IfNoneMatch=="*" and old is not None:
                raise S3Error("PreconditionFailed")
            if IfMatch is not None and (not old or old[0]!=IfMatch):
                raise S3Error("PreconditionFailed")
            self.n+=1
            self.objects[(Bucket,Key)]=(f'"etag-{self.n}"',bytes(Body))
        if self.fail_after_commit:
            raise ConnectionError("committed without client ACK")
    def get_object(self, *, Bucket, Key):
        with self.lock:
            found=self.objects.get((Bucket,Key))
        if found is None:
            raise S3Error("NoSuchKey")
        return {"ETag":found[0],"Body":io.BytesIO(found[1])}
    def seed(self,bucket,key,doc):
        self.put_object(Bucket=bucket,Key=key,
            Body=json.dumps(doc).encode(),ContentType="application/json",IfNoneMatch="*")


class Storage:
    bucket="private-factory-test"
    def __init__(self):self.client=FakeS3()


def ready_job():
    job=ProductionJob("independent fact checked technical preview")
    job.status=JobStatus.READY_FOR_HUMAN
    job.media=[MediaRef(str(uuid4()),f"r2://private-factory-test/media/{uuid4()}/test.mp4",
      "a"*64,123,"video/mp4","test",1)]
    job.publish_payload={"caption":"Private sample, NEVER publish","creative_revision":1}
    return job


class SharedR2CanonicalTests(unittest.TestCase):
    def setUp(self):
        self.storage=Storage()
        self.repo=R2JobRepository(self.storage)
        self.job=ready_job()
    def test_create_load_restart_and_cas(self):
        self.repo.register_job(self.job)
        first=R2JobRepository(self.storage).get_job(self.job.job_id)
        self.assertEqual(first.job.approval_manifest(),self.job.approval_manifest())
        changed=first.job
        changed.metadata["test"]="updated"
        saved=self.repo.save_job(changed,expected_store_version=1)
        self.assertEqual(saved.store_version,2)
        self.assertEqual(R2JobRepository(self.storage).get_job(self.job.job_id).job.metadata["test"],"updated")
        with self.assertRaises(ConcurrentUpdateError):
            self.repo.save_job(first.job,expected_store_version=1)
    def test_create_once_even_after_worker_restart(self):
        self.repo.register_job(self.job)
        with self.assertRaises(ConcurrentUpdateError):
            R2JobRepository(self.storage).register_job(self.job)
    def test_unknown_write_result_must_be_reconciled_not_blindly_retried(self):
        self.storage.client.fail_after_commit=True
        with self.assertRaises(AmbiguousJobWrite):
            self.repo.register_job(self.job)
        self.storage.client.fail_after_commit=False
        recovered=self.repo.get_job(self.job.job_id)
        self.assertEqual(recovered.store_version,1)
        with self.assertRaises(ConcurrentUpdateError):
            self.repo.register_job(self.job)
    def test_corrupted_or_cross_job_envelope_is_rejected(self):
        self.repo.register_job(self.job)
        key=self.repo._key(self.job.job_id)
        etag,_=self.storage.client.objects[(self.storage.bucket,key)]
        self.storage.client.objects[(self.storage.bucket,key)]=(etag,b'{"schema":"FAKE"}')
        with self.assertRaises(AmbiguousJobWrite):
            self.repo.get_job(self.job.job_id)
    def test_real_dashboard_intent_applies_against_shared_r2_job_once(self):
        self.repo.register_job(self.job)
        preview_id=str(uuid4());request_id=str(uuid4())
        manifest=self.job.approval_manifest()
        media=self.job.media[0]
        review={"schema":"FACTORY-REVIEW-INTENT-V1","request_id":request_id,
            "preview_id":preview_id,"job_id":self.job.job_id,"revision":1,
            "manifest":manifest,"actor":"authenticated_dashboard_owner",
            "status":"PENDING_FACTORY_APPLICATION","action":"change",
            "text":"Please change the opening sentence"}
        state={"schema":"FACTORY-PREVIEW-STATE-V1","job_id":self.job.job_id,
            "preview_id":None,"revision":1,"manifest":manifest,
            "state":"REVIEW_REQUESTED","review":review}
        preview={"schema":"FACTORY-MEDIA-PREVIEW-V1","preview_id":preview_id,
           "job_id":self.job.job_id,"revision":1,"manifest":manifest,"qm_passed":True,
           "state":"READY_FOR_HUMAN","caption":self.job.publish_payload["caption"],
           "media":{"media_id":media.media_id,"key":media.uri.removeprefix("r2://private-factory-test/"),
                    "size_bytes":123,"sha256":media.sha256,"mime_type":"video/mp4"}}
        self.storage.client.seed(self.storage.bucket,
            "ai-central/v1/preview-state/"+self.job.job_id+".json",state)
        self.storage.client.seed(self.storage.bucket,
            "ai-central/v1/previews/"+preview_id+".json",preview)
        result=apply_review_request(self.job.job_id,storage=self.storage,repository=self.repo)
        self.assertEqual(result.result,"APPLIED_TO_PERSISTENT_FACTORY_PENDING_R2_ACK")
        restarted=R2JobRepository(self.storage)
        self.assertEqual(restarted.get_job(self.job.job_id).job.revision,2)
        repeat=apply_review_request(self.job.job_id,storage=self.storage,repository=restarted)
        self.assertEqual(repeat.result,"ALREADY_APPLIED")
    def test_no_fake_post_through_canonical_shared_store(self):
        self.repo.register_job(self.job)
        self.assertEqual(self.repo.get_job(self.job.job_id).job.status,JobStatus.READY_FOR_HUMAN)
        self.assertIsNone(self.repo.get_job(self.job.job_id).job.publish_handoff_key)


if __name__=="__main__":
    unittest.main()
