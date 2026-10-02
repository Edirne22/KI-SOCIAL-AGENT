"""No-network source triage regression for existing capped Apify YouTube route."""
import unittest
from inspiration.youtube_source_evidence import filter_results,review_video

BASE={"url":"https://www.youtube.com/watch?v=k0XXTKmcrLI",
      "title":"Moto3 Practice Full Highlights | 2026 Japanese Grand Prix",
      "channelTitle":"Motorcycle TV"}
CID="UC"+"A"*22


class YoutubeEvidenceTests(unittest.TestCase):
    def test_real_sample_unrelated_recipe_uploader_is_quarantined(self):
        row={**BASE,"channelTitle":"مطبخ ام رسيم"}
        result=review_video(row)
        self.assertEqual(result.triage,"QUARANTINE")
        self.assertEqual(result.coverage,"METADATA_ONLY")
        self.assertEqual(result.channel_verification,"NOT_VERIFIED")
    def test_another_sample_unrelated_routines_uploader_is_quarantined(self):
        self.assertEqual(review_video({**BASE,"channelTitle":"روتينات في الريف"}).triage,"QUARANTINE")
    def test_foreign_language_alone_is_never_quarantined(self):
        for channel in ["Türkiye yarış dünyası","عالم سباقات الدراجات","Motorcycle Deutschland"]:
            verdict=review_video({**BASE,"channelTitle":channel})
            self.assertEqual(verdict.triage,"RESEARCH_ONLY")
    def test_official_sounding_display_name_never_authenticates_official(self):
        verdict=review_video({**BASE,"channelTitle":"MotoGP Official"})
        self.assertEqual(verdict.channel_verification,"NOT_VERIFIED")
        self.assertEqual(verdict.coverage,"METADATA_ONLY")
    def test_exact_precurated_channel_id_only_confirms_account_not_video(self):
        verdict=review_video({**BASE,"channelId":CID},trusted_channel_ids=frozenset({CID}))
        self.assertEqual(verdict.channel_verification,"CURATED_CHANNEL_ID")
        self.assertEqual(verdict.coverage,"METADATA_ONLY")
        self.assertEqual(verdict.triage,"CHANNEL_CONFIRMED_METADATA_ONLY")
    def test_impostor_id_and_official_name_not_accepted(self):
        verdict=review_video({**BASE,"channelId":"UC"+"B"*22,
                              "channelTitle":"MotoGP Official"},trusted_channel_ids=frozenset({CID}))
        self.assertEqual(verdict.channel_verification,"NOT_VERIFIED")
    def test_unrelated_racing_interview_is_not_arbitrarily_deleted(self):
        row={**BASE,"title":"Toprak Razgatlioglu interview","channelTitle":"cooking"}
        self.assertEqual(review_video(row).triage,"RESEARCH_ONLY")
    def test_invalid_non_youtube_url_or_redirected_link_is_quarantined(self):
        for url in ["https://youtube.com.evil.invalid/watch?v=k0XXTKmcrLI",
                    "http://www.youtube.com/watch?v=k0XXTKmcrLI",
                    "https://youtu.be/not-a-video"]:
            self.assertEqual(review_video({**BASE,"url":url}).triage,"QUARANTINE")
    def test_keeps_original_urls_and_all_quarantine_evidence(self):
        good={**BASE,"channelTitle":"Motorcycle World"}
        bad={**BASE,"channelTitle":"مطبخ ام رسيم"}
        accepted,quarantined=filter_results([good,bad])
        self.assertEqual(len(accepted),1)
        self.assertEqual(len(quarantined),1)
        self.assertEqual(quarantined[0][0]["url"],bad["url"])
        self.assertEqual(accepted[0][1].coverage,"METADATA_ONLY")
    def test_pretend_transcript_json_must_not_escalate_coverage(self):
        row={**BASE,"transcript":"fake extracted user-provided text",
             "description":"I saw this full video"}
        self.assertEqual(review_video(row).coverage,"METADATA_ONLY")

if __name__=="__main__":
    unittest.main()
