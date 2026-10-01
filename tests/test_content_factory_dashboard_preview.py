"""Offline actual-byte index registration for private dashboard video."""
import json
import tempfile
import unittest
from pathlib import Path

from content_factory_core import ProductionJob, JobStatus
from content_factory_dashboard_preview import register_verified_video_preview, INDEX_PREFIX
from content_factory_golden_tablet import FinalQM, QMCheck
from media_storage import R2Storage


class InMemoryR2:
    def __init__(self):
        self.objects = {}
        self.index = {}
    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        self.objects[(bucket,key)] = Path(filename).read_bytes()
    def download_file(self, bucket, key, filename):
        Path(filename).write_bytes(self.objects[(bucket,key)])
    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.index[(Bucket, Key)] = json.loads(Body)
        return {"ETag": "synthetic-evidence-not-live"}


class DashboardPreviewRegistration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.client=InMemoryR2()
        self.storage=R2Storage(account_id="test",access_key_id="test",secret_access_key="test",
            bucket="private-unit-test",cache_root=root/"cache",client=self.client)
        mediafile=root/"clip.mp4"
        mediafile.write_bytes(b"private verified video sample")
        self.media=self.storage.put_file(mediafile,provenance="unit-test",mime_type="video/mp4")
        self.job=ProductionJob("video test")
        self.job.status=JobStatus.QM
        self.job.media=[self.media]
        self.job.metadata["creative_package:r1"]={"draft":{"caption":"private reel"}}
        self.report=FinalQM().evaluate(self.job,[QMCheck("facts",True),QMCheck("render",True)])
    def test_registers_bytes_verified_revisions_into_private_r2_index(self):
        preview=register_verified_video_preview(self.job,self.report,storage=self.storage)
        record=self.client.index[(self.storage.bucket,INDEX_PREFIX+preview+".json")]
        self.assertEqual(record["schema"],"FACTORY-MEDIA-PREVIEW-V1")
        self.assertEqual(record["media"]["sha256"],self.media.sha256)
        self.assertEqual(record["media"]["key"],"media/"+self.media.media_id+"/clip.mp4")
        self.assertEqual(record["manifest"],self.job.approval_manifest())
        self.assertEqual(JobStatus.READY_FOR_HUMAN,self.job.status)
    def test_corrupt_media_not_indexed(self):
        k=("private-unit-test","media/"+self.media.media_id+"/clip.mp4")
        self.client.objects[k]=b"corrupted"
        with self.assertRaises(Exception):
            register_verified_video_preview(self.job,self.report,storage=self.storage)
        self.assertFalse(self.client.index)
        self.assertEqual(JobStatus.QM,self.job.status)
    def test_failed_qm_not_indexed(self):
        report=FinalQM().evaluate(self.job,[QMCheck("facts",False)])
        with self.assertRaises(Exception):
            register_verified_video_preview(self.job,report,storage=self.storage)
        self.assertFalse(self.client.index)
    def test_unexpected_media_count_refused(self):
        self.job.media=[]
        with self.assertRaises(ValueError):
            register_verified_video_preview(self.job,self.report,storage=self.storage)
    def test_non_private_storage_refused(self):
        from media_storage import LocalScratchStorage
        with self.assertRaises(ValueError):
            register_verified_video_preview(self.job,self.report,storage=LocalScratchStorage(Path(self.temp.name)/"local"))


if __name__=="__main__":
    unittest.main()
