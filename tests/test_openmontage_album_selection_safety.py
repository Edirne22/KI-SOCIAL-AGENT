"""B88: private selection writer must not overwrite or accept implicit rights."""
from hashlib import sha256
from io import BytesIO
import json
import unittest

from scripts.openmontage_store_album_selection import store_album_selection

JOB = "tgalbum" + "b" * 32


class R2:
    def __init__(self):
        self.puts = []
    def get_object(self, *, Key, **kwargs):
        return {"Body": BytesIO(json.dumps({
            "job_id": JOB, "lane": "private",
            "owner_hash": sha256(b"123").hexdigest()}).encode())}
    def put_object(self, **kwargs):
        self.puts.append(kwargs)


class SafetyTests(unittest.TestCase):
    def test_duplicate_scene_number_rejected(self):
        r2 = R2()
        scenes = [{"scene_number": 1, "asset_id": "file00000001",
                   "media_license": "owned_content", "rights_verified": True},
                  {"scene_number": 1, "asset_id": "file00000002",
                   "media_license": "owned_content", "rights_verified": True}]
        with self.assertRaises(ValueError):
            store_album_selection(r2, "private", request_id="tg-1",
                                  album_job_id=JOB, owner_chat="123",
                                  authorized_chat="123", selections=scenes)
        self.assertFalse(r2.puts)

    def test_no_implicit_license(self):
        r2 = R2()
        with self.assertRaises(ValueError):
            store_album_selection(r2, "private", request_id="tg-1",
                                  album_job_id=JOB, owner_chat="123",
                                  authorized_chat="123",
                                  selections=[{"scene_number": 1,
                                               "asset_id": "file00000001",
                                               "rights_verified": True}])
        self.assertFalse(r2.puts)

    def test_owner_hash_mismatch(self):
        r2 = R2()
        r2.get_object = lambda **kwargs: {"Body": BytesIO(json.dumps({
            "job_id": JOB, "lane": "private", "owner_hash": sha256(b"999").hexdigest()
        }).encode())}
        with self.assertRaises(PermissionError):
            store_album_selection(r2, "private", request_id="tg-1",
                                  album_job_id=JOB, owner_chat="123",
                                  authorized_chat="123",
                                  selections=[{"scene_number": 1,
                                               "asset_id": "file00000001",
                                               "media_license": "owned_content",
                                               "rights_verified": True}])
        self.assertFalse(r2.puts)


if __name__ == "__main__":
    unittest.main()
