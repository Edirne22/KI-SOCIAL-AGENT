import unittest
from openmontage_storyboard import build_storyboard
from openmontage_media_sourcing import build_media_manifest

class MediaContractTests(unittest.TestCase):
    def test_authorized_asset_metadata_survives_storyboard_to_manifest(self):
        story = {"title": "Quickshifter erklärt", "summary": "Technische Details",
                 "media_url": "https://example.org/owned.mp4",
                 "media_source": "Eigene Aufnahmen",
                 "media_license": "owned_content",
                 "visual_target": "Schalthebel",
                 "visual_anchor": {"x": 0.25, "y": 0.8}}
        board = build_storyboard({"stories": [story]}, target_duration=35,
                                 film_type="product_explainer")
        first = board["scenes"][0]
        self.assertEqual(first["media_request"], "technical_detail_clip")
        self.assertEqual(first["visual_target"], "Schalthebel")
        self.assertEqual(first["visual_anchor"]["x"], 0.25)
        manifest = build_media_manifest(board)
        self.assertTrue(manifest["all_rights_verified"])
        self.assertEqual(manifest["manifest"][0]["media_url"], story["media_url"])

    def test_unlicensed_media_remains_blocked(self):
        board = build_storyboard({"stories": [{
            "title": "Technik", "media_url": "https://example.org/unknown.mp4"
        }]}, target_duration=30, film_type="product_explainer")
        manifest = build_media_manifest(board)
        self.assertFalse(manifest["all_rights_verified"])
