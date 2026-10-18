"""B80: owner identity and rights gates before any private R2 write."""
from hashlib import sha256
from io import BytesIO
import json
import unittest

from scripts.openmontage_store_album_selection import store_album_selection


JOB = "tgalbum" + "a" * 32
SELECTION = [{"scene_number": 1, "asset_id": "file00000001",
              "media_license": "owned_content", "rights_verified": True}]


class R2:
    def __init__(self):
        self.writes = []
    def get_object(self, *, Bucket, Key):
        index = {"job_id": JOB, "lane": "private",
                 "owner_hash": sha256(b"123").hexdigest()}
        return {"Body": BytesIO(json.dumps(index).encode())}
    def put_object(self, **kwargs):
        self.writes.append(kwargs)


class SelectionWriterTests(unittest.TestCase):
    def test_owner_selection_written_privately(self):
        r2 = R2()
        result = store_album_selection(r2, "bucket", request_id="tg-42",
                                       album_job_id=JOB, owner_chat="123",
                                       authorized_chat="123", selections=SELECTION)
        self.assertEqual(result["selected_scenes"], 1)
        self.assertEqual(r2.writes[0]["Key"], "openmontage/album-selections/tg-42.json")
        self.assertEqual(r2.writes[0]["IfNoneMatch"], "*")

    def test_foreign_owner_blocked_before_write(self):
        r2 = R2()
        with self.assertRaises(PermissionError):
            store_album_selection(r2, "bucket", request_id="tg-42",
                                  album_job_id=JOB, owner_chat="456",
                                  authorized_chat="123", selections=SELECTION)
        self.assertFalse(r2.writes)

    def test_rights_cannot_be_assumed(self):
        r2 = R2()
        with self.assertRaises(ValueError):
            store_album_selection(r2, "bucket", request_id="tg-42",
                                  album_job_id=JOB, owner_chat="123",
                                  authorized_chat="123",
                                  selections=[{**SELECTION[0], "rights_verified": False}])
        self.assertFalse(r2.writes)


if __name__ == "__main__":
    unittest.main()
