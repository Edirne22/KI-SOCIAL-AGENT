"""Real FFmpeg regressions using generated media only; no network or private data."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import private_birthday_first_production as birthday


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


class MemoryR2:
    def __init__(self, objects):
        self.objects = objects

    def get_object(self, *, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}

    def put_object(self, *, Bucket, Key, Body, **kwargs):
        self.objects[Key] = Body


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class BirthdayTimelineTests(unittest.TestCase):
    def test_invalid_output_never_reaches_delivery(self):
        assets = [{"mime": "image/png", "key": "input"}]
        for duration, streams, corrupt, expected in (
            (324.01, True, False, "PRIVATE_RENDER_DURATION_UNSAFE"),
            (300, False, False, "PRIVATE_RENDER_STREAMS_INVALID"),
            (300, True, True, "PRIVATE_R2_RENDER_VERIFY_FAILED"),
        ):
            with self.subTest(expected=expected):
                client = MemoryR2({"input": b"synthetic"})
                real_get = client.get_object
                def get(**kwargs):
                    if corrupt and kwargs["Key"].startswith("private/v1/productions/"):
                        return {"Body": io.BytesIO(b"corrupted")}
                    return real_get(**kwargs)
                client.get_object = get
                with patch.object(birthday, "client_from_env", return_value=(client, "test")), \
                     patch.dict(os.environ, TELEGRAM_BOT_TOKEN="synthetic", TELEGRAM_CHAT_ID="synthetic"), \
                     patch.object(birthday, "render_segment"), \
                     patch.object(birthday.subprocess, "run"), \
                     patch.object(birthday, "mix_music", side_effect=lambda v, m, o: o.write_bytes(b"output")), \
                     patch.object(birthday, "probe_duration", return_value=duration), \
                     patch.object(birthday, "output_is_valid", return_value=streams), \
                     patch.object(birthday.requests, "post") as send:
                    with self.assertRaisesRegex(RuntimeError, expected):
                        birthday.run(assets_override=assets)
                send.assert_not_called()

    def test_mixed_order_and_short_clip_use_same_timebase(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            ffmpeg("-f", "lavfi", "-i", "color=c=blue:s=160x288", "-frames:v", "1", p / "image.png")
            ffmpeg("-f", "lavfi", "-i", "color=c=red:s=160x288:r=15:d=0.4",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", p / "short.mp4")
            birthday.render_segment(p / "image.png", p / "photo.mp4", is_image=True, seconds=2)
            birthday.render_segment(p / "short.mp4", p / "video.mp4", is_image=False, seconds=2)
            for name in ("photo", "video"):
                result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "stream=time_base,r_frame_rate", "-of", "json", str(p / (name + ".mp4"))],
                    capture_output=True, text=True, check=True)
                stream = json.loads(result.stdout)["streams"][0]
                self.assertEqual(stream["time_base"], "1/25000")
                self.assertEqual(stream["r_frame_rate"], "25/1")
            for order in (("photo", "video"), ("video", "photo")):
                (p / "concat.txt").write_text("".join(f"file '{name}.mp4'\n" for name in order))
                ffmpeg("-f", "concat", "-safe", "0", "-i", p / "concat.txt", "-c", "copy", p / "out.mp4")
                self.assertAlmostEqual(birthday.probe_duration(p / "out.mp4"), 4, delta=0.05)

    def test_full_five_minute_render_audio_r2_hash_and_delivery(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            ffmpeg("-f", "lavfi", "-i", "color=c=blue:s=160x288", "-frames:v", "1", p / "image.png")
            ffmpeg("-f", "lavfi", "-i", "color=c=red:s=160x288:r=15:d=1",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", p / "short.mp4")
            client = MemoryR2({"test-image": (p / "image.png").read_bytes(),
                               "test-video": (p / "short.mp4").read_bytes()})
            # Real timeline alternates photo/video, including a short source clip.
            assets = [{"mime": "image/png", "key": "test-image"},
                      {"mime": "video/mp4", "key": "test-video"}] * 3
            plan = SimpleNamespace(duration_seconds=300, overlays=("Synthetic", "Memory", "End"))
            with patch.object(birthday, "client_from_env", return_value=(client, "test")), \
                 patch.dict(os.environ, TELEGRAM_BOT_TOKEN="synthetic", TELEGRAM_CHAT_ID="synthetic"), \
                 patch.object(birthday.requests, "post", return_value=SimpleNamespace(status_code=200)) as send:
                result = birthday.run(task_id="synthetic", plan=plan, assets_override=assets)
            self.assertAlmostEqual(result["duration"], 300, delta=0.2)
            self.assertTrue(result["has_audio"] and result["has_video"])
            self.assertEqual(birthday.sha256(client.objects[result["r2_key"]]).hexdigest(), result["sha256"])
            send.assert_called_once()
            self.assertLess(len(client.objects[result["r2_key"]]), 49 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
