"""B90 tests: real media intake rejects unlicensed URLs before networking."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from scripts.openmontage_licensed_media_intake import download_licensed_scenes


class Tests(unittest.TestCase):
    def test_unlicensed_social_media_never_downloaded(self):
        with TemporaryDirectory() as temp:
            with patch("scripts.openmontage_licensed_media_intake.requests.get") as get:
                with self.assertRaisesRegex(ValueError, "rights"):
                    download_licensed_scenes([{"scene_number": 1,
                        "media_url": "https://www.youtube.com/clip.mp4",
                        "media_license": "none", "rights_verified": False,
                        "external_media_accepted": False}], Path(temp) / "assets")
                get.assert_not_called()

    def test_private_address_rejected(self):
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "unsafe"):
                download_licensed_scenes([{"scene_number": 1,
                    "media_url": "https://127.0.0.1/private.mp4",
                    "media_license": "cc0", "rights_verified": True,
                    "external_media_accepted": True}], Path(temp) / "assets")

    def test_scene_order_rejected(self):
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "order"):
                download_licensed_scenes([{"scene_number": 2}], Path(temp) / "assets")


if __name__ == "__main__":
    unittest.main()
