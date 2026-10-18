"""Focused B72B staging tests; no live Telegram or R2 calls."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.openmontage_private_media_stage import stage_private_scenes


class R2:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_object(self, **kwargs):
        from io import BytesIO
        self.calls.append(kwargs)
        return {"Body": BytesIO(self.payload)}


class PrivateMediaStageTests(unittest.TestCase):
    def setUp(self):
        self.payload = b"local-fixture"
        self.prefix = "private/v1/2026/10/18/tg000000001234/"
        self.asset = {"asset_id": "file00000001", "mime": "image/png",
                      "key": self.prefix + "originals/file00000001/a.png",
                      "size": len(self.payload),
                      "sha256": hashlib.sha256(self.payload).hexdigest()}
        self.manifest = {"schema": "MEDIA-JOB-MANIFEST-V1", "lane": "private",
                         "job_id": "tg000000001234", "prefix": self.prefix,
                         "assets": [self.asset]}
        self.selections = [{"scene_number": 1, "asset_id": "file00000001",
                            "media_license": "owned_content", "rights_verified": True}]

    def test_stages_selected_asset_with_hash(self):
        with TemporaryDirectory() as tmp:
            client = R2(self.payload)
            config = stage_private_scenes(client, "private-bucket", self.manifest,
                                          self.selections, Path(tmp) / "stage")
            self.assertEqual(config["scenes"][0]["local_path"], "scene_001.png")
            self.assertEqual((Path(tmp) / "stage/scene_001.png").read_bytes(), self.payload)
            self.assertEqual(client.calls[0]["Key"], self.asset["key"])

    def test_rejects_unapproved_media_without_download(self):
        with TemporaryDirectory() as tmp:
            client = R2(self.payload)
            self.selections[0]["rights_verified"] = False
            with self.assertRaisesRegex(ValueError, "approval"):
                stage_private_scenes(client, "bucket", self.manifest,
                                     self.selections, Path(tmp) / "stage")
            self.assertEqual(client.calls, [])

    def test_rejects_cross_lane_key(self):
        with TemporaryDirectory() as tmp:
            client = R2(self.payload)
            self.asset["key"] = "social/v1/2026/10/18/tg000000001234/originals/file00000001/a.png"
            with self.assertRaisesRegex(ValueError, "unsafe original"):
                stage_private_scenes(client, "bucket", self.manifest,
                                     self.selections, Path(tmp) / "stage")
            self.assertEqual(client.calls, [])

    def test_rejects_corrupted_bytes(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "size/hash mismatch"):
                stage_private_scenes(R2(b"wrong"), "bucket", self.manifest,
                                     self.selections, Path(tmp) / "stage")
            self.assertEqual(list((Path(tmp) / "stage").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
