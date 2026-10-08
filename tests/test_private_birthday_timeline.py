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

    def test_renderer_uses_plan_music_and_dynamic_title_timing(self):
        source=Path(birthday.__file__).read_text(encoding="utf-8")
        self.assertIn('music=Path(getattr(plan,"music_track",MUSIC)',source)
        self.assertIn('midpoint=max(8.0,target_seconds*0.50)',source)
        self.assertIn('ending=max(midpoint+8.0,target_seconds-14.0)',source)
        self.assertNotIn("between(t,286,299)",source)

    def test_original_audio_timeline_contract(self):
        with self.assertRaisesRegex(ValueError,"PRIVATE_AUDIO_TIMELINE_MISMATCH"):
            birthday.build_original_audio_mix([(Path("a.mp4"),True)],[0.0,2.0],[2.0],Path("out.m4a"))
        self.assertFalse(birthday.build_original_audio_mix(
            [(Path("photo.jpg"),False)],[0.0],[3.0],Path("unused.m4a")))

    def test_real_original_audio_ducking_synthetic(self):
        from music_agent import mix_music, source_has_audio
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            video=p/"voice.mp4"; music=p/"music.wav"; output=p/"mixed.mp4"
            ffmpeg("-f","lavfi","-i","color=c=black:s=160x288:r=25:d=2",
                   "-f","lavfi","-i","sine=frequency=500:duration=2",
                   "-c:v","libx264","-c:a","aac","-shortest",video)
            ffmpeg("-f","lavfi","-i","sine=frequency=220:duration=2",music)
            self.assertTrue(source_has_audio(video))
            mix_music(video,music,output,duck_original=True)
            self.assertTrue(birthday.output_is_valid(output))

    def test_real_xfade_between_synthetic_segments(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            for name,color in (("first","red"),("second","blue")):
                ffmpeg("-f","lavfi","-i",f"color=c={color}:s=540x960:r=25:d=2",
                       "-c:v","libx264","-pix_fmt","yuv420p",p/(name+".mp4"))
            cmd=birthday.build_xfade_command(
                [p/"first.mp4",p/"second.mp4"],[2.0,2.0],
                [("soft_fade",0.35),("quick_fade",0.30)],p/"xfade.mp4")
            self.assertIn("xfade=transition=smoothleft"," ".join(cmd))
            birthday.run_ffmpeg(cmd,step="synthetic_xfade",timeout=90)
            self.assertAlmostEqual(birthday.probe_duration(p/"xfade.mp4"),3.7,delta=0.15)
            import numpy as np
            pixels=subprocess.check_output(["ffmpeg","-v","error","-ss","1.85","-i",str(p/"xfade.mp4"),
                "-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"])
            mean=np.frombuffer(pixels,dtype=np.uint8).reshape(-1,3).mean(axis=0)
            self.assertGreater(mean[0],30)  # old red frame survives inside transition
            self.assertGreater(mean[2],30)  # new blue frame appears; no black fade

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
            plan = SimpleNamespace(duration_seconds=300, overlays=("Synthetic", "Memory", "End"),
                                   asset_effects=("zoom_in","pan_left","zoom_out","pan_right","zoom_in","pan_left"),
                                   asset_transitions=(("soft_fade",0.35),("soft_fade",0.35),("quick_fade",0.22),("quick_fade",0.22),("long_fade",0.80),("long_fade",0.80)),
                                   asset_pacing=(1.12,1.0,0.78,0.92,1.15,1.20),
                                   scene_plan=({"id":"a"},{"id":"b"},{"id":"c"},{"id":"d"}),
                                   creative_revision="duenya-creative-v2",asset_order=tuple(range(6)))
            with patch.object(birthday, "client_from_env", return_value=(client, "test")), \
                 patch.dict(os.environ, TELEGRAM_BOT_TOKEN="synthetic", TELEGRAM_CHAT_ID="synthetic"), \
                 patch.object(birthday.requests, "post", return_value=SimpleNamespace(status_code=200)) as send:
                result = birthday.run(task_id="synthetic", plan=plan, assets_override=assets)
            self.assertAlmostEqual(result["duration"], 300, delta=0.2)
            self.assertTrue(result["has_audio"] and result["has_video"])
            self.assertGreaterEqual(len(result["creative_evidence"]["applied_effects"]),3)
            self.assertEqual(result["creative_evidence"]["creative_revision"],"duenya-creative-v2")
            self.assertEqual(birthday.sha256(client.objects[result["r2_key"]]).hexdigest(), result["sha256"])
            send.assert_not_called()
            self.assertLess(len(client.objects[result["r2_key"]]), 49 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()

@unittest.skipUnless(shutil.which("ffmpeg"),"FFmpeg required")
class MeasuredAudioTests(unittest.TestCase):
    def test_ducking_reduces_music_and_preserves_time(self):
        import numpy as np
        from music_agent import mix_music
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            # Original sound only from t=2 to t=4; music occupies another frequency.
            ffmpeg('-f','lavfi','-i','color=c=black:s=160x288:r=25:d=6',
                   '-f','lavfi','-i',"aevalsrc=0.35*sin(2*PI*1000*t)*between(t\\,2\\,4):s=48000:d=6",
                   '-c:v','libx264','-c:a','aac','-shortest',p/'voice.mp4')
            ffmpeg('-f','lavfi','-i','sine=frequency=220:sample_rate=48000:duration=6',p/'music.wav')
            mix_music(p/'voice.mp4',p/'music.wav',p/'mixed.mp4',duck_original=True)
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p/'mixed.mp4'),'-f','f32le','-ac','1','-ar','48000','-'])
            samples=np.frombuffer(raw,dtype='<f4')
            def amplitude(freq,start):
                part=samples[int(start*48000):int((start+0.4)*48000)]
                t=np.arange(len(part))/48000
                return abs(np.sum(part*np.exp(-2j*np.pi*freq*t)))*2/len(part)
            before=amplitude(220,1.3);during=amplitude(220,2.6)
            self.assertLess(during,before*0.65)
            self.assertGreater(amplitude(1000,2.6),0.20)
            self.assertLess(amplitude(1000,1.3),0.005)
            self.assertAlmostEqual(birthday.probe_duration(p/'mixed.mp4'),6,delta=0.15)

    def test_delayed_trimmed_original_bed_pads_silent_finale(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            ffmpeg('-f','lavfi','-i','sine=frequency=800:sample_rate=48000:duration=3',p/'source.wav')
            birthday.build_original_audio_mix([(p/'source.wav',True)],[1.5],[1.0],p/'bed.m4a',
                                              source_starts=[0.5],total_duration=6)
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p/'bed.m4a'),'-f','f32le','-ac','1','-ar','48000','-'])
            samples=np.frombuffer(raw,dtype='<f4')
            rms=lambda a,b: float(np.sqrt(np.mean(samples[int(a*48000):int(b*48000)]**2)))
            self.assertLess(rms(0.2,1.2),0.001)
            self.assertGreater(rms(1.7,2.3),0.03)
            self.assertLess(rms(3,5.8),0.001)
            self.assertAlmostEqual(birthday.probe_duration(p/'bed.m4a'),6,delta=0.1)
