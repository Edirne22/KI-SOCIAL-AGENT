import unittest
from scripts.openmontage_social_copy import build_social_copy

class SocialCaptionFormatting(unittest.TestCase):
    def test_real_line_breaks_and_whitespace(self):
        result = build_social_copy({"verified_item_count": 1, "stories": [{"title": "Quickshifter  erklärt", "summary": "Sensor   erkennt Schaltimpuls.", "content_type": "technical_explainer", "series": "Motorradtechnik"}]})
        caption = result["instagram"]["caption"]
        self.assertIn("\n", caption)
        self.assertNotIn("\\n", caption)
        self.assertIn("Sensor erkennt", caption)
        self.assertIn("Quickshifter erklärt", caption)
