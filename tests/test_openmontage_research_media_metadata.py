import unittest
from openmontage_research import build_research
from openmontage_storyboard import build_storyboard
from openmontage_media_sourcing import build_media_manifest

class ResearchMetadataContract(unittest.TestCase):
    def test_research_storyboard_manifest_retains_rights(self):
        research = build_research("Technik", mock_items=[{
            "title": "Technische Analyse", "url": "https://www.motogp.com/en/news/tech",
            "summary": "Technischer Aufbau", "content_type": "technical_explainer",
            "media_url": "https://example.org/owned.mp4",
            "media_license": "owned_content",
            "media_source": "Eigene Kamera",
            "visual_target": "Schalthebel",
        }])
        story = research["stories"][0]
        self.assertEqual(story["content_type"], "technical_explainer")
        board = build_storyboard(research, target_duration=20, film_type="product_explainer")
        self.assertEqual(board["scenes"][0]["visual_target"], "Schalthebel")
        manifest = build_media_manifest(board)
        self.assertEqual(manifest["manifest"][0]["media_url"], "https://example.org/owned.mp4")
        self.assertTrue(manifest["all_rights_verified"])

    def test_unclassified_story_stays_news(self):
        research = build_research("MotoGP", mock_items=[{
            "title": "MotoGP Ergebnis", "url": "https://www.motogp.com/en/news/result"
        }])
        self.assertEqual(research["stories"][0]["content_type"], "news")
