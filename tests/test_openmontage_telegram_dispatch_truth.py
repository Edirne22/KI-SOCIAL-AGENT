import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.openmontage_control import handle


class TelegramDispatchTruthTests(unittest.TestCase):
    def test_unsupported_render_and_plan_are_not_queued(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "jobs.json"
            for command in ("/montage erstellen MotoGP", "/montage planen WSBK"):
                with patch("scripts.openmontage_control.requests.post") as post:
                    message = handle(command, 12, "owner", "owner", jobs_state=ledger)
                    self.assertIn("NICHT AUSFÜHRBAR", message)
                    self.assertIn("Kein Job", message)
                    post.assert_not_called()
                self.assertFalse(ledger.exists())

    def test_unauthorized_chat_remains_blocked(self):
        with self.assertRaises(PermissionError):
            handle("/montage erstellen MotoGP", 12, "stranger", "owner")


if __name__ == "__main__":
    unittest.main()
