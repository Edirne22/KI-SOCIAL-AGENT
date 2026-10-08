import unittest
from unittest.mock import patch
from content_factory_private_video_orchestrator import (
    STAGES, preflight_private_machine_contract, PrivateProductionLead, PrivateCreativeDirector, PrivateMediaStoryAgent,
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
        self.assertGreaterEqual(plan.duration_seconds,120)
        self.assertLessEqual(plan.duration_seconds,plan.max_duration_seconds)
        self.assertEqual(plan.aspect_ratio,"9:16")
        self.assertEqual(plan.privacy,"private-only")
        self.assertEqual(plan.title,"Dünya – Level 12")
        self.assertEqual(plan.stages,STAGES)
        self.assertGreaterEqual(len(plan.overlays),3)
        self.assertGreaterEqual(len(plan.scene_plan),4)
        self.assertEqual(len(plan.asset_effects),len(assets))
        self.assertEqual(plan.creative_revision,"duenya-creative-v2")

    def test_verified_visual_analysis_drives_storyboard_order(self):
        spec=PrivateCreativeDirector().create(PrivateProductionLead().decompose("private-task","Dünya 12 Geburtstag"))
        assets=[
            {"mime":"image/jpeg","content_verified":True,"story_beat":"finale","asset_role":"portrait","analysis_source":"private-vision-v1"},
            {"mime":"video/mp4","content_verified":True,"story_beat":"action","asset_role":"trampoline","analysis_source":"private-vision-v1"},
            {"mime":"image/jpeg","content_verified":True,"story_beat":"intro","asset_role":"arrival","analysis_source":"private-vision-v1"},
        ]
        for asset in assets:
            asset["visual_evidence"]={"source":"private-frame-analysis-v1","frame_sha256":"a"*64,"observations":["Visible birthday activity"]}
        result=PrivateMediaStoryAgent().bind(spec,assets)
        self.assertEqual(result["asset_order"],(2,1,0))
        self.assertEqual(result["selection"],"verified-content-storyboard")
        self.assertEqual(len(result["asset_effects"]),3)

    def test_self_asserted_visual_labels_do_not_pass_preflight(self):
        from content_factory_private_video_orchestrator import verified_visual_evidence
        asset={"content_verified":True,"story_beat":"action","asset_role":"trampoline",
               "analysis_source":"private-vision-v1"}
        self.assertFalse(verified_visual_evidence(asset))
        asset["visual_evidence"]={"source":"private-frame-analysis-v1",
                                  "frame_sha256":"a"*64,"observations":["Visible trampoline jump"]}
        self.assertTrue(verified_visual_evidence(asset))

    def test_unverified_media_cannot_claim_visual_analysis(self):
        spec=PrivateCreativeDirector().create(PrivateProductionLead().decompose("private-task","Dünya 12 Geburtstag"))
        result=PrivateMediaStoryAgent().bind(spec,[{"mime":"image/jpeg","story_beat":"action"}])
        self.assertEqual(result["selection"],"unclassified-blocked")

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
                                        "expected_effects":effects,"applied_effects":effects,
                                        "applied_transitions":("soft_fade","quick_fade","long_fade"),
                                        "pacing_applied":True})
        self.assertTrue(qm["passed"])

    def test_preflight_blocks_current_slideshow_before_machine(self):
        assets=[{"mime":"image/jpeg"},{"mime":"video/mp4"}]
        tracks=[{"id":"x","title":"Ambient","category":"chill",
                 "path":"assets/musik/chill/hypnotic-ambient.mp3","license":"PD","source_page":"local"}]
        with patch("content_factory_private_video_orchestrator.load_library",return_value=tracks):
            plan=build_plan("f6f50c9f4c2690e4eb1fe978","Dünya 12 Geburtstag",assets)
        result=preflight_private_machine_contract(plan,assets)
        self.assertEqual(result["decision"],"NOT_READY_FOR_MEDIA")
        self.assertIn("ASSET_CONTENT_NOT_CLASSIFIED",result["issues"])
        self.assertIn("REAL_TRANSITION_ADAPTER_UNPROVEN",result["issues"])
        self.assertIn("QM_EXPECTED_ACTUAL_CONTRACT_MISSING",result["issues"])
        self.assertIn("ASSET_CONTENT_NOT_CLASSIFIED",result["issues"])

    def test_preflight_rejects_empty_or_unassigned_assets(self):
        from dataclasses import replace
        tracks=[{"id":"x","title":"Ambient","category":"chill",
                 "path":"assets/musik/chill/hypnotic-ambient.mp3","license":"PD","source_page":"local"}]
        with patch("content_factory_private_video_orchestrator.load_library",return_value=tracks):
            plan=build_plan("f6f50c9f4c2690e4eb1fe978","Dünya 12 Geburtstag",[{"mime":"image/jpeg"}])
        broken=replace(plan,asset_effects=())
        result=preflight_private_machine_contract(broken,[{"mime":"image/jpeg"}])
        self.assertIn("ASSET_ASSIGNMENT_INCOMPLETE",result["issues"])

    def test_runtime_preflight_is_before_ffmpeg_machine(self):
        from pathlib import Path
        service=Path("infra/private-asr/service.py").read_text(encoding="utf-8")
        start=service.index('plan=build_plan(task_id,prompt,assets)')
        gate=service.index('preflight_private_machine_contract(plan, assets)',start)
        machine=service.index('private_birthday.run(task_id=task_id',start)
        self.assertLess(start,gate)
        self.assertLess(gate,machine)
        self.assertIn('PRIVATE_CREATIVE_PREFLIGHT_NOT_READY',service[gate:machine])

    def test_private_chain_contains_no_publish_stage(self):
        self.assertNotIn("publish",STAGES)
        self.assertEqual(STAGES[-1],"private_preview")

if __name__=="__main__":
    unittest.main()
