import unittest
from unittest.mock import patch, MagicMock

import telegram_router as tr
import telegram_receive as trec
import motogp_telegram_receive_v85 as motogp_rec
import racing_run_controller as rc
import daily_digest as digest
import search_provider as search_provider


class TestTelegramBotBugs(unittest.TestCase):

    def test_bug1_slash_prefix_tolerance(self):
        # Router general command detection
        self.assertTrue(tr._is_general_command("/alle"))
        self.assertTrue(tr._is_general_command("/liste"))
        self.assertTrue(tr._is_general_command("/watchlist"))
        self.assertTrue(tr._is_general_command("/follow-analyse"))
        self.assertTrue(tr._is_general_command("/race"))
        self.assertTrue(tr._is_general_command("/inspiration"))
        self.assertTrue(tr._is_general_command("/viral"))
        self.assertTrue(tr._is_general_command("/go"))

        # telegram_receive parse_approval
        self.assertEqual(trec.parse_approval("/alle"), [1, 2, 3])
        self.assertEqual(trec.parse_approval("/1,3"), [1, 3])
        self.assertEqual(trec.parse_approval("alle", [1]), [1])
        self.assertEqual(trec.parse_approval("alle", [1, 2]), [1, 2])
        self.assertIsNone(trec.parse_approval("1,3", [1]))

        # telegram_receive _named_command
        self.assertEqual(trec._named_command("/track: Motorrad", ("track",)), "Motorrad")

        # motogp selection
        self.assertEqual(motogp_rec.selection("/motogp 1,2"), [1, 2])
        self.assertEqual(motogp_rec.selection("/motogp alle"), [1, 2, 3, 4, 5])

    def test_bug2_multiple_motogp_keywords(self):
        # Multiple motogp keywords in various casing and spacing
        self.assertEqual(motogp_rec.selection("motogp 1, motogp 2, motogp 4"), [1, 2, 4])
        self.assertEqual(motogp_rec.selection("motogp 1 motogp 2"), [1, 2])
        self.assertEqual(motogp_rec.selection("Motogp 1, MotoGP 2"), [1, 2])
        self.assertEqual(motogp_rec.selection("/motogp 1, /motogp 2"), [1, 2])

    def test_bug3_batch_status_freigegeben(self):
        # Check that run controller allows active_batch_id for FREIGEGEBEN
        rc.transition("batch-test", "FREIGEGEBEN")
        self.assertEqual(rc.get_run("batch-test")["status"], "FREIGEGEBEN")
        self.assertEqual(rc.active_batch_id(), "batch-test")

        # Clean up controller state
        rc.transition("batch-test", "CLOSED")


    def test_daily_digest_creates_only_non_racing_approval_choices(self):
        posts = [
            {"number": "1", "title": "Ride With Me", "hook": "h", "platform": "Instagram", "description": "d", "full_text": "x", "source": "https://example.com"}
        ]
        with patch.object(digest, "load_latest_posts", return_value=posts):
            message = digest.build_digest()
        self.assertIn("Allgemeine Content-Entwürfe zur Freigabe", message)
        self.assertIn("1. Ride With Me", message)
        self.assertIn("Racing-Content", message)
        self.assertNotIn("deal:", message)

    def test_price_offer_rejects_unrelated_euro_snippet(self):
        bad = {"title": "Kreis Unna PDF", "snippet": "Gebühr 1,00 € für eine Veranstaltung"}
        self.assertFalse(search_provider._offer_matches_query(bad, 1.0, "motorradhandschuhe max: 50 €"))
        good = {"title": "Alpinestars Motorradhandschuhe", "snippet": "Motorrad Handschuhe 49,99 €"}
        self.assertTrue(search_provider._offer_matches_query(good, 49.99, "motorradhandschuhe max: 50 €"))

    def test_price_offer_rejects_unrelated_calendar_price(self):
        bad = {"title": "Alpenverein München Veranstaltung", "snippet": "Teilnahme 5,00 €"}
        self.assertFalse(search_provider._offer_matches_query(bad, 5.0, "motorradhandschuhe max: 50 €"))

    unittest.main()
