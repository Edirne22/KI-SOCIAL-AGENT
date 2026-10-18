"""Regression: synthetic video is rejected before reaching the production renderer."""
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
        manifest.return_value = {"all_rights_verified": True, "manifest": [
            {"external_media_accepted": False, "media_url": ""}
        ]}
        with self.assertRaisesRegex(RuntimeError, "MEDIA_RESEARCH_INCOMPLETE"):
            render_verified_research({"stories": []}, Path("unused"))
        produce.assert_not_called()


if __name__ == "__main__":
    unittest.main()
