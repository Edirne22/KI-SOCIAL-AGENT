import unittest
from pathlib import Path
from unittest.mock import patch
from openmontage_production import produce_video

class RenderReportTests(unittest.TestCase):
    def test_unverified_media_is_rejected(self):
        with patch("openmontage_production.fc.verify_research_payload",
                   return_value={"verified_item_count": 1}):
            with self.assertRaisesRegex(ValueError, "Unverified media rights"):
                produce_video({}, {"scenes": [{"title": "Tech", "duration": 4}]},
                              {"manifest": [{"rights_verified": False}],
                               "all_rights_verified": False}, Path("/tmp/not-rendered"))

    def test_synthetic_output_is_labeled_correctly(self):
        with patch("openmontage_production.fc.verify_research_payload",
                   return_value={"verified_item_count": 1}), patch(
                       "openmontage_production.creative_renderer.render",
                       return_value={"duration": 4}), patch(
                       "openmontage_production.creative_renderer.verify",
                       return_value={}), patch("pathlib.Path.write_text"):
            report = produce_video({}, {"scenes": [{"title": "Tech", "duration": 4}]},
                                   {"manifest": [{"rights_verified": True}],
                                    "all_rights_verified": True}, Path("/tmp/mock-render"))
        self.assertFalse(report["source_media_included"])
        self.assertFalse(report["subtitles_and_audio"]["spoken_voice_present"])
        self.assertFalse(report["subtitles_and_audio"]["subtitles_burned_in"])
