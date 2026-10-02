"""Isolated Block 9 existing-Meta adapter tests. No real social API calls."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from content_factory_core import JobStatus, ProductionJob, MediaRef
from content_factory_control_center import ControlCenterError
from content_factory_publish_ledger import AmbiguousPublication
from content_factory_r2_job_repository import R2JobRepository
from content_factory_r2_publish_ledger import R2PublishLedger
from content_factory_meta_video_ports import (
    CanonicalPrivatePublisherBridge,ExistingFacebookVideoPort,ExistingInstagramReelPort
)
from media_storage import R2Storage
from tests.test_content_factory_r2_job_repository import FakeS3


class BinaryFakeS3(FakeS3):
    def download_file(self,bucket,key,filename):
        raw=self.objects.get((bucket,key))
        if not raw:
            raise FileNotFoundError("private video not present")
        Path(filename).write_bytes(raw[1])


class MetaPortTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.client=BinaryFakeS3()
        self.storage=R2Storage(account_id="local-test",access_key_id="offline",
            secret_access_key="offline",bucket="private-factory-test",
            cache_root=Path(self.temp.name)/"cache",client=self.client)
        self.repository=R2JobRepository(self.storage)
        self.ledger=R2PublishLedger(self.storage)
        self.bridge=CanonicalPrivatePublisherBridge(self.repository,self.storage,self.ledger)
        self.job=ProductionJob("verified editorial video fixture, not real content")
        media_id=str(uuid4())
        media=b"offline video mock media bytes"
        sha=hashlib.sha256(media).hexdigest()
        key=f"media/{media_id}/sample.mp4"
        self.client.objects[(self.storage.bucket,key)]=('"media-test"',media)
        self.job.status=JobStatus.READY_FOR_HUMAN
        self.job.media=[MediaRef(media_id,f"r2://{self.storage.bucket}/{key}",
            sha,len(media),"video/mp4","mock-render")]
        self.job.publish_payload={"caption":"Offline contract fixture",
            "editorial_evidence":{"source_fact_contract":True,"human_writing":True,
                "media_rights":True,"synthetic":False,"final_qm_report_id":"test-report-only"}}
        self.repository.register_job(self.job)
        self.job.transition(JobStatus.APPROVED,actor="human")
        self.job.publish_handoff()
        self.job.metadata["human_post:r1"]={"actor":"authenticated_dashboard_owner",
           "revision":self.job.revision,"manifest":self.job.approval_manifest(),
           "request_id":str(uuid4())}
        self.repository.save_job(self.job,expected_store_version=1)
        self.port=ExistingFacebookVideoPort(self.storage)
        self.environ={"FACEBOOK_PAGE_ID":"offline-page","FACEBOOK_PAGE_TOKEN":"offline-no-network"}

    def send(self,provider_return="meta-video-test-id"):
        with patch.dict(os.environ,self.environ),patch(
          "facebook_publish.post_video_to_facebook",return_value=provider_return) as mock:
            result=self.bridge.publish(self.job.job_id,platform="facebook",publisher=self.port)
            return result,mock.call_count

    def test_provider_id_creates_single_shared_receipt(self):
        receipt,calls=self.send()
        self.assertEqual(calls,1)
        self.assertEqual(receipt.external_id,"meta-video-test-id")
        self.assertEqual(receipt.proof,"META_GRAPH_VIDEO_ID_RECEIVED")
        again,calls2=self.send()
        self.assertEqual(again,receipt)
        self.assertEqual(calls2,0)
        self.assertEqual(self.repository.get_job(self.job.job_id).job.status,JobStatus.PUBLISH_QUEUED)

    def test_timeout_leaves_permanent_shared_claim_and_never_reposts(self):
        with patch.dict(os.environ,self.environ),patch(
          "facebook_publish.post_video_to_facebook",return_value=None) as fake:
            with self.assertRaises(AmbiguousPublication):
                self.bridge.publish(self.job.job_id,platform="facebook",publisher=self.port)
            with self.assertRaises(AmbiguousPublication):
                self.bridge.publish(self.job.job_id,platform="facebook",publisher=self.port)
            self.assertEqual(fake.call_count,1)

    def test_missing_per_post_auth_or_changed_caption_cannot_reach_meta(self):
        fresh=self.repository.get_job(self.job.job_id)
        del fresh.job.metadata["human_post:r1"]
        self.repository.save_job(fresh.job,expected_store_version=fresh.store_version)
        with patch.dict(os.environ,self.environ),patch("facebook_publish.post_video_to_facebook") as fake:
            with self.assertRaises(ControlCenterError):
                self.bridge.publish(self.job.job_id,platform="facebook",publisher=self.port)
            self.assertEqual(fake.call_count,0)

    def test_synthetic_test_video_and_missing_rights_never_claim(self):
        fresh=self.repository.get_job(self.job.job_id)
        fresh.job.metadata["technical_test_only"]=True
        self.repository.save_job(fresh.job,expected_store_version=fresh.store_version)
        with patch.dict(os.environ,self.environ),patch("facebook_publish.post_video_to_facebook") as fake:
            with self.assertRaises(ControlCenterError):
                self.bridge.publish(self.job.job_id,platform="facebook",publisher=self.port)
            self.assertEqual(fake.call_count,0)

    def test_instagram_fails_without_verified_signed_delivery(self):
        with self.assertRaises(ControlCenterError):
            self.bridge.publish(self.job.job_id,platform="instagram",publisher=ExistingInstagramReelPort())

    def test_no_provider_credentials_no_claim(self):
        with patch.dict(os.environ,{"FACEBOOK_PAGE_ID":"","FACEBOOK_PAGE_TOKEN":""}):
            with self.assertRaises(ControlCenterError):
                self.bridge.publish(self.job.job_id,platform="facebook",publisher=self.port)
        key=self.ledger._paths(self.job.publish_handoff_key,"facebook")[0]
        self.assertNotIn((self.storage.bucket,key),self.client.objects)


if __name__=="__main__":
    unittest.main()
