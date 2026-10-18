"""B72C ownership boundary tests."""
from io import BytesIO
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.openmontage_owner_album_handoff import stage_owner_album


class FakeR2:
    def __init__(self, objects):
        self.objects = objects
        self.keys = []

    def get_object(self, *, Bucket, Key):
        self.keys.append(Key)
        return {"Body": BytesIO(self.objects[Key])}


class OwnerAlbumHandoffTests(unittest.TestCase):
    def setUp(self):
        self.job = "tgalbum" + "a" * 32
        self.prefix = "private/v1/2026/10/18/" + self.job + "/"
        self.payload = b"sample"
        self.asset = "file00000001"
        self.objects = {
            "private/v1/telegram-album-index/" + self.job:
                json.dumps({"job_id": self.job, "lane": "private",
                            "owner_hash": hashlib.sha256(b"123").hexdigest(),
                            "created_at": "2026-10-18T18:00:00+00:00"}).encode(),
            self.prefix + "manifest.json":
                json.dumps({"schema": "MEDIA-JOB-MANIFEST-V1",
                            "job_id": self.job, "lane": "private",
                            "prefix": self.prefix,
                            "assets": [{"asset_id": self.asset, "mime": "image/png",
                                        "key": self.prefix + "originals/" + self.asset + "/a.png",
                                        "size": len(self.payload),
                                        "sha256": hashlib.sha256(self.payload).hexdigest()}]}).encode(),
            self.prefix + "originals/" + self.asset + "/a.png": self.payload,
        }
        self.selections = [{"scene_number": 1, "asset_id": self.asset,
                            "media_license": "owned_content", "rights_verified": True}]

    def stage(self, client, dest, owner="123"):
        return stage_owner_album(client, "bucket", job_id=self.job,
                                 owner_chat=owner, authorized_chat="123",
                                 selections=self.selections, destination=dest)

    def test_authorized_album(self):
        with TemporaryDirectory() as tmp:
            client = FakeR2(self.objects)
            result = self.stage(client, Path(tmp) / "stage")
            self.assertEqual(result["scenes"][0]["local_path"], "scene_001.png")

    def test_wrong_owner_rejected_before_storage(self):
        with TemporaryDirectory() as tmp:
            client = FakeR2(self.objects)
            with self.assertRaises(PermissionError):
                self.stage(client, Path(tmp) / "stage", owner="456")
            self.assertEqual(client.keys, [])

    def test_index_owner_mismatch_rejected(self):
        with TemporaryDirectory() as tmp:
            client = FakeR2(self.objects)
            self.objects["private/v1/telegram-album-index/" + self.job] = b'{"job_id":"bad"}'
            with self.assertRaises(PermissionError):
                self.stage(client, Path(tmp) / "stage")
            self.assertEqual(len(client.keys), 1)


if __name__ == "__main__":
    unittest.main()
