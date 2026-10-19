import json
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from integrations.openmontage.agent_reach_adapter import validate_news_url, fold_text
from integrations.openmontage.hermes_live_workers import (
    publication_date,
    _reader,
    validate_claims,
    _checker,
    _handoff,
)
from openmontage_fact_checker import check_recency, verify_research_payload


class HermesFactcheckRegressionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.fresh_date = self.now.isoformat()
        self.stale_date = (self.now - timedelta(days=10)).isoformat()
        self.future_date = (self.now + timedelta(days=2)).isoformat()
        self.valid_url = 'https://www.motogp.com/en/news/2026/10/19/toprak-update/1234'
        self.trf1_url = 'https://trf1.net/motor-sporlari/toprak-razgatlioglu-basari/5678'
        self.motoetkinlik_url = 'https://motoetkinlik.com/toprak-razgatlioglu-yarisi-kazandi'

    def test_news_url_validation(self):
        for url in (self.valid_url, self.trf1_url, self.motoetkinlik_url):
            self.assertEqual(validate_news_url(url), url)

        for invalid in ('http://www.motogp.com/', 'https://127.0.0.1/news',
                        'https://unapproved-site.com/article', 'https://user:pass@trf1.net/'):
            with self.subTest(url=invalid), self.assertRaises(ValueError):
                validate_news_url(invalid)

    def test_publication_date_extraction(self):
        # Header metadata
        doc1 = {'url': 'https://trf1.net/news/1', 'text': 'Published Time: 2026-10-19T10:00:00+00:00\nMarkdown Content:\nText'}
        self.assertEqual(publication_date(doc1), '2026-10-19T10:00:00+00:00')

        # Permalink date
        doc2 = {'url': 'https://www.motogp.com/en/news/2026/10/19/test/1', 'text': 'Markdown Content:\nText'}
        self.assertEqual(publication_date(doc2), '2026-10-19T00:00:00+00:00')

        # Undated or crawl time
        doc3 = {'url': 'https://trf1.net/about', 'text': 'Retrieved today'}
        self.assertEqual(publication_date(doc3), '')

    def test_check_recency_rules(self):
        ok, msg = check_recency(self.fresh_date)
        self.assertTrue(ok)

        ok, msg = check_recency(self.stale_date)
        self.assertFalse(ok)
        self.assertIn('old', msg)

        ok, msg = check_recency(self.future_date)
        self.assertFalse(ok)
        self.assertIn('future', msg)

        ok, msg = check_recency('')
        self.assertFalse(ok)
        self.assertIn('Missing', msg)

    @patch('integrations.openmontage.hermes_live_workers.read_web')
    def test_reader_filters_stale_and_offtopic(self, mock_read_web):
        mock_read_web.side_effect = [
            # Fresh & topical
            {'url': self.valid_url,
             'text': f'Published Time: {self.fresh_date}\nMarkdown Content:\n# Toprak Razgatlioglu gewinnt das Rennen.'},
            # Stale
            {'url': self.trf1_url,
             'text': f'Published Time: {self.stale_date}\nMarkdown Content:\n# Toprak Razgatlioglu siegte vergangen.'},
            # Off-topic
            {'url': self.motoetkinlik_url,
             'text': f'Published Time: {self.fresh_date}\nMarkdown Content:\n# Völlig anderes Thema ohne Bezug.'},
        ]
        candidates = [
            {'url': self.valid_url, 'title': 'Toprak update'},
            {'url': self.trf1_url, 'title': 'Old Toprak'},
            {'url': self.motoetkinlik_url, 'title': 'Offtopic'},
        ]
        state = {'topic': 'Toprak Razgatlioglu', 'research_discovery': {'candidates': candidates}}
        res = _reader(state)
        self.assertEqual(len(res['documents']), 1)
        self.assertEqual(res['documents'][0]['url'], self.valid_url)

    @patch('integrations.openmontage.hermes_live_workers.read_web')
    @patch('integrations.openmontage.hermes_live_workers.model_json')
    def test_checker_accepts_and_corrects_claims(self, mock_model, mock_read):
        doc = {'url': self.valid_url, 'text': 'Toprak Razgatlioglu hat das SBK-Rennen in Estoril gewonnen.',
               'published_at': self.fresh_date}
        mock_read.return_value = {'url': self.valid_url, 'text': 'Markdown Content:\n' + doc['text'],
                                  'retrieved_at': self.fresh_date, 'sha256': '123'}

        claims = [
            {'source_url': self.valid_url, 'title': 'Toprak siegte in Estoril',
             'claim': 'Toprak Razgatlioglu hat das SBK-Rennen in Estoril gewonnen.',
             'evidence_excerpt': doc['text'], 'published_at': self.fresh_date},
            {'source_url': self.valid_url, 'title': 'Unpräzise Aussage',
             'claim': 'Toprak ist der Schnellste aller Zeiten.',
             'evidence_excerpt': doc['text'], 'published_at': self.fresh_date},
        ]

        # First call: verdict with 1 accepted index and 1 correction
        # Second call: independent review of correction
        mock_model.side_effect = [
            {
                'accepted_indices': [0],
                'corrections': [{'index': 1, 'title': 'Toprak siegte in Estoril 2',
                                 'claim': 'Toprak Razgatlioglu gewann in Estoril.'}],
                'rejections': []
            },
            {
                'accepted_indices': [0],
                'rejections': []
            }
        ]

        res = _checker({'source_reader': {'documents': [doc]},
                        'nemotron_analyst': {'claims': claims},
                        'topic': 'Toprak'})
        self.assertEqual(len(res['verified_claims']), 2)
        self.assertEqual(res['verified_claims'][0]['title'], 'Toprak siegte in Estoril')
        self.assertEqual(res['verified_claims'][1]['title'], 'Toprak siegte in Estoril 2')

    def test_verify_research_payload_filters_invalid_stories(self):
        valid_story = {
            'story_id': 's1', 'title': 'Valid news', 'summary': 'Summary',
            'published_at': self.fresh_date, 'content_type': 'news',
            'series': 'MotoGP', 'source_status': 'journalistic'
        }
        stale_story = {
            'story_id': 's2', 'title': 'Stale news', 'summary': 'Old summary',
            'published_at': self.stale_date, 'content_type': 'news',
            'series': 'MotoGP', 'source_status': 'journalistic'
        }
        undated_story = {
            'story_id': 's3', 'title': 'Undated news', 'summary': 'Undated summary',
            'published_at': '', 'content_type': 'news',
            'series': 'MotoGP', 'source_status': 'journalistic'
        }

        res = verify_research_payload({'stories': [valid_story, stale_story, undated_story]})
        self.assertEqual(res['verified_item_count'], 1)
        self.assertEqual(res['rejected_item_count'], 2)
        self.assertEqual(len(res['needs_date_verification']), 1)


if __name__ == '__main__':
    unittest.main()
