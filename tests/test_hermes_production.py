import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from integrations.openmontage.agent_reach_adapter import validate_news_url
from integrations.openmontage.hermes_live_workers import validate_claims, _checker, publication_date


class ProductionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.url = 'https://www.motogp.com/en/news/2026/10/12/example/123'
        self.quote = 'Toprak reported shoulder pain and a lack of strength under braking.'
        self.doc = {'url': self.url, 'text': self.quote,
                    'published_at': datetime.now(timezone.utc).isoformat()}
        self.claim = {'source_url': self.url, 'title': 'Toprak berichtet von Schmerzen',
                      'claim': 'Toprak berichtete von Schmerzen in der Schulter.',
                      'evidence_excerpt': self.quote}

    def test_real_excerpt_passes(self):
        self.assertEqual(len(validate_claims([self.claim], [self.doc])), 1)

    def test_fabricated_excerpt_and_unknown_source_block(self):
        for change in ({'evidence_excerpt': 'Invented evidence ' * 5},
                       {'source_url': 'https://trf1.net/not-retrieved'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_claims([dict(self.claim, **change)], [self.doc])

    def test_stale_future_missing_dates_block(self):
        now = datetime.now(timezone.utc)
        for date in ('', (now-timedelta(days=8)).isoformat(), (now+timedelta(days=1)).isoformat()):
            with self.subTest(date=date), self.assertRaises(ValueError):
                validate_claims([self.claim], [dict(self.doc, published_at=date)])

    def test_private_and_unapproved_urls_block(self):
        for url in ('http://www.motogp.com/', 'https://127.0.0.1/',
                    'https://www.motogp.com.evil.test/', 'https://user:pass@trf1.net/',
                    'https://trf1.net:8080/', 'https://example.com/'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_news_url(url)
        self.assertEqual(validate_news_url(self.url), self.url)

    @patch('integrations.openmontage.hermes_live_workers.model_json')
    def test_checker_rejection_is_not_promoted(self, model):
        model.return_value = {'accepted_indices': [], 'rejections': [{'index': 0, 'reason': 'not supported'}]}
        result = _checker({'source_reader': {'documents': [self.doc]},
                           'nemotron_analyst': {'claims': [self.claim]}})
        self.assertEqual(result['verified_claims'], [])

    @patch('integrations.openmontage.hermes_live_workers.model_json', side_effect=TimeoutError)
    def test_provider_failure_has_no_fallback(self, model):
        with self.assertRaises(TimeoutError):
            _checker({'source_reader': {'documents': [self.doc]},
                      'nemotron_analyst': {'claims': [self.claim]}})

    def test_crawl_time_is_not_publication_date(self):
        self.assertEqual(publication_date({'url': 'https://trf1.net/article/',
                                          'text': 'Retrieved today'}), '')


if __name__ == '__main__':
    unittest.main()
