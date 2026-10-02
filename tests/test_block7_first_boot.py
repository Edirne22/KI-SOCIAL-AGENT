"""Offline security contracts; real model/voice startup runs separately on main."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
ASR=(ROOT/"scripts/block7_faster_whisper_startup.py").read_text(encoding="utf-8")
TTS=(ROOT/"scripts/block7_chatterbox_startup.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/block7-first-boot.yml").read_text(encoding="utf-8")


class BootGuardTests(unittest.TestCase):
    def test_both_startup_modules_syntax_valid_without_heavy_deps(self):
        ast.parse(ASR)
        ast.parse(TTS)

    def test_actual_asr_and_complete_generator_iteration_required(self):
        self.assertIn("from faster_whisper import WhisperModel",ASR)
        self.assertIn("compute_type=\"int8\"",ASR)
        self.assertIn("word_timestamps=True",ASR)
        self.assertIn("finished=list(segments)",ASR)
        self.assertIn('"de","Guten Tag',ASR)
        self.assertIn('"tr","Merhaba',ASR)
        self.assertIn("UNVERIFIED_SYNTHETIC_SPEAKER",ASR)

    def test_multilingual_not_english_turbo(self):
        self.assertIn("chatterbox.mtl_tts",TTS)
        self.assertIn("ChatterboxMultilingualTTS",TTS)
        self.assertIn('from_pretrained(device="cpu",t3_model="v3")',TTS)
        self.assertNotIn('from_pretrained(device="cpu")',TTS)
        self.assertNotIn("ChatterboxTurboTTS",TTS)
        self.assertIn("owner_voice_used\":False",TTS)
        self.assertIn("user_voice_acceptance\":\"NOT_RUN",TTS)

    def test_real_cpu_execution_is_bounded_and_private(self):
        self.assertIn("timeout-minutes: 13",WORKFLOW)
        self.assertIn("timeout-minutes: 14",WORKFLOW)
        self.assertIn("actual-asr-cpu:",WORKFLOW)
        self.assertIn("actual-chatterbox-install:",WORKFLOW)
        self.assertIn("HF_HUB_DISABLE_TELEMETRY",WORKFLOW)
        self.assertNotIn("R2_ACCESS_KEY",WORKFLOW)
        self.assertNotIn("GITHUB_TOKEN",WORKFLOW)
        self.assertNotIn("FACEBOOK_PAGE_TOKEN",WORKFLOW)
        self.assertNotIn("APIFY_API_TOKEN",WORKFLOW)

    def test_no_real_user_reference_or_autopublish(self):
        self.assertNotIn("Buelent.wav",ASR+TTS+WORKFLOW)
        self.assertNotIn("post_video_to_facebook",ASR+TTS+WORKFLOW)
        self.assertNotIn("publish_handoff()",ASR+TTS+WORKFLOW)


if __name__=="__main__":
    unittest.main()
