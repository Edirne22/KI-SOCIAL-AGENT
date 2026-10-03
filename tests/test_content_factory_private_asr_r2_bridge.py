import hashlib
import io
import json
import unittest
from unittest.mock import patch
from content_factory_private_asr import PrivateASRError
from content_factory_private_asr_r2_bridge import verified_inbox, verified_consent, run_private_r2_asr

ID="11111111-1111-4111-8111-111111111111"
DAY="2026-10-03"
AUDIO=b"synthetic non-voice bytes"
SHA=hashlib.sha256(AUDIO).hexdigest()
INBOX={"schema":"AI-INBOX-V1","id":ID,"kind":"file","channel":"web",
       "created_at":DAY+"T07:00:00Z","file":{"r2_key":f"ai-central/v1/uploads/{ID}/data",
       "mime":"audio/webm","size":len(AUDIO)}}
CONSENT={"schema":"PRIVATE-ASR-CONSENT-V1","inbox_id":ID,
         "source_sha256":SHA,"scope":"transcription","status":"granted"}

class FakeClient:
    def __init__(self,consent=True):
        self.consent=consent;self.writes=[]
    def list_objects_v2(self,**kw):
        return {"Contents":[{"Key":f"ai-central/v1/inbox/{DAY}/one.json"}]}
    def get_object(self,**kw):
        key=kw["Key"]
        if key.endswith("one.json"): return {"Body":io.BytesIO(json.dumps(INBOX).encode())}
        if key.endswith("consent.json"):
            if not self.consent: raise KeyError("revoked")
            return {"Body":io.BytesIO(json.dumps(CONSENT).encode())}
        if key.endswith("/data"):
            return {"Body":io.BytesIO(AUDIO),"ContentType":"audio/webm","ContentLength":len(AUDIO)}
        raise KeyError(key)
    class exceptions:
        class ClientError(Exception):pass
    def head_object(self,**kw):
        e=self.exceptions.ClientError()
        e.response={"Error":{"Code":"404"}}
        raise e
    def put_object(self,**kw):self.writes.append(kw)

class BridgeTests(unittest.TestCase):
    def test_canonical_inbox(self):
        self.assertEqual(verified_inbox(FakeClient(),"private",ID,DAY),INBOX["file"])
    def test_invalid_identity(self):
        with self.assertRaises(PrivateASRError):
            verified_inbox(FakeClient(),"private","bad",DAY)
    def test_missing_consent(self):
        with self.assertRaises(PrivateASRError):
            verified_consent(FakeClient(False),"private",ID,SHA)
    def test_synthetic_private_draft(self):
        from content_factory_private_asr import PrivateASRTranscript
        c=FakeClient()
        def fake_asr(request,audio,**kw):
            self.assertEqual(audio,AUDIO)
            return PrivateASRTranscript(ID,SHA,"de","Synthetic transcript")
        with patch("content_factory_private_asr_r2_bridge.transcribe_private_audio",fake_asr):
            result=run_private_r2_asr(c,"private",ID,DAY,"de")
        self.assertEqual(result["status"],"TRANSCRIPT_PRIVATE_DRAFT")
        self.assertEqual(len(c.writes),1)
        self.assertEqual(json.loads(c.writes[0]["Body"])["text"],"Synthetic transcript")
    def test_revocation_during_inference(self):
        c=FakeClient()
        def revoke(request,audio,**kw):
            c.consent=False
            from content_factory_private_asr import PrivateASRTranscript
            return PrivateASRTranscript(ID,SHA,"de","Synthetic transcript")
        with patch("content_factory_private_asr_r2_bridge.transcribe_private_audio",revoke):
            with self.assertRaises(PrivateASRError):
                run_private_r2_asr(c,"private",ID,DAY,"de")
        self.assertEqual(c.writes,[])
if __name__=="__main__":unittest.main()
