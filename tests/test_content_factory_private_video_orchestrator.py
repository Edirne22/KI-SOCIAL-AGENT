import unittest
from unittest.mock import patch
from content_factory_private_video_orchestrator import (
    STAGES, PrivateProductionLead, PrivateCreativeDirector, PrivateMediaStoryAgent,
    PrivateMusicAudioAgent, PrivateQM, build_plan,
)

class PrivateVideoAgentChainTests(unittest.TestCase):
    def test_private_prompt_is_decomposed_into_full_agent_chain(self):
        prompt="PRIVATE VIDEOPRODUKTION: Dünya wird 12. 5 min, 9:16, emotional, Musik, Texte und Übergänge."
        assets=[{"mime":"image/jpeg"},{"mime":"video/mp4"}]
        tracks=[{"id":"x","title":"Ambient","category":"chill","path":"assets/musik/chill/hypnotic-ambient.mp3",
                 "license":"PD","source_page":"local"}]
        with patch("content_factory_private_video_orchestrator.load_library",return_value=tracks):
            plan=build_plan("f6f50c9f4c2690e4eb1fe978",prompt,assets)
        self.assertEqual(plan.duration_seconds,300)
        self.assertEqual(plan.aspect_ratio,"9:16")
        self.assertEqual(plan.privacy,"private-only")
        self.assertEqual(plan.title,"Dünya – Level 12")
        self.assertEqual(plan.stages,STAGES)
        self.assertGreaterEqual(len(plan.overlays),3)
        self.assertGreaterEqual(len(plan.scene_plan),4)
        self.assertEqual(len(plan.asset_effects),len(assets))
        self.assertGreaterEqual(len(set(plan.asset_effects)),2)
        self.assertEqual(plan.creative_revision,"duenya-creative-v2")

    def test_qm_fails_without_audio_or_real_render_evidence(self):
        qm=PrivateQM().checks(duration=300,has_audio=False,has_video=True,
                              creative={"privacy":"private-only","scene_count":6,
                                        "overlays_rendered":3,"creative_revision":"duenya-creative-v2",
                                        "expected_effects":("zoom_in","pan_left","zoom_out","pan_right"),
                                        "applied_effects":()})
        self.assertFalse(qm["passed"])
        self.assertFalse(qm["checks"]["audio"])
        self.assertFalse(qm["checks"]["creative_effect_variety"])
        self.assertFalse(qm["checks"]["creative_effects_executed"])

    def test_qm_passes_only_with_scene_and_effect_evidence(self):
        effects=("zoom_in","pan_left","zoom_out","pan_right")
        qm=PrivateQM().checks(duration=300,has_audio=True,has_video=True,
                              creative={"privacy":"private-only","scene_count":6,
                                        "overlays_rendered":3,"creative_revision":"duenya-creative-v2",
                                        "expected_effects":effects,"applied_effects":effects})
        self.assertTrue(qm["passed"])

    def test_private_chain_contains_no_publish_stage(self):
        self.assertNotIn("publish",STAGES)
        self.assertEqual(STAGES[-1],"private_preview")

if __name__=="__main__":
    unittest.main()
