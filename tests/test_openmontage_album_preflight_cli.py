"""B85 owner preflight CLI wiring."""
import os
import unittest
from unittest.mock import patch
from scripts.openmontage_album_preflight_cli import main


class Tests(unittest.TestCase):
    def test_missing_owner_fails(self):
        with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": ""}), patch(
                "sys.argv", ["cli", "--request-id", "tg-1",
                             "--album-job-id", "tgalbum" + "a" * 32]):
            with self.assertRaises(PermissionError):
                main()

    def test_authorized_preflight(self):
        with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "123"}), patch(
                "sys.argv", ["cli", "--request-id", "tg-1",
                             "--album-job-id", "tgalbum" + "a" * 32]), patch(
                "scripts.openmontage_album_preflight_cli.client_from_env",
                return_value=(object(), "private")), patch(
                "scripts.openmontage_album_preflight_cli.preflight_album",
                return_value={"ready": True, "scene_count": 1}) as preflight:
            main()
            self.assertEqual(preflight.call_args.kwargs["owner_chat"], "123")


if __name__ == "__main__":
    unittest.main()
