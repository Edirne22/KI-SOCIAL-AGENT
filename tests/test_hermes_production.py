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

class DiscoveryRegressionTests(unittest.TestCase):
    @patch('integrations.openmontage.agent_reach_adapter.read_web')
    def test_subject_search_excludes_instruction_words_and_navigation(self, read):
        from integrations.openmontage.agent_reach_adapter import discover, topic_terms
        topic = 'Toprak Razgatlioglu – aktuelle überprüfbare Motorrad-News auf Deutsch'
        self.assertEqual(topic_terms(topic), ['toprak', 'razgatlioglu'])
        stale = 'https://trf1.net/motor-sporlari/toprak-2025/1/'
        fresh = 'https://trf1.net/motor-sporlari/toprak-update/2/'
        read.side_effect = lambda url: {'text': f'[Toprak 2025]({stale})\n### [Toprak Update]({fresh})'} if '?s=' in url else {'text': ''}
        result = discover(topic)
        self.assertEqual([c['url'] for c in result['results']], [fresh])
        self.assertEqual(read.call_args_list[0].args[0], 'https://trf1.net/?s=toprak')

    def test_blocked_checker_diagnostics_survive_without_advancing(self):
        from integrations.openmontage.hermes_coordinator import run_research
        workers = {
            'research_discovery': lambda s: {'candidates': ['source']},
            'source_reader': lambda s: {'documents': [{'url': 'source', 'text': 'evidence'}]},
            'nemotron_analyst': lambda s: {'claims': [{'source_url': 'source', 'claim': 'candidate'}]},
            'fact_checker': lambda s: {'verified_claims': [], 'rejections': [{'index': 0, 'reason': 'wrong attribution'}]},
            'handoff': lambda s: self.fail('Rejected facts must not advance'),
        }
        result = run_research('Toprak', workers, max_retries=0)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertNotIn('fact_checker', result)
        self.assertEqual(result['blocked_outputs']['fact_checker']['rejections'][0]['reason'], 'wrong attribution')

    @patch.dict('os.environ', {'NVIDIA_API_KEY': 'unit-test-sentinel'})
    @patch('integrations.openmontage.hermes_live_workers.urlopen')
    def test_key_reaches_only_provider_request_and_timeout_is_preserved(self, send):
        from integrations.openmontage.hermes_live_workers import model_json
        import io
        send.return_value.__enter__.return_value = io.StringIO('{"choices":[{"finish_reason":"stop","message":{"content":"{}"}}]}')
        self.assertEqual(model_json('test', {}), {})
        request = send.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer unit-test-sentinel')
        self.assertNotIn('unit-test-sentinel', request.data.decode())
        self.assertEqual(send.call_args.kwargs['timeout'], 240)

class EvidenceIdRegressionTests(unittest.TestCase):
    def test_model_selects_source_span_without_retyping_quote(self):
        from integrations.openmontage.hermes_live_workers import evidence_catalog, claims_from_evidence, validate_claims
        doc = {'url': 'https://trf1.net/story/', 'published_at': datetime.now(timezone.utc).isoformat(),
               'text': 'Der Fahrer sagte: „Ich hoffe auf eine baldige Rückkehr.“ Die Entscheidung bleibt offen.'}
        catalog = evidence_catalog([doc])
        claims = claims_from_evidence([{'title': 'Rückkehr bleibt offen',
                                       'claim': 'Der Fahrer hoffte auf eine baldige Rückkehr.',
                                       'evidence_id': 'e0', 'evidence_excerpt': 'invented replacement'}], catalog)
        self.assertEqual(claims[0]['evidence_excerpt'], doc['text'])
        self.assertEqual(len(validate_claims(claims, [doc])), 1)

    def test_unknown_evidence_id_fails_closed(self):
        from integrations.openmontage.hermes_live_workers import claims_from_evidence
        with self.assertRaisesRegex(ValueError, 'Unknown evidence ID'):
            claims_from_evidence([{'evidence_id': 'invented'}], {})
