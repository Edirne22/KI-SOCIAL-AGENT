"""B76: explicit album selection contract is fail-closed."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.openmontage_load_album_selection import main


class Storage:
    def __init__(self, payload):
        self.payload = payload
    def get_object(self, *, Key):
        return {"Body": BytesIO(self.payload)}


class SelectionTests(unittest.TestCase):
    def test_selection_mismatch_blocks(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"REQUEST_ID": "tg-123",
                                         "TELEGRAM_CHAT_ID": "1",
                                         "ALBUM_JOB_ID": "tgalbum" + "a" * 32}), patch(
                    "scripts.openmontage_load_album_selection.from_environment",
                    return_value=Storage(json.dumps({
                        "request_id": "tg-123", "album_job_id": "wrong",
                        "scenes": [{"scene_number": 1}]}).encode())), patch(
                    "scripts.openmontage_load_album_selection.get_request",
                    return_value={"owner_chat_sha256": hashlib.sha256(b"1").hexdigest()}):
                with self.assertRaisesRegex(ValueError, "mismatched"):
                    main()

    def test_wrong_owner_blocks_before_selection_read(self):
        import os
        storage = Storage(b"{}")
        with patch.dict(os.environ, {"REQUEST_ID": "tg-123",
                                     "TELEGRAM_CHAT_ID": "1"}), patch(
                "scripts.openmontage_load_album_selection.from_environment",
                return_value=storage), patch(
                "scripts.openmontage_load_album_selection.get_request",
                return_value={"owner_chat_sha256": hashlib.sha256(b"2").hexdigest()}):
            with self.assertRaises(SystemExit):
                main()


if __name__ == "__main__":
    unittest.main()
