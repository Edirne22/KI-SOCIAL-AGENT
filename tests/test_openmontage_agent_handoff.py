"""Nervous-system dry-run at the pre-render boundary."""
import unittest
from scripts.openmontage_agent_handoff import inspect_handoff, require_handoff


class AgentHandoffTests(unittest.TestCase):
    def test_quickshifter_text_only_is_blocked(self):
        research = {"verified_item_count": 5, "stories": [{"title": "Quickshifter"}]}
        storyboard = {"scenes": [{"title": "Sensor", "speaker_text": "Der Sensor erkennt den Schaltwunsch."}]}
        manifest = {"manifest": [{"rights_verified": True, "external_media_accepted": False,
                                   "selected_asset_type": "animated_text_scene"}]}
        report = inspect_handoff(research, storyboard, manifest)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("MEDIA_RESEARCH_INCOMPLETE", report["issues"])
        with self.assertRaisesRegex(ValueError, "MEDIA_RESEARCH_INCOMPLETE"):
            require_handoff(research, storyboard, manifest)

    def test_complete_handoff_is_ready(self):
        research = {"verified_item_count": 1, "stories": [{"title": "Sensor"}]}
        storyboard = {"scenes": [{"title": "Sensor", "speaker_text": "Ein Sensor erkennt den Schaltwunsch."}]}
        manifest = {"manifest": [{"rights_verified": True, "external_media_accepted": True,
                                   "media_url": "https://example.org/owned.mp4"}]}
        self.assertEqual(require_handoff(research, storyboard, manifest)["status"], "HANDOFF_READY")

    def test_missing_script_is_blocked(self):
        research = {"verified_item_count": 1, "stories": [{"title": "Sensor"}]}
        storyboard = {"scenes": [{"title": "Sensor"}]}
        manifest = {"manifest": [{"rights_verified": True, "external_media_accepted": True,
                                   "media_url": "https://example.org/owned.mp4"}]}
        self.assertIn("CREATIVE_SCRIPT_INCOMPLETE", inspect_handoff(research, storyboard, manifest)["issues"])


if __name__ == "__main__":
    unittest.main()
