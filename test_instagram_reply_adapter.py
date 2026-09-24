import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import instagram_engagement as ie
import instagram_reply_adapter as adapter


class InstagramReplyAdapterTests(unittest.TestCase):
    def _response(self, status=200, payload=None, text=""):
        response = Mock()
        response.status_code = status
        response.text = text
        response.json.return_value = payload if payload is not None else {}
        return response

    @patch.dict(os.environ, {"INSTAGRAM_ACCESS_TOKEN": "test-token"}, clear=False)
    def test_success_200_and_engagement_sets_sent_reply_id_sent_at(self):
        response = self._response(200, {"id": "reply_123"})
        with patch.object(adapter.requests, "post", return_value=response) as post:
            self.assertEqual(adapter.send_reply("comment_1", "Danke!"), "reply_123")
            post.assert_called_once_with(
                f"{adapter.API}/comment_1/replies",
                data={"message": "Danke!", "access_token": "test-token"},
                timeout=45,
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(ie, "MEMORY_FILE", root/"m.md"), \
                 patch.object(ie, "QUEUE_FILE", root/"q.jsonl"), \
                 patch.object(ie, "SEEN_FILE", root/"s.txt"), \
                 patch.object(ie, "LOCK_DIR", root), \
                 patch.object(ie, "send_reply", return_value="reply_123"):
                event = ie.ingest({"event_id": "comment_1", "text": "Hi", "reply_draft": "Danke!"})
                self.assertIn("SENT", ie.telegram_command("antwort " + event["ticket_id"]))
                saved = ie._queue()[0]
                self.assertEqual(saved["status"], "SENT")
                self.assertEqual(saved["reply_id"], "reply_123")
                self.assertTrue(saved["sent_at"])

    @patch.dict(os.environ, {"INSTAGRAM_ACCESS_TOKEN": "test-token"}, clear=False)
    def test_http_400_raises(self):
        with patch.object(adapter.requests, "post", return_value=self._response(400, text="bad")):
            with self.assertRaises(RuntimeError):
                adapter.send_reply("comment_1", "Text")

    @patch.dict(os.environ, {"INSTAGRAM_ACCESS_TOKEN": "test-token"}, clear=False)
    def test_http_500_raises(self):
        with patch.object(adapter.requests, "post", return_value=self._response(500, text="server")):
            with self.assertRaises(RuntimeError):
                adapter.send_reply("comment_1", "Text")

    @patch.dict(os.environ, {"INSTAGRAM_ACCESS_TOKEN": "test-token"}, clear=False)
    def test_invalid_json_raises(self):
        response = self._response(200)
        response.json.side_effect = ValueError("invalid")
        with patch.object(adapter.requests, "post", return_value=response):
            with self.assertRaises(RuntimeError):
                adapter.send_reply("comment_1", "Text")

    @patch.dict(os.environ, {"INSTAGRAM_ACCESS_TOKEN": "test-token"}, clear=False)
    def test_missing_reply_id_raises(self):
        with patch.object(adapter.requests, "post", return_value=self._response(200, {})):
            with self.assertRaises(RuntimeError):
                adapter.send_reply("comment_1", "Text")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_token_fails_before_http(self):
        with patch.object(adapter.requests, "post") as post:
            with self.assertRaisesRegex(RuntimeError, "^INSTAGRAM_ACCESS_TOKEN nicht gesetzt$"):
                adapter.send_reply("comment_1", "Text")
            post.assert_not_called()

    @patch.dict(os.environ, {"INSTAGRAM_ACCESS_TOKEN": "test-token"}, clear=False)
    def test_empty_message_fails_before_http(self):
        with patch.object(adapter.requests, "post") as post:
            with self.assertRaisesRegex(RuntimeError, "^message ist leer$"):
                adapter.send_reply("comment_1", "   ")
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
