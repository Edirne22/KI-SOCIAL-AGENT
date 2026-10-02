"""Block 9 signed URL issuance/port tests: no real social or public fetch."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs
from uuid import uuid4

from content_factory_core import JobStatus, ProductionJob, MediaRef
from content_factory_control_center import ControlCenterError
from content_factory_publish_ledger import AmbiguousPublication
from content_factory_meta_video_ports import CanonicalPrivatePublisherBridge,ExistingInstagramReelPort
from content_factory_meta_private_delivery import issue_private_meta_delivery, PREFIX
from content_factory_r2_job_repository import R2JobRepository
from content_factory_r2_publish_ledger import R2PublishLedger
from media_storage import R2Storage
from tests.test_content_factory_meta_video_ports import BinaryFakeS3

ORIGIN="https://editorial-gateway.example.workers.dev"

class TestBlock9PrivateDelivery(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.client=BinaryFakeS3()
        self.storage=R2Storage(account_id="offline",access_key_id="offline",
            secret_access_key="offline",bucket="private-factory-test",
            cache_root=Path(self.tmp.name),client=self.client)
        self.repo=R2JobRepository(self.storage)
        self.ledger=R2PublishLedger(self.storage)
        self.bridge=CanonicalPrivatePublisherBridge(self.repo,self.storage,self.ledger)
        self.job=ProductionJob("real editorial candidate: test fixture not posted")
        binary=b"offline video mock media bytes"
        media_id=str(uuid4())
        media=MediaRef(media_id,f"r2://{self.storage.bucket}/media/{media_id}/sample.mp4",
            hashlib.sha256(binary).hexdigest(),len(binary),"video/mp4","verified-editorial")
        self.client.objects[(self.storage.bucket,f"media/{media_id}/sample.mp4")]=('"media"',binary)
        self.job.status=JobStatus.READY_FOR_HUMAN
        self.job.media=[media]
        self.job.publish_payload={"caption":"Verified example only",
          "editorial_evidence":{"source_fact_contract":True,"human_writing":True,
            "media_rights":True,"synthetic":False,"final_qm_report_id":"report-immutable"}}
        self.repo.register_job(self.job)
        self.job.transition(JobStatus.APPROVED,actor="human")
        self.job.publish_handoff()
        self.job.metadata["human_post:r1"]={"actor":"authenticated_dashboard_owner",
             "revision":1,"manifest":self.job.approval_manifest(),"request_id":str(uuid4())}
        self.repo.save_job(self.job,expected_store_version=1)
        self.creds={"INSTAGRAM_USER_ID":"offline","INSTAGRAM_ACCESS_TOKEN":"offline-token"}
    def grant(self,**kw):
        return issue_private_meta_delivery(self.repo,self.storage,self.job.job_id,
            gateway_origin=ORIGIN,**kw)
    def port(self,issuer=None):
        return ExistingInstagramReelPort(self.repo,self.storage,gateway_origin=ORIGIN,
           issue_delivery=issuer or issue_private_meta_delivery)

    def test_grant_requires_separate_opt_in_and_exact_canonical_approval(self):
        with self.assertRaises(ControlCenterError):self.grant()
        with self.assertRaises(ControlCenterError):self.grant(explicitly_approved=True,
            gateway_origin="http://evil.example")
        self.assertFalse(any(PREFIX in key for _,key in self.client.objects))
        updated=self.repo.get_job(self.job.job_id)
        updated.job.metadata["technical_test_only"]=True
        self.repo.save_job(updated.job,expected_store_version=updated.store_version)
        with self.assertRaises(ControlCenterError):self.grant(explicitly_approved=True)
        self.assertFalse(any(PREFIX in key for _,key in self.client.objects))

    def test_real_issued_capability_is_hashed_and_binds_exact_revision(self):
        url=self.grant(explicitly_approved=True)
        parsed=urlparse(url)
        self.assertEqual(parsed.scheme,"https")
        self.assertEqual(parsed.hostname,"editorial-gateway.example.workers.dev")
        self.assertEqual(parsed.path,"/api/meta-delivery")
        args=parse_qs(parsed.query)
        key=PREFIX+args["id"][0]+".json"
        saved=json.loads(self.client.objects[(self.storage.bucket,key)][1])
        self.assertNotIn(args["token"][0],json.dumps(saved))
        self.assertEqual(saved["token_sha256"],hashlib.sha256(args["token"][0].encode()).hexdigest())
        self.assertEqual(saved["handoff_key"],self.job.publish_handoff_key)
        self.assertEqual(saved["sha256"],self.job.media[0].sha256)
        self.assertLessEqual(0,(saved["expires_at"]>saved["issued_at"]))
        with self.assertRaises(ControlCenterError):
            self.grant(explicitly_approved=True,lifetime_seconds=7201)

    def test_no_secrets_or_media_means_no_issuance(self):
        with self.assertRaises(ControlCenterError):
            self.grant(explicitly_approved=True,gateway_origin="https://other.example")
        saved=self.repo.get_job(self.job.job_id)
        saved.job.metadata.pop("human_post:r1")
        self.repo.save_job(saved.job,expected_store_version=saved.store_version)
        with self.assertRaises(ControlCenterError):self.grant(explicitly_approved=True)

    def test_instagram_happy_path_single_post_and_immutable_shared_receipt(self):
        port=self.port()
        calls=[]
        def mock_post(url,**kw):
            calls.append(url)
            if url.endswith("/media"):return type("Response",(),{"status_code":200,"json":lambda self:{"id":"creation-id"}})()
            return type("Response",(),{"status_code":200,"json":lambda self:{"id":"posted-reel-id"}})()
        def mock_head(url,**kw):
            return type("Response",(),{"status_code":200,"headers":{
                "Content-Type":"video/mp4","Content-Length":str(self.job.media[0].size_bytes)}})()
        with patch.dict(os.environ,self.creds),patch("requests.head",side_effect=mock_head),patch(
                "requests.post",side_effect=mock_post),patch(
                "instagram_reels.wait_for_container",return_value=True):
            receipt=self.bridge.publish(self.job.job_id,platform="instagram",publisher=port)
            self.assertEqual(receipt.external_id,"posted-reel-id")
            self.assertEqual(receipt.proof,"META_GRAPH_REEL_ID_RECEIVED")
            cached=self.bridge.publish(self.job.job_id,platform="instagram",publisher=port)
        self.assertEqual(cached,receipt)
        self.assertEqual(len(calls),2)

    def test_timeout_after_ledger_claim_does_not_retry_create_or_publish(self):
        port=self.port()
        with patch.dict(os.environ,self.creds),patch("requests.head",side_effect=TimeoutError("offline timeout")):
            # TimeoutError is intentionally outside requests' exception hierarchy;
            # outer bridge still retains an ambiguous one-writer claim.
            with self.assertRaises(AmbiguousPublication):
                self.bridge.publish(self.job.job_id,platform="instagram",publisher=port)
            with self.assertRaises(AmbiguousPublication):
                self.bridge.publish(self.job.job_id,platform="instagram",publisher=port)

    def test_default_instagram_port_without_issuer_is_fail_closed_before_claim(self):
        with patch.dict(os.environ,self.creds):
            with self.assertRaises(ControlCenterError):
                self.bridge.publish(self.job.job_id,platform="instagram",
                                    publisher=ExistingInstagramReelPort())
        intent=self.ledger._paths(self.job.publish_handoff_key,"instagram")[0]
        self.assertNotIn((self.storage.bucket,intent),self.client.objects)

if __name__=="__main__": unittest.main()
