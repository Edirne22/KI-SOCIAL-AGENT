"""B82: contract test between immutable selection writer and production loader."""
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.openmontage_store_album_selection import store_album_selection
from scripts.openmontage_load_album_selection import main as load_selection


JOB = "tgalbum" + "a" * 32
SCENES = [{"scene_number": 1, "asset_id": "file00000001",
           "media_license": "owned_content", "rights_verified": True}]


class R2:
    def __init__(self):
        self.objects = {
            "private/v1/telegram-album-index/" + JOB + ".json":
                json.dumps({"job_id": JOB, "lane": "private",
                            "owner_hash": sha256(b"123").hexdigest()}).encode()
        }
    def get_object(self, *, Key, **kwargs):
        return {"Body": BytesIO(self.objects[Key])}
    def put_object(self, *, Key, Body, **kwargs):
        self.objects[Key] = Body


class SelectionContractTests(unittest.TestCase):
    def test_writer_output_is_accepted_by_loader(self):
        storage = R2()
        store_album_selection(storage, "private", request_id="tg-42",
                              album_job_id=JOB, owner_chat="123",
                              authorized_chat="123", selections=SCENES)
        with tempfile.TemporaryDirectory() as temp, patch.dict(
                os.environ, {"REQUEST_ID": "tg-42", "ALBUM_JOB_ID": JOB,
                             "TELEGRAM_CHAT_ID": "123"}), patch(
                "scripts.openmontage_load_album_selection.from_environment",
                return_value=storage), patch(
                "scripts.openmontage_load_album_selection.get_request",
                return_value={"owner_chat_sha256": sha256(b"123").hexdigest()}), patch(
                "scripts.openmontage_load_album_selection.Path",
                wraps=Path):
            original = Path.cwd()
            os.chdir(temp)
            try:
                load_selection()
                data = json.loads(Path(
                    "integrations/openmontage/.runtime/album_selection.json").read_text())
                self.assertEqual(data["scenes"], SCENES)
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
