"""Synthetic integration test: no real R2, Telegram or paid API calls."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import openmontage_publish_preview as preview


class PrivatePreviewE2ETests(unittest.TestCase):
    def test_quality_gate_before_private_upload_and_owner_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "demo.mp4"
            video.write_bytes(b"synthetic")
            order = []
            class Storage:
                @classmethod
                def from_env(cls, **kwargs):
                    order.append("storage")
                    return cls()
            def validate(path):
                self.assertEqual(path, video)
                order.append("quality")
            def upload(path, *, storage):
                self.assertEqual(path, video)
                order.append("upload")
                return {"media_id": "12345678-1234-1234-1234-123456789abc",
                        "download_url": "https://example.invalid/private",
                        "expires_seconds": 86400}
            def notify(result):
                self.assertEqual(result["expires_seconds"], 86400)
                order.append("owner")
            with patch.dict("os.environ", {"OPENMONTAGE_VIDEO_PATH": str(video)}), \
                 patch.object(preview, "validate_video", side_effect=validate), \
                 patch.object(preview, "R2Storage", Storage), \
                 patch.object(preview, "upload_private_preview", side_effect=upload), \
                 patch.object(preview, "send_owner_preview", side_effect=notify):
                preview.main()
            self.assertEqual(order, ["quality", "storage", "upload", "owner"])

    def test_failed_quality_gate_blocks_storage_and_telegram(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "demo.mp4"
            video.write_bytes(b"synthetic")
            with patch.dict("os.environ", {"OPENMONTAGE_VIDEO_PATH": str(video)}), \
                 patch.object(preview, "validate_video", side_effect=ValueError("bad")), \
                 patch.object(preview, "R2Storage") as storage, \
                 patch.object(preview, "send_owner_preview") as notify:
                with self.assertRaises(ValueError):
                    preview.main()
                storage.from_env.assert_not_called()
                notify.assert_not_called()
