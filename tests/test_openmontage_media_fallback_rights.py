import unittest
from openmontage_media_sourcing import build_media_manifest, evaluate_media_item

class FallbackRightsTests(unittest.TestCase):
    def test_unlicensed_url_is_not_passed_to_renderer(self):
        item = evaluate_media_item(1, "technical_detail_clip",
                                   media_url="https://example.com/unlicensed.mp4")
        self.assertTrue(item["rights_verified"])
        self.assertFalse(item["external_media_accepted"])
        self.assertEqual(item["media_url"], "")
        self.assertEqual(item["rejected_media_url"], "https://example.com/unlicensed.mp4")
        self.assertEqual(item["license_status"], "unverified_third_party")

    def test_synthetic_fallback_does_not_block_entire_manifest(self):
        storyboard = {"scenes": [{"scene_number": 1, "media_request": "technical_detail_clip",
                                   "media_url": "https://example.com/unlicensed.mp4"}]}
        manifest = build_media_manifest(storyboard)
        self.assertTrue(manifest["all_rights_verified"])
        self.assertEqual(manifest["manifest"][0]["media_url"], "")

    def test_owned_media_keeps_original_url(self):
        item = evaluate_media_item(1, "technical_detail_clip",
                                   media_url="https://example.com/owned.mp4",
                                   media_license="owned_content")
        self.assertTrue(item["external_media_accepted"])
        self.assertEqual(item["media_url"], "https://example.com/owned.mp4")
