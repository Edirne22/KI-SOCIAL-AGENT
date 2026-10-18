import unittest
from scripts.openmontage_social_copy import build_social_copy
from integrations.openmontage.research_memory_playbook import LESSONS

class BuelentSocialVoiceTest(unittest.TestCase):
    def test_voice_and_avatar_policy(self):
        payload = {"verified_item_count": 1, "stories": [{"title": "Quickshifter", "summary": "Sensor erkennt Schaltimpuls.", "content_type": "technical_explainer", "series": "Motorradtechnik"}]}
        result = build_social_copy(payload)
        self.assertEqual(result["voice_profile"], "buelent_locker_flockig_chillig_v1")
        self.assertFalse(result["avatar_ready_future"])
        self.assertFalse(result["publication_authorized"])
        self.assertIn("😎", result["instagram"]["caption"])
        self.assertTrue(any("3D-Avatar" in lesson for lesson in LESSONS["creative_director"]))
