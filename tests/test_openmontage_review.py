import tempfile
import unittest
from pathlib import Path
from scripts.openmontage_review import record_review

MEDIA = "12345678-1234-1234-1234-123456789abc"


class ReviewTests(unittest.TestCase):
    def test_owner_can_approve_without_publishing(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "review.json"
            self.assertEqual(record_review(MEDIA, "approve", chat_id="42",
                authorized_chat_id="42", state_path=state), "recorded")
            self.assertIn('"approve"', state.read_text())
            self.assertEqual(record_review(MEDIA, "approve", chat_id="42",
                authorized_chat_id="42", state_path=state), "already-recorded")

    def test_unauthorized_chat_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                record_review(MEDIA, "approve", chat_id="99",
                    authorized_chat_id="42", state_path=Path(tmp) / "review.json")

    def test_conflicting_decision_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "review.json"
            record_review(MEDIA, "reject", chat_id="42",
                authorized_chat_id="42", state_path=state)
            with self.assertRaises(ValueError):
                record_review(MEDIA, "approve", chat_id="42",
                    authorized_chat_id="42", state_path=state)
