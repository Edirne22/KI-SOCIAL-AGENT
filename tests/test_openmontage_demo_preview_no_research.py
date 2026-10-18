import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from scripts import openmontage_publish_preview as p

class DemoPreviewWithoutResearchTest(unittest.TestCase):
    def test_demo_sends_no_fabricated_captions(self):
        with TemporaryDirectory() as tmp:
            video = Path(tmp) / "demo.mp4"
            video.write_bytes(b"synthetic")
            with patch.dict("os.environ", {"OPENMONTAGE_VIDEO_PATH": str(video)}), \
                 patch.object(p, "validate_video"), \
                 patch.object(p, "R2Storage"), \
                 patch.object(p, "upload_private_preview", return_value={"download_url": "https://example.com/v", "expires_seconds": 3600, "media_id": "demo"}), \
                 patch.object(p, "send_owner_preview") as send:
                p.main()
                self.assertIsNone(send.call_args.kwargs["social_copy"])
