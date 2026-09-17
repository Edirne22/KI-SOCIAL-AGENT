import unittest
import re
from datetime import datetime

import instagram_publish
import instagram_reels
import instagram_stories
import facebook_publish
import facebook_carousel
import instagram_carousel

class TestPublisherClaimRelease(unittest.TestCase):
    def setUp(self):
        self.sample_block = (
            "## Instagram\n"
            "Status: FREIGEGEBEN\n"
            "Publication-Claim: IN_BEARBEITUNG 12345-1\n"
            "Freigabe: Telegram MotoGP\n"
            "Medienstatus: QUELLE_PRÜFEN\n"
            "Text: Testtext\n"
            "Bild: test.jpg\n"
        )
        self.sample_full_content = f"# Header\n\n{self.sample_block}"

    def test_instagram_publish_mark_block(self):
        res = instagram_publish.mark_block(self.sample_full_content, self.sample_block, "999")
        self.assertIn("## Instagram [GEPOSTET ", res)
        self.assertIn("| ID: 999]", res)
        self.assertIn("Status: GEPOSTET", res)
        self.assertNotIn("Status: FREIGEGEBEN", res)
        self.assertNotIn("Publication-Claim:", res)
        self.assertIn("Freigabe: Telegram MotoGP", res)
        self.assertIn("Medienstatus: QUELLE_PRÜFEN", res)
        self.assertIn("Text: Testtext", res)

    def test_instagram_reels_mark_block(self):
        block = self.sample_block.replace("## Instagram", "## Instagram Reel")
        content = f"# Header\n\n{block}"
        res = instagram_reels.mark_block(content, block, "999")
        self.assertIn("## Instagram Reel [GEPOSTET ", res)
        self.assertIn("| ID: 999]", res)
        self.assertIn("Status: GEPOSTET", res)
        self.assertNotIn("Publication-Claim:", res)

    def test_instagram_stories_mark_block(self):
        block = self.sample_block.replace("## Instagram", "## Story")
        content = f"# Header\n\n{block}"
        res = instagram_stories.mark_block(content, block, "999")
        self.assertIn("## Story [GEPOSTET ", res)
        self.assertIn("| ID: 999]", res)
        self.assertIn("Status: GEPOSTET", res)
        self.assertNotIn("Publication-Claim:", res)

    def test_facebook_publish_mark_block(self):
        block = self.sample_block.replace("## Instagram", "## Facebook")
        content = f"# Header\n\n{block}"
        res = facebook_publish.mark_block(content, block, "999")
        self.assertIn("## Facebook [GEPOSTET ", res)
        self.assertIn("| ID: 999]", res)
        self.assertIn("Status: GEPOSTET", res)
        self.assertNotIn("Publication-Claim:", res)

    def test_facebook_carousel_mark_block(self):
        block = self.sample_block.replace("## Instagram", "## Facebook Karussell")
        content = f"# Header\n\n{block}"
        res = facebook_carousel.mark_block(content, block, "999")
        self.assertIn("## Facebook Karussell [GEPOSTET ", res)
        self.assertIn("| ID: 999]", res)
        self.assertIn("Status: GEPOSTET", res)
        self.assertNotIn("Publication-Claim:", res)

    def test_instagram_carousel_mark_block(self):
        block = self.sample_block.replace("## Instagram", "## Instagram Karussell")
        content = f"# Header\n\n{block}"
        res = instagram_carousel.mark_block(content, block, "999")
        self.assertIn("## Instagram Karussell [GEPOSTET ", res)
        self.assertIn("| ID: 999]", res)
        self.assertIn("Status: GEPOSTET", res)
        self.assertNotIn("Publication-Claim:", res)

if __name__ == "__main__":
    unittest.main()
