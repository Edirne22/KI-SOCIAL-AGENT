import hashlib
import os
import unittest
from content_factory_private_asr import PrivateASRError, PrivateASRRequest
from content_factory_private_asr_runtime import transcribe_private_audio

ID="11111111-1111-4111-8111-111111111111"
AUDIO=b"synthetic metadata-only bytes; no user voice"
SHA=hashlib.sha256(AUDIO).hexdigest()

class FakeModel:
    def transcribe(self, path, **kwargs):
        assert os.path.exists(path)
        assert kwargs["language"] == "de"
        return [type("Segment", (), {"text":"Synthetic result"})()], type("Info", (), {"language":"de"})()

def req(**kw):
    data=dict(inbox_id=ID,r2_key=f"ai-central/v1/uploads/{ID}/data",
              sha256=SHA,size=len(AUDIO),mime="audio/webm",
              language="de",consent_ref="synthetic-test-only")
    data.update(kw)
    return PrivateASRRequest(**data)

class RuntimeBoundaryTests(unittest.TestCase):
    def test_synthetic_model_positive(self):
        self.assertEqual(transcribe_private_audio(req(),AUDIO,model=FakeModel()).text,"Synthetic result")
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
