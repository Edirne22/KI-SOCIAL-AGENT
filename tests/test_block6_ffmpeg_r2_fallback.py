import json
import pathlib
import tempfile
import unittest
from types import SimpleNamespace

from scripts import block6_ffmpeg_r2_fallback as m

class FFmpegAlternative(unittest.TestCase):
    def test_source_locked_and_duration_limited_before_process(self):
        with tempfile.TemporaryDirectory() as temp:
            dest=pathlib.Path(temp)/"result.mp4"
            for secs in (0,1,6,8,16,31,300):
                with self.subTest(secs=secs),self.assertRaisesRegex(ValueError,"duration"):
                    m.run_ffmpeg(m.SOURCE,dest,secs,runner=lambda *a,**kw:self.fail("forbidden"))
            bad=pathlib.Path(temp)/"untrusted.mp4"
            bad.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError,"only tracked"):
                m.run_ffmpeg(bad,dest,7,runner=lambda *a,**kw:self.fail("forbidden"))
    def test_no_shell_constant_caption_and_bounded_encoder(self):
        with tempfile.TemporaryDirectory() as temp:
            out=pathlib.Path(temp)/"7.mp4"
            commands=[]
            def fake(cmd,**kw):
                commands.append((cmd,kw))
                out.write_bytes(b"fake-mp4")
                return SimpleNamespace(returncode=0)
            m.run_ffmpeg(m.SOURCE,out,7,runner=fake)
            self.assertEqual(len(commands),1)
            cmd,kw=commands[0]
            self.assertEqual(cmd[0],"ffmpeg")
            self.assertNotIn("shell",kw)
            self.assertEqual(kw["timeout"],180)
            self.assertIn("EDIRNE 22 TEST"," ".join(cmd))
            self.assertIn("anullsrc=r=48000:cl=stereo",cmd)
    def test_failed_or_oversized_render_blocks_storage(self):
        with tempfile.TemporaryDirectory() as temp:
            out=pathlib.Path(temp)/"failed.mp4"
            with self.assertRaisesRegex(RuntimeError,"RENDER_FAILED"):
                m.run_ffmpeg(m.SOURCE,out,7,
                    runner=lambda *a,**kw:SimpleNamespace(returncode=1))
    def test_probe_requires_video_audio_duration_and_size(self):
        with tempfile.TemporaryDirectory() as temp:
            out=pathlib.Path(temp)/"7.mp4"
            p={"format":{"duration":"7.00","size":"1280"},
                "streams":[{"codec_type":"video","codec_name":"h264"},
                           {"codec_type":"audio","codec_name":"aac"}]}
            fake=lambda *a,**kw:SimpleNamespace(returncode=0,stdout=json.dumps(p))
            self.assertEqual(m.inspect_ffprobe(out,7,runner=fake)["tracks"],["audio","video"])
            p["streams"]=p["streams"][:1]
            with self.assertRaisesRegex(RuntimeError,"MEDIA_CONTRACT"):
                m.inspect_ffprobe(out,7,runner=fake)
            p["streams"].append({"codec_type":"audio"})
            p["format"]["duration"]="1.25"
            with self.assertRaisesRegex(RuntimeError,"MEDIA_CONTRACT"):
                m.inspect_ffprobe(out,7,runner=fake)
if __name__=="__main__":unittest.main()
