import unittest
from scripts.openmontage_telegram_preview import preview_message

class TelegramCaptionReviewTest(unittest.TestCase):
    def test_video_and_platform_captions(self):
        preview = {"download_url": "https://example.com/preview", "expires_seconds": 3600, "media_id": "m1"}
        captions = {"publication_authorized": False, "instagram": {"caption": "Locker 😎 #MotoGP"}, "facebook": {"caption": "Hallo Leute 🏍️"}}
        message = preview_message(preview, captions)
        self.assertIn("https://example.com/preview", message)
        self.assertIn("INSTAGRAM", message)
        self.assertIn("#MotoGP", message)
        self.assertIn("FACEBOOK", message)
        self.assertIn("Keine Veröffentlichung", message)
    def test_cannot_claim_publication_approved(self):
        with self.assertRaises(ValueError):
            preview_message({"download_url": "https://example.com/v", "expires_seconds": 3600, "media_id": "m"}, {"publication_authorized": True})
