"""B81: owner selection CLI fails before R2 when configuration is missing."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.openmontage_album_selection_cli import main


class CliTests(unittest.TestCase):
    def test_owner_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "selections.json"
            p.write_text("[]")
            with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": ""}), patch(
                    "sys.argv", ["cli", "--request-id", "tg-42",
                                 "--album-job-id", "tgalbum" + "a" * 32,
                                 "--selections", str(p)]):
                with self.assertRaises(PermissionError):
                    main()

    def test_valid_explicit_selection_passed_to_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "selections.json"
            selection = [{"scene_number": 1, "asset_id": "file00000001",
                          "media_license": "owned_content", "rights_verified": True}]
            p.write_text(json.dumps(selection))
            with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "123"}), patch(
                    "sys.argv", ["cli", "--request-id", "tg-42",
                                 "--album-job-id", "tgalbum" + "a" * 32,
                                 "--selections", str(p)]), patch(
                    "scripts.openmontage_album_selection_cli.client_from_env",
                    return_value=(object(), "bucket")), patch(
                    "scripts.openmontage_album_selection_cli.store_album_selection",
                    return_value={"selected_scenes": 1}) as writer:
                main()
                self.assertEqual(writer.call_args.kwargs["selections"], selection)


if __name__ == "__main__":
    unittest.main()
