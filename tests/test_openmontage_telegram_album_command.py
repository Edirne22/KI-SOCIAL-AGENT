"""B79: Telegram album command is opt-in and dispatches correct job identity."""
import json
import os
import unittest
from unittest.mock import patch

from scripts.openmontage_control import handle, parse_command


ALBUM = "tgalbum" + "a" * 32


class Response:
    status_code = 204


class AlbumCommandTests(unittest.TestCase):
    def test_parse_explicit_album(self):
        action = parse_command(f"/montage album {ALBUM} Familienfilm")
        self.assertEqual(action, {"action": "erstellen", "prompt": "Familienfilm",
                                  "album_job_id": ALBUM})

    def test_invalid_album_rejected(self):
        self.assertEqual(parse_command("/montage album ../bad Film"), "invalid")

    def test_dispatch_album_input(self):
        calls = []
        def store(*args, **kwargs):
            calls.append(kwargs)
        def post(url, **kwargs):
            calls.append(kwargs["json"])
            return Response()
        with patch.dict(os.environ, {"GITHUB_TOKEN": "unit-test"}), patch(
                "integrations.openmontage.private_request_store.put_request",
                side_effect=store):
            reply = handle(f"/montage album {ALBUM} Familienfilm", 15, "123", "123",
                           request_storage=object(), post=post)
        self.assertIn("angenommen", reply)
        self.assertEqual(calls[1]["inputs"]["album_job_id"], ALBUM)
        self.assertEqual(calls[1]["inputs"]["request_id"], "tg-15")

    def test_foreign_owner_rejected(self):
        with self.assertRaises(PermissionError):
            handle(f"/montage album {ALBUM} Familienfilm", 15, "456", "123")


if __name__ == "__main__":
    unittest.main()
