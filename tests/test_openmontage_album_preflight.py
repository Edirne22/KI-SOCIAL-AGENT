"""B84: read-only preflight denies missing rights and mismatched album."""
from hashlib import sha256
from io import BytesIO
import json
import unittest

from scripts.openmontage_album_preflight import preflight_album


JOB = "tgalbum" + "a" * 32


class R2:
    def __init__(self, approved=True):
        self.approved = approved
    def get_object(self, *, Key, **kwargs):
        if "telegram-album-index" in Key:
            value = {"job_id": JOB, "lane": "private",
                     "owner_hash": sha256(b"123").hexdigest()}
        else:
            value = {"request_id": "tg-42", "album_job_id": JOB,
                     "scenes": [{"scene_number": 1, "asset_id": "file00000001", "media_license": "owned_content", "rights_verified": self.approved}]}
        return {"Body": BytesIO(json.dumps(value).encode())}


class PreflightTests(unittest.TestCase):
    def test_ready(self):
        result = preflight_album(R2(), "private", request_id="tg-42",
                                 album_job_id=JOB, owner_chat="123",
                                 authorized_chat="123")
        self.assertEqual(result, {"ready": True, "scene_count": 1})

    def test_no_implicit_rights(self):
        with self.assertRaises(ValueError):
            preflight_album(R2(False), "private", request_id="tg-42",
                            album_job_id=JOB, owner_chat="123",
                            authorized_chat="123")

    def test_missing_media_license_rejected(self):
        class MissingLicense(R2):
            def get_object(self, *, Key, **kwargs):
                result = super().get_object(Key=Key, **kwargs)
                if "album-selections" in Key:
                    data = json.loads(result["Body"].read())
                    data["scenes"][0].pop("media_license")
                    return {"Body": BytesIO(json.dumps(data).encode())}
                return result
        with self.assertRaises(ValueError):
            preflight_album(MissingLicense(), "private", request_id="tg-42",
                            album_job_id=JOB, owner_chat="123",
                            authorized_chat="123")

    def test_owner_mismatch(self):
        with self.assertRaises(PermissionError):
            preflight_album(R2(), "private", request_id="tg-42",
                            album_job_id=JOB, owner_chat="456",
                            authorized_chat="123")


if __name__ == "__main__":
    unittest.main()
