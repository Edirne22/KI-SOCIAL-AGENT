import hashlib
import os
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess
from content_factory_private_asr import PrivateASRError, PrivateASRRequest
from content_factory_private_asr_runtime import transcribe_private_audio

ID="11111111-1111-4111-8111-111111111111"
AUDIO=b"synthetic metadata-only bytes; no user voice"
SHA=hashlib.sha256(AUDIO).hexdigest()

class FakeModel:
    def transcribe(self, path, **kwargs):
        assert os.path.exists(path)
        assert path.endswith(".wav")
        assert kwargs["language"] == "de"
        assert kwargs["beam_size"] == 5
        assert "Bülent" in kwargs["initial_prompt"]
        assert "Edirne 22" in kwargs["initial_prompt"]
        return [type("Segment", (), {"text":"Synthetic result"})()], type("Info", (), {"language":"de"})()

def req(**kw):
    data=dict(inbox_id=ID,r2_key=f"ai-central/v1/uploads/{ID}/data",
              sha256=SHA,size=len(AUDIO),mime="audio/webm",
              language="de",consent_ref="synthetic-test-only")
    data.update(kw)
    return PrivateASRRequest(**data)

def fake_ffmpeg(command, **kwargs):
    assert command[0] == "ffmpeg"
    assert "-ac" in command and command[command.index("-ac")+1] == "1"
    assert "-ar" in command and command[command.index("-ar")+1] == "16000"
    Path(command[-1]).write_bytes(b"RIFF" + b"0"*48)
    return subprocess.CompletedProcess(command, 0)

class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.ffmpeg=patch("content_factory_private_asr_runtime.subprocess.run", side_effect=fake_ffmpeg)
        self.ffmpeg.start()
        self.addCleanup(self.ffmpeg.stop)

    def test_synthetic_model_positive(self):
        self.assertEqual(transcribe_private_audio(req(),AUDIO,model=FakeModel()).text,"Synthetic result")
    def test_m4a_mime_variants_accepted_by_runtime(self):
        # The Dashboard accepts both MIME variants; runtime must match.
        class CheckM4AModel(FakeModel):
            def transcribe(self, path, **kwargs):
                assert path.endswith(".wav")
                return super().transcribe(path, **kwargs)
        for mime in ("audio/mp4", "audio/x-m4a", "audio/m4a"):
            with self.subTest(mime=mime):
                result=transcribe_private_audio(req(mime=mime), AUDIO, model=CheckM4AModel())
                self.assertEqual(result.text, "Synthetic result")
    def test_decoder_failure_fails_closed(self):
        with patch("content_factory_private_asr_runtime.subprocess.run",
                   side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with self.assertRaisesRegex(PrivateASRError, "decoding failed"):
                transcribe_private_audio(req(mime="audio/x-m4a"), AUDIO, model=FakeModel())
    def test_wrong_bytes_rejected_before_model(self):
        with self.assertRaises(PrivateASRError):
            transcribe_private_audio(req(),b"x"*len(AUDIO),model=FakeModel())
    def test_wrong_length_rejected(self):
        with self.assertRaises(PrivateASRError):
            transcribe_private_audio(req(),AUDIO+b"x",model=FakeModel())
    def test_missing_local_model_fails_closed(self):
        with self.assertRaises(PrivateASRError):
            transcribe_private_audio(req(),AUDIO,model_dir="/no/such/private/model")
    def test_wrong_language_rejected(self):
        class WrongModel(FakeModel):
            def transcribe(self,path,**kw):
                segments,info=super().transcribe(path,**kw)
                info.language="tr"
                return segments,info
        with self.assertRaises(PrivateASRError):
            transcribe_private_audio(req(),AUDIO,model=WrongModel())
    def test_empty_transcript_rejected(self):
        class EmptyModel(FakeModel):
            def transcribe(self,path,**kw):
                return [],type("Info",(),{"language":"de"})()
        with self.assertRaises(PrivateASRError):
            transcribe_private_audio(req(),AUDIO,model=EmptyModel())
if __name__=="__main__": unittest.main()
