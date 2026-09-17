"""Regression tests for Telegram receive deduplication logic."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import telegram_receive
import motogp_telegram_receive_v85


class TestTelegramDedup(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.published_file = Path(self.tmp_dir.name) / "content" / "PUBLISHED.md"
        self.published_file.parent.mkdir(parents=True, exist_ok=True)

        # Patch PUBLISHED_FILE in telegram_receive and PUBLISHED in motogp_telegram_receive_v85
        self.patcher1 = patch.object(telegram_receive, "PUBLISHED_FILE", self.published_file)
        self.patcher2 = patch.object(motogp_telegram_receive_v85, "PUBLISHED", self.published_file)
        self.patcher1.start()
        self.patcher2.start()

    def tearDown(self):
        self.patcher2.stop()
        self.patcher1.stop()
        self.tmp_dir.cleanup()

    def test_identical_text_rejected(self):
        """Case 1: Identical text in a second message is rejected as duplicate."""
        posts_1 = {
            1: {
                "title": "Titel 1",
                "platform": "Instagram",
                "full_text": "Inspirations-Quelle: https://example.com\n\nInstagram-Caption:\nDas ist ein eindeutiger Testtext für Dedup.",
            }
        }
        posts_2 = {
            1: {
                "title": "Titel 1 Duplicate",
                "platform": "Instagram",
                "full_text": "Inspirations-Quelle: https://example.com\n\nInstagram-Caption:\nDas ist ein eindeutiger Testtext für Dedup.",
            }
        }

        # First approval
        telegram_receive.append_approved_posts(posts_1, [1], update_id=1001)
        content_1 = self.published_file.read_text(encoding="utf-8")
        self.assertIn("Das ist ein eindeutiger Testtext für Dedup.", content_1)
        self.assertIn("Telegram-Update-ID: 1001", content_1)

        # Second approval with identical text but different update ID
        telegram_receive.append_approved_posts(posts_2, [1], update_id=1002)
        content_2 = self.published_file.read_text(encoding="utf-8")
        self.assertNotIn("Telegram-Update-ID: 1002", content_2)

    def test_case_and_whitespace_variation_rejected(self):
        """Case 2: Similar text with uppercase/lowercase or whitespace differences is rejected."""
        posts_1 = {
            1: {
                "title": "Titel 2",
                "platform": "Instagram",
                "full_text": "Instagram-Caption:\nSchluss mit geraden Bundesstraßen.\n\nLass dir  flüssige Kurven vorschlagen!",
            }
        }
        posts_2 = {
            1: {
                "title": "Titel 2 Similar",
                "platform": "Instagram",
                "full_text": "Instagram-Caption:\nSCHLUSS MIT GERADEN BUNDESSTRASSEN. Lass dir flüssige Kurven vorschlagen!",
            }
        }

        telegram_receive.append_approved_posts(posts_1, [1], update_id=2001)
        telegram_receive.append_approved_posts(posts_2, [1], update_id=2002)

        content = self.published_file.read_text(encoding="utf-8")
        self.assertIn("Telegram-Update-ID: 2001", content)
        self.assertNotIn("Telegram-Update-ID: 2002", content)

    def test_different_text_both_accepted(self):
        """Case 3: Different text in two messages -> both are written to PUBLISHED.md."""
        posts_1 = {
            1: {
                "title": "Titel 3A",
                "platform": "Instagram",
                "full_text": "Instagram-Caption:\nErster Beitrag Text.",
            }
        }
        posts_2 = {
            1: {
                "title": "Titel 3B",
                "platform": "Instagram",
                "full_text": "Instagram-Caption:\nZweiter Beitrag Text mit völlig anderem Inhalt.",
            }
        }

        telegram_receive.append_approved_posts(posts_1, [1], update_id=3001)
        telegram_receive.append_approved_posts(posts_2, [1], update_id=3002)

        content = self.published_file.read_text(encoding="utf-8")
        self.assertIn("Telegram-Update-ID: 3001", content)
        self.assertIn("Telegram-Update-ID: 3002", content)

    def test_different_hashtags_treated_as_different(self):
        """Case 4: Text with different hashtags is treated as different text (both accepted).

        Decision / Behavior: Deduplication normalizes all whitespace and casefold of the full caption
        (including hashtags). If the hashtags differ, the full text differs, so it is treated as
        a distinct post and added to PUBLISHED.md.
        """
        posts_1 = {
            1: {
                "title": "Titel 4A",
                "platform": "Instagram",
                "full_text": "Instagram-Caption:\nSpannendes Rennen am Sonntag! #MotoGP #Racing",
            }
        }
        posts_2 = {
            1: {
                "title": "Titel 4B",
                "platform": "Instagram",
                "full_text": "Instagram-Caption:\nSpannendes Rennen am Sonntag! #Moto2 #Motorsport",
            }
        }

        telegram_receive.append_approved_posts(posts_1, [1], update_id=4001)
        telegram_receive.append_approved_posts(posts_2, [1], update_id=4002)

        content = self.published_file.read_text(encoding="utf-8")
        self.assertIn("Telegram-Update-ID: 4001", content)
        self.assertIn("Telegram-Update-ID: 4002", content)

    def test_motogp_v85_dedup(self):
        """Test motogp_telegram_receive_v85 publish deduplication."""
        posts_1 = {
            1: {
                "title": "MotoGP Post",
                "source": "https://motogp.com",
                "image": "img.jpg",
                "text": "Toprak auf Pole Position in Spielberg!",
            }
        }
        posts_2 = {
            1: {
                "title": "MotoGP Post Duplicate",
                "source": "https://motogp.com",
                "image": "img.jpg",
                "text": "TOPRAK AUF POLE POSITION IN SPIELBERG!",
            }
        }

        count_1 = motogp_telegram_receive_v85.publish(posts_1, [1], uid=5001, batch="batch_1")
        self.assertEqual(count_1, 2)  # Instagram + Facebook

        count_2 = motogp_telegram_receive_v85.publish(posts_2, [1], uid=5002, batch="batch_2")
        self.assertEqual(count_2, 0)  # Duplicate skipped


if __name__ == "__main__":
    unittest.main()
