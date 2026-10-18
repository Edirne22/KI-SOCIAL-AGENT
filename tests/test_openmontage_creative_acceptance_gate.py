"""Regression: a synthetic video must not pass the real-media creative gate."""
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.openmontage_render_verified import render_verified_research


class CreativeGateTests(unittest.TestCase):
    @patch("scripts.openmontage_render_verified.produce_video")
    @patch("scripts.openmontage_render_verified.build_media_manifest")
    @patch("scripts.openmontage_render_verified.build_storyboard")
    @patch("scripts.openmontage_render_verified.verify_research_payload")
    def test_synthetic_video_is_not_creatively_accepted(self, verify, storyboard, manifest, produce):
        verify.return_value = {"verified_item_count": 1, "stories": [{"title": "Quickshifter"}]}
        storyboard.return_value = {"scenes": [{"title": "Quickshifter"}]}
        manifest.return_value = {"all_rights_verified": True}
        produce.return_value = {"status": "COMPLETED", "source_media_included": False,
                                "subtitles_and_audio": {"spoken_voice_present": False}}
        result = render_verified_research({"stories": []}, Path("unused"))
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["creative_acceptance"], "BLOCKED_NO_REAL_MEDIA")
        self.assertIn("MEDIA_RESEARCH_INCOMPLETE", result["creative_issues"])


if __name__ == "__main__":
    unittest.main()
