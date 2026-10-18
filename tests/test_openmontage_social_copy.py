import unittest
from scripts.openmontage_social_copy import build_social_copy

class SocialCopyTest(unittest.TestCase):
    def test_quickshifter_caption(self):
        r = {"verified_item_count": 1, "stories": [{"title": "Quickshifter erklärt", "summary": "Der Sensor erkennt den Schaltimpuls.", "content_type": "technical_explainer", "series": "Motorradtechnik"}]}
        c = build_social_copy(r)
        self.assertIn("#Quickshifter", c["instagram"]["caption"])
        self.assertIn("Schaltimpuls", c["facebook"]["caption"])
        self.assertFalse(c["publication_authorized"])
    def test_unverified_fails(self):
        with self.assertRaises(ValueError):
            build_social_copy({"stories": [{"title": "Ergebnis"}], "verified_item_count": 0})
