import unittest
from uuid import uuid4
from content_factory_telegram_change_feedback import PendingChange, prepare_change_text

class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.ctx = PendingChange("owner_chat", "owner", str(uuid4()), str(uuid4()), 2, "manifest", str(uuid4()))
        self.args = dict(chat_id="owner_chat", actor_id="owner", text="Bitte Ton entfernen",
                         current_job_id=self.ctx.job_id, current_preview_id=self.ctx.preview_id,
                         current_revision=2, current_manifest="manifest")
    def test_exact_feedback(self):
        result = prepare_change_text(self.ctx, **self.args)
        self.assertEqual(result["action"], "change")
        self.assertEqual(result["text"], "Bitte Ton entfernen")
        self.assertNotIn("publish", result)
    def test_foreign_actor(self):
        with self.assertRaises(PermissionError):
            prepare_change_text(self.ctx, **{**self.args, "actor_id": "intruder"})
    def test_old_revision(self):
        with self.assertRaises(ValueError):
            prepare_change_text(self.ctx, **{**self.args, "current_revision": 3})
    def test_wrong_preview(self):
        with self.assertRaises(ValueError):
            prepare_change_text(self.ctx, **{**self.args, "current_preview_id": str(uuid4())})
    def test_empty_and_oversize(self):
        for text in (" ", "x"*2001):
            with self.subTest(textlen=len(text)), self.assertRaises(ValueError):
                prepare_change_text(self.ctx, **{**self.args, "text": text})
    def test_credentials_blocked(self):
        with self.assertRaises(ValueError):
            prepare_change_text(self.ctx, **{**self.args, "text": "password=secret123"})
if __name__ == "__main__":
    unittest.main()
