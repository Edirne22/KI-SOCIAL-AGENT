import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from scripts.openmontage_quality_gate import validate_video


class QualityGateTests(unittest.TestCase):
    def test_valid_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "demo.mp4"
            video.write_bytes(b"sample")
            def probe(*args, **kwargs):
                return SimpleNamespace(stdout=json.dumps({"format": {"duration": "12.5"}, "streams": [{"codec_type": "video", "width": 1080, "height": 1920}]}))
            self.assertEqual(validate_video(video, runner=probe)["duration_seconds"], 12.5)

    def test_missing_stream_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "demo.mp4"
            video.write_bytes(b"sample")
            def probe(*args, **kwargs):
                return SimpleNamespace(stdout=json.dumps({"format": {"duration": "12"}, "streams": []}))
            with self.assertRaises(ValueError):
                validate_video(video, runner=probe)

    def test_empty_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "demo.mp4"
            video.touch()
            with self.assertRaises(ValueError):
                validate_video(video)
