"""Telegram private-preview tests: offline, no Telegram or R2 network calls."""
import unittest
from unittest.mock import Mock
from scripts.openmontage_telegram_preview import preview_message, send_owner_preview


class TelegramPrivatePreviewTests(unittest.TestCase):
    def setUp(self):
        self.preview = {
            "download_url": "https://private.example/video?signature=masked",
            "expires_seconds": 900,
            "media_id": "review-only-123",
        }

    def test_preview_is_review_only(self):
        text = preview_message(self.preview)
        self.assertIn("PRIVATE VORSCHAU", text)
        self.assertIn("15 Minuten", text)
        self.assertIn("keine Veröffentlichung", text)
        self.assertNotIn("/montage freigabe", text)

    def test_owner_chat_only_and_no_web_preview(self):
        response = Mock()
        response.json.return_value = {"ok": True}
        post = Mock(return_value=response)
        send_owner_preview(self.preview, token="dummy", chat_id="12345", post=post)
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["json"]["chat_id"], "12345")
        self.assertTrue(kwargs["json"]["disable_web_page_preview"])
        self.assertEqual(post.call_count, 1)

    def test_missing_chat_rejected_without_network(self):
        post = Mock()
        with self.assertRaises(ValueError):
            send_owner_preview(self.preview, token="dummy", chat_id="not-a-chat", post=post)
        post.assert_not_called()

    def test_non_https_rejected(self):
        self.preview["download_url"] = "http://not-secure"
        with self.assertRaises(ValueError):
            preview_message(self.preview)

    def test_telegram_failure_is_not_success(self):
        response = Mock()
        response.json.return_value = {"ok": False}
        post = Mock(return_value=response)
        with self.assertRaises(RuntimeError):
            send_owner_preview(self.preview, token="dummy", chat_id="12345", post=post)


if __name__ == "__main__":
    unittest.main()
