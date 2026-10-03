import unittest
from content_factory_private_asr import (
    PrivateASRError, PrivateASRRequest, PrivateASRTranscript, bind_transcript
)

ID = "11111111-1111-4111-8111-111111111111"
SHA = "a" * 64
KEY = f"ai-central/v1/uploads/{ID}/data"

class PrivateASRContractTests(unittest.TestCase):
    def request(self, **overrides):
        args = dict(inbox_id=ID, r2_key=KEY, sha256=SHA, size=1024,
                    mime="audio/webm", language="de", consent_ref="test-consent")
        args.update(overrides)
        return PrivateASRRequest(**args)

    def test_exact_source_is_editable(self):
        r = self.request()
        t = PrivateASRTranscript(ID, SHA, "de", "Test eins zwei drei")
        self.assertEqual(bind_transcript(r, t), "Test eins zwei drei")

    def test_turkish_is_supported(self):
        r = self.request(language="tr")
        self.assertEqual(bind_transcript(r, PrivateASRTranscript(ID, SHA, "tr", "Merhaba")), "Merhaba")

    def test_missing_consent_fails(self):
        with self.assertRaises(PrivateASRError):
            self.request(consent_ref="")

    def test_cross_job_fails(self):
        r = self.request()
        t = PrivateASRTranscript("22222222-2222-4222-8222-222222222222", SHA, "de", "Test")
        with self.assertRaises(PrivateASRError):
            bind_transcript(r, t)

    def test_wrong_digest_fails(self):
        with self.assertRaises(PrivateASRError):
            bind_transcript(self.request(), PrivateASRTranscript(ID, "b"*64, "de", "Test"))

    def test_bad_source_and_size_fail(self):
        for args in ({"r2_key":"public/audio.webm"}, {"size":8*1024*1024+1},
                     {"mime":"video/mp4"}, {"language":"auto"}):
            with self.subTest(args=args), self.assertRaises(PrivateASRError):
                self.request(**args)

    def test_language_mismatch_fails(self):
        with self.assertRaises(PrivateASRError):
            bind_transcript(self.request(), PrivateASRTranscript(ID, SHA, "tr", "Merhaba"))

    def test_overlong_transcript_fails(self):
        with self.assertRaises(PrivateASRError):
            PrivateASRTranscript(ID, SHA, "de", "x"*2501)

if __name__ == "__main__":
    unittest.main()
