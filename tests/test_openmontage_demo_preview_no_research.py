import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import openmontage_publish_preview as p

class DemoPreviewWithoutResearchTest(unittest.TestCase):
    def test_demo_sends_no_fabricated_captions(self):
        with patch.dict("os.environ", {"OPENMONTAGE_VIDEO_PATH": "demo.mp4"}), patch.object(p, "validate_video"), patch.object(p, "R2Storage") as storage, patch.object(p, "upload_private_preview", return_value={"download_url": "https://example.com/v", "expires_seconds": 3600, "media_id": "demo"}), patch.object(p, "send_owner_preview") as send, patch.object(p, "Path", side_effect=lambda x: Path("demo.mp4") if str(x) == "demo.mp4" else Path("/not-a-real-file")):
            p.main()
            self.assertIsNone(send.call_args.kwargs["social_copy"])
