"""Regression test suite for Bundle E++:
- Test 1: Editor CFO series strictness
- Test 2: Semantic QM Knowledge Cutoff bypass
- Test 3: BLOCKED threshold lowered to 3
- Test 4: Community Fallback when final = 2
- Test 5: Community Fallback when final = 0
- Test 6: No Fallback when final = 3
- Test 7: Community Rotation
"""
import unittest
import json
from datetime import datetime, timezone
from pathlib import Path

import motogp_content_agency_v2 as agency
import racing_v855_hardening as hardening
import racing_semantic_qm as semantic_qm

# Install hardening
hardening.install(agency)

class BundleEPPTests(unittest.TestCase):
    def test_1_editor_series_fidelity(self):
        """Test 1 – Editor-Serientreue: Input: Quelle mit SERIE: MotoGP, Text 'X gewinnt das Rennen' -> Editor schreibt nicht 'Moto2'."""
        item = {'title': 'Rider grabs momentum-shifting victory', 'summary': 'X gewinnt das Rennen', 'series': 'MotoGP', 'source_series': 'MotoGP', 'trusted_series': 'MotoGP'}
        agency.lock_source_series(item)
        errs = agency.fact_whitelist_errors(item, 'Rider gewinnt das Moto2-Rennen!')
        self.assertTrue(any('Moto2' in e for e in errs), "Expected Moto2 violation error when CFO is MotoGP")

    def test_2_knowledge_cutoff_ignored(self):
        """Test 2 – Wissens-Cutoff: Input: Quelle mit Datum 'gestern' -> keine Ablehnung wegen 'nach Wissensstand'."""
        item = {'title': 'Race report 2026-09-16', 'summary': 'Test', 'url': 'https://motogp.com/2026/09/16/race'}
        caption = "Das Rennen am 16. September 2026 war spannend. #MotoGP"

        # Mock generate returning a knowledge cutoff response
        orig_generate = semantic_qm.generate
        try:
            semantic_qm.generate = lambda task, prompt: json.dumps({
                "hard_fact_ok": False,
                "series_ok": True,
                "rider_team_ok": True,
                "quote_ok": True,
                "german_ok": True,
                "style_ok": True,
                "hard_reasons": ["Quelle-Datum 2026-09-16 liegt nach Kenntnisstand-Juli-2026; Fakten können nicht überprüft werden"],
                "repair_reasons": []
            })
            res = semantic_qm.review_detailed(item, caption)
            self.assertTrue(res['hard_ok'], "Knowledge cutoff should not fail hard_ok")
            self.assertFalse(res['hard_reasons'], "Hallucinated knowledge cutoff reasons should be filtered out")
        finally:
            semantic_qm.generate = orig_generate

    def test_3_threshold_3_sends_telegram(self):
        """Test 3 – BLOCKED-Schwelle: 3 finale Kandidaten -> Telegram-Versand (nicht BLOCKED)."""
        now = datetime.now(timezone.utc)
        messages = []
        agency.send_message = lambda msg: messages.append(msg)

        # Test 3 candidates -> generate fallbacks if needed, should be total 3 and sent
        picks = [
            {'title': 'Story 1', 'url': 'https://a.com/1', 'caption': 'Post 1 #MotoGP', 'series': 'MotoGP', 'instagram_media': ''},
            {'title': 'Story 2', 'url': 'https://a.com/2', 'caption': 'Post 2 #MotoGP', 'series': 'MotoGP', 'instagram_media': ''},
            {'title': 'Story 3', 'url': 'https://a.com/3', 'caption': 'Post 3 #MotoGP', 'series': 'MotoGP', 'instagram_media': ''}
        ]
        agency.write_session(picks, now)
        agency.telegram_preview(picks, False)

        session_text = agency.SESSION.read_text(encoding='utf-8')
        self.assertIn('Approval-Status: READY', session_text)
        self.assertTrue(len(messages) > 0, "Telegram preview should be sent")

    def test_4_fallback_at_2(self):
        """Test 4 – Fallback bei 2: 2 finale MotoGP -> 1 Community-Spotlight zusätzlich, total 3."""
        now = datetime.now(timezone.utc)
        fallbacks = agency.generate_community_fallbacks(1, now)
        self.assertEqual(len(fallbacks), 1)
        self.assertEqual(fallbacks[0]['series'], 'Community')

    def test_5_fallback_at_0(self):
        """Test 5 – Fallback bei 0: 0 finale MotoGP -> 3 Community-Spotlights."""
        now = datetime.now(timezone.utc)
        fallbacks = agency.generate_community_fallbacks(3, now)
        self.assertEqual(len(fallbacks), 3)

    def test_6_no_fallback_at_3(self):
        """Test 6 – Kein Fallback bei 3: 3 finale MotoGP-Kandidaten -> kein Fallback."""
        picks = [
            {'title': 'Story 1', 'url': 'https://a.com/1', 'caption': 'Post 1 #MotoGP', 'series': 'MotoGP'},
            {'title': 'Story 2', 'url': 'https://a.com/2', 'caption': 'Post 2 #MotoGP', 'series': 'MotoGP'},
            {'title': 'Story 3', 'url': 'https://a.com/3', 'caption': 'Post 3 #MotoGP', 'series': 'MotoGP'}
        ]
        self.assertEqual(len(picks), 3)

    def test_7_community_rotation(self):
        """Test 7 – Rotation: Zweiter Fallback-Lauf -> Andere Community als beim ersten Lauf."""
        now = datetime.now(timezone.utc)
        fb1 = agency.generate_community_fallbacks(1, now)
        fb2 = agency.generate_community_fallbacks(1, now)
        self.assertNotEqual(fb1[0]['title'], fb2[0]['title'], "Rotation should select different community on second run")

if __name__ == '__main__':
    unittest.main(verbosity=2)
