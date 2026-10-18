import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.openmontage_render_verified import render_verified_research


class VerifiedRenderTests(unittest.TestCase):
    def test_empty_research_rejected_before_render(self):
        with patch("scripts.openmontage_render_verified.produce_video") as render:
            with self.assertRaisesRegex(ValueError, "No verified research"):
                render_verified_research({"stories": []}, Path("/tmp/no-render"))
            render.assert_not_called()

    def test_all_stages_are_called_in_order(self):
        verified = {"verified_item_count": 1, "stories": [{"title": "Test"}]}
        with patch("scripts.openmontage_render_verified.verify_research_payload",
                   return_value=verified) as facts, patch(
                   "scripts.openmontage_render_verified.build_storyboard",
                   return_value={"scenes": [{"title": "Test"}]}) as board, patch(
                   "scripts.openmontage_render_verified.build_media_manifest",
                   return_value={"all_rights_verified": True}) as media, patch(
                   "scripts.openmontage_render_verified.produce_video",
                   return_value={"status": "COMPLETED"}) as render:
            result = render_verified_research({"stories": [{"title": "Test"}]},
                                              Path("/tmp/mock"), duration=35)
        self.assertEqual(result["status"], "COMPLETED")
        facts.assert_called_once()
        board.assert_called_once()
        media.assert_called_once()
        render.assert_called_once()
        self.assertEqual(board.call_args.kwargs["target_duration"], 35)
