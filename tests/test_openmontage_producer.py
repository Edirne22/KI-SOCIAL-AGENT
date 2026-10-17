"""Focused producer contract tests; no network or actual rendering."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
from scripts import openmontage_producer as producer


class ProducerTests(unittest.TestCase):
    def test_rejects_invalid_manifest_before_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "job.json"
            for clips in ([], [{}], [{"path": "x.mp4", "seconds": 100}],
                          [{"path": "x.mp4", "seconds": True}]):
                manifest.write_text(json.dumps({"clips": clips}))
                with patch.object(producer.subprocess, "run") as run:
                    with self.assertRaises(ValueError):
                        producer.render(manifest, root / "out.mp4")
                    run.assert_not_called()

    def test_image_producer_uses_local_ffmpeg_and_validates_qc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source.jpg").write_bytes(b"test")
            manifest = root / "job.json"
            manifest.write_text(json.dumps({"clips": [{"path": "source.jpg", "seconds": 2}]}))
            calls = []
            def fake_run(cmd, **kwargs):
                calls.append(cmd)
                return Mock(stdout="")
            with patch.object(producer.subprocess, "run", side_effect=fake_run), \
                 patch.object(producer, "probe", return_value={
                     "streams": [{"codec_type": "video", "width": 1080, "height": 1920}],
                     "format": {"duration": "2.0"}}):
                result = producer.render(manifest, root / "out.mp4")
            self.assertEqual(result["clips"], 1)
            self.assertEqual(result["width"], 1080)
            self.assertEqual(len(calls), 2)
            self.assertIn("concat", calls[1])
            self.assertNotIn("shell", str(calls))

    def test_rejects_non_mp4_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "job.json"
            manifest.write_text(json.dumps({"clips": [{"path": "x.jpg", "seconds": 2}]}))
            with self.assertRaises(ValueError):
                producer.render(manifest, root / "output.txt")


if __name__ == "__main__":
    unittest.main()
