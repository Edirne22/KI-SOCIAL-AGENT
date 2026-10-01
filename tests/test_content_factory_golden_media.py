"""Real-byte, fail-closed Block 8 Golden Tablet tests (no R2 credentials)."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from content_factory_core import JobStatus, ProductionJob, MediaRef
from content_factory_golden_tablet import (
    FinalQM, QMCheck, GoldenTabletError, HumanDecisionService,
)
from content_factory_golden_media import present_verified_golden_tablet
from media_storage import LocalScratchStorage


class GoldenRealMedia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.storage = LocalScratchStorage(root / "private")
        asset = root / "clip.mp4"
        asset.write_bytes(b"private 15-second video stand-in")
        self.ref = self.storage.put_file(asset, provenance="test-reel", mime_type="video/mp4")
        self.job = ProductionJob("approved racing test")
        self.job.status = JobStatus.QM
        self.job.media = [self.ref]
        self.job.metadata["creative_package:r1"] = {"draft": {"caption": "Bülents freigegebene Vorschau"}}
        self.report = FinalQM().evaluate(self.job, [QMCheck("facts", True), QMCheck("render", True)])

    def preview(self, **kwargs):
        kwargs.setdefault("allowed_uri_prefixes", ("scratch://",))
        return present_verified_golden_tablet(
            self.job, self.report, storage=self.storage, **kwargs,
        )

    def test_verified_bytes_manifest_and_human_authority(self):
        result = self.preview()
        self.assertEqual(JobStatus.READY_FOR_HUMAN, self.job.status)
        self.assertEqual(self.ref.sha256, result.media[0].sha256)
        handoff = HumanDecisionService().post(self.job, result.tablet)
        self.assertEqual(JobStatus.PUBLISH_QUEUED, self.job.status)
        self.assertEqual(handoff, self.job.publish_handoff_key)

    def test_default_rejects_non_r2(self):
        with self.assertRaises(GoldenTabletError):
            present_verified_golden_tablet(self.job, self.report, storage=self.storage)
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_tampered_storage_bytes_rejected(self):
        self.storage.resolve_local(self.ref).write_bytes(b"malicious substitute")
        with self.assertRaises(GoldenTabletError):
            self.preview()
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_missing_storage_rejected(self):
        self.storage.resolve_local(self.ref).unlink()
        with self.assertRaises(GoldenTabletError):
            self.preview()
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_wrong_report_revision_rejected(self):
        self.job.revision += 1
        with self.assertRaises(GoldenTabletError):
            self.preview()
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_qm_failure_rejected(self):
        self.report = FinalQM().evaluate(self.job, [QMCheck("facts", False)])
        with self.assertRaises(GoldenTabletError):
            self.preview()
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_empty_media_rejected(self):
        self.job.media = []
        with self.assertRaises(GoldenTabletError):
            self.preview()

    def test_duplicate_media_ids_rejected(self):
        self.job.media.append(self.ref)
        with self.assertRaises(GoldenTabletError):
            self.preview()
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_unauthorized_uri_rejected(self):
        with self.assertRaises(GoldenTabletError):
            self.preview(allowed_uri_prefixes=("r2://",))

    def test_oversized_media_rejected(self):
        with self.assertRaises(GoldenTabletError):
            self.preview(max_media_bytes=1)
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_unsupported_content_type_rejected(self):
        ref = self.ref
        self.job.media = [MediaRef(ref.media_id, ref.uri, ref.sha256, ref.size_bytes, "text/plain", ref.provenance)]
        with self.assertRaises(GoldenTabletError):
            self.preview()
        self.assertEqual(JobStatus.QM, self.job.status)

    def test_changed_manifest_still_blocks_post(self):
        result = self.preview()
        self.job.publish_payload["caption"] = "tampered"
        with self.assertRaises(GoldenTabletError):
            HumanDecisionService().post(self.job, result.tablet)


if __name__ == "__main__":
    unittest.main()
