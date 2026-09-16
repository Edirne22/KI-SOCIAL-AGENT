"""Deterministic V8.6 regressions. No provider/network calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import racing_cfo as c
import motogp_content_agency_v2 as a
from racing_v855_hardening import install
install(a)

def item(title='Agius takes Moto2 P1 at San Marino', summary='Agius fastest in Practice.'):
    return {'title': title, 'summary': summary, 'source_series': 'Moto2'}

def post(body='Agius holt P1 in San Marino.'):
    return 'Agius vorne\n\n' + body + '\n\nWas meint ihr dazu?\n\n#Moto2 #Agius #MotorradRacing #RacingDeutschland #BuelentsBikeLife'

def semantic(hard=True, language=True):
    return {'hard_ok': hard, 'language_ok': language,
            'hard_reasons': [] if hard else ['unsupported relationship'],
            'repair_reasons': [] if language else ['holpriger Satz']}

class Facts(unittest.TestCase):
    def setUp(self):
        self.x = item()
        self.f = c.build_cfo(self.x, ('Senna Agius', 'Manuel Gonzalez'))

    def test_schema_and_source_only(self):
        for key in ('series', 'event', 'session', 'riders', 'entities', 'teams', 'manufacturers',
                    'locations', 'dates', 'positions', 'numbers', 'relationships', 'claims', 'modality', 'forbidden_inferences'):
            self.assertIn(key, self.f)
        self.assertEqual(self.f['riders'][0]['value'], 'Agius')
        self.assertNotIn('Senna', json.dumps(self.f))
        self.assertEqual(self.f['teams'], [])
        self.assertEqual(c.validate_cfo(self.f, self.x, ('Senna Agius', 'Manuel Gonzalez')), [])

    def test_evidence(self):
        source = c.source_text(self.x)
        def visit(obj):
            if isinstance(obj, dict):
                if 'evidence' in obj:
                    e = obj['evidence']
                    self.assertEqual(source[e['start']:e['end']], e['text'])
                for value in obj.values(): visit(value)
            elif isinstance(obj, list):
                for value in obj: visit(value)
        visit(self.f)

    def test_no_roster_series_inference(self):
        f = c.build_cfo({'title': 'Agius takes pole', 'summary': ''}, ('Senna Agius',))
        self.assertEqual(f['series'], '')

    def test_transfer_and_metadata(self):
        self.assertEqual(c.select_series({'title':'Tech3 signs Agius for MotoGP debut from 2027', 'source_series':'Moto2'})[0], 'MotoGP')
        self.assertEqual(c.select_series({'title':'Quiles takes pole', 'summary':'The Official Home of MotoGP', 'source_series':'Moto3'})[0], 'Moto3')
        self.assertEqual(c.series_mentions('WorldSSP300 #WorldSSP300'), ['WorldSSP300'])

    def test_known_good(self):
        self.assertEqual(c.guard_errors(self.f, post()), [])
        self.assertEqual(c.guard_errors(self.f, post('Agius holt Platz 1 in San Marino.')), [])

    def test_required_regressions(self):
        cases = [
            (self.f, post().replace('Agius', 'Aras'), 'Entity'),
            (self.f, post().replace('Agius vorne', 'Aras Agius vorne'), 'Entity'),
            (self.f, post().replace('San Marino', 'Mugello'), 'Entity'),
            (self.f, post('Agius übernimmt die Meisterschaftsführung.'), 'Claim'),
            (self.f, post('Agius holt P1 mit 99 Punkten.'), 'Number'),
            (c.build_cfo(item('Gonzalez grabs Moto2 pole', 'Gonzalez takes pole.')), 'Gonzales holt die Pole.', 'Entity'),
            (c.build_cfo(item('WorldSBK teams react', 'WorldSBK race.')), 'WorldSSP und Supersport', 'Series'),
        ]
        for f, caption, kind in cases:
            with self.subTest(caption=caption):
                errors = c.guard_errors(f, caption)
                self.assertTrue(any(kind in e for e in errors), errors)

    def test_hashtag_bypass(self):
        self.assertTrue(c.guard_errors(self.f, post() + ' #Mugello #99 #WorldSSP'))

    def test_new_team_manufacturer_first_name(self):
        for text in ('Agius fährt für Yamaha.', 'Agius fährt für Pramac.', 'Senna Agius holt P1.'):
            self.assertTrue(c.guard_errors(self.f, post(text), ('Senna Agius',)))

    def test_positions_not_qualifying(self):
        self.assertTrue(c.guard_errors(self.f, post().replace('P1', 'Q1')))

    def test_modality(self):
        f = c.build_cfo(item('Ogura targets MotoGP return', 'Ogura may return.'))
        self.assertTrue(c.guard_errors(f, 'Ogura wird sicher zurückkehren.'))
        self.assertEqual(c.guard_errors(f, 'Ogura hofft auf seine Rückkehr.'), [])

    def test_mutation(self):
        self.f['claims'][0]['value'] = 'invented'
        self.assertTrue(c.validate_cfo(self.f, self.x))
        self.f = c.build_cfo(self.x)
        self.x['summary'] += ' new fact'
        self.assertTrue(c.validate_cfo(self.f, self.x))

class Patches(unittest.TestCase):
    def test_exact_merge(self):
        before = post('Agius holt P1 in Mugello.')
        raw = json.dumps({'patches':[{'old':'Mugello', 'new':'San Marino'}]})
        self.assertEqual(c.apply_patch(before, raw), post())

    def test_invalid_atomic_patches(self):
        before = post('Agius holt P1 in Mugello.')
        invalid = [
            'not JSON', '{}', '{"patches":[]}', before,
            json.dumps({'patches':[{'old':'absent','new':'x'}]}),
            json.dumps({'patches':[{'old':'Agius','new':'x'}]}),
            json.dumps({'patches':[{'old':'Mugello','new':'Mugello'}]}),
            json.dumps({'patches':[{'old':before,'new':post()}]}),
            json.dumps({'patches':[{'old':'Mugello','new':'San Marino'},{'old':'in Mugello','new':'hier'}]}),
            json.dumps({'patches':[{'old':'Mugello','new':'San Marino'},{'old':'missing','new':'x'}]}),
            json.dumps({'patches':[{'old':'Mugello','new':42}]}),
        ]
        for raw in invalid:
            with self.subTest(raw=raw):
                with self.assertRaises((ValueError, TypeError)):
                    c.apply_patch(before, raw)
        self.assertIn('Mugello', before)

    def test_no_cascading(self):
        raw = json.dumps({'patches':[{'old':'Mugello','new':'Misano'},{'old':'Misano','new':'San Marino'}]})
        with self.assertRaises(ValueError): c.apply_patch(post('Agius holt P1 in Mugello.'), raw)

class Pipeline(unittest.TestCase):
    def run_case(self, caption, responses=(), sem=None, racing=None):
        x = item()
        with patch.object(a, 'racing_relevant', return_value=True), \
             patch.object(a, 'german_editor', return_value=caption) as editor, \
             patch.object(a, 'generate', side_effect=list(responses)) as generator, \
             patch.object(a, 'racing_review', side_effect=racing or (lambda x,c: (True, []))) as qm, \
             patch.object(a, 'semantic_review_detailed', side_effect=sem or (lambda x,c: semantic())) as sm, \
             patch.object(a, 'reanalyse_source', side_effect=AssertionError('no research')), \
             patch.object(a, 'language_sane', return_value=True):
            result = a.qualify_copy(x)
        return result, x, editor, generator, qm, sm

    def test_guard_repair_before_semantic(self):
        result, x, editor, gen, qm, sem = self.run_case(
            post('Agius holt P1 in Mugello.'),
            [json.dumps({'patches':[{'old':'Mugello','new':'San Marino'}]})])
        self.assertTrue(result)
        self.assertEqual(editor.call_count, 1)
        self.assertEqual(gen.call_count, 1)
        self.assertEqual(sem.call_count, 1)
        self.assertEqual(x['rewrite_count'], 1)
        self.assertEqual([h['stage'] for h in x['guard_history']], ['whitelist','pass'])

    def test_new_numbers_after_repair_block_semantic(self):
        bad = json.dumps({'patches':[{'old':'San Marino','new':'San Marino mit 99 Punkten'}]})
        result, x, _, gen, qm, sem = self.run_case(post(), [bad, '{}'], lambda x,c: semantic(language=False))
        self.assertFalse(result)
        self.assertEqual(sem.call_count, 1)
        self.assertTrue(any('Number' in e for e in x['guard_errors']))
        self.assertEqual(x['rewrite_count'], 2)

    def test_strict_semantic_remains_required(self):
        result, x, _, _, _, sem = self.run_case(post(), ['{}','{}'], lambda x,c: semantic(hard=False))
        self.assertFalse(result)
        self.assertEqual(sem.call_count, 3)
        self.assertEqual(x['semantic_qm'], 'FAIL')

    def test_no_free_regeneration(self):
        result, x, editor, gen, _, sem = self.run_case(post('Agius holt P1 in Mugello.'), [post(), post()])
        self.assertFalse(result)
        self.assertEqual(editor.call_count, 1)
        self.assertEqual(gen.call_count, 2)
        self.assertEqual(sem.call_count, 0)
        self.assertTrue(all(not h['applied'] for h in x['repair_history']))

    def test_racing_mutation_rechecked(self):
        def racing(x, caption):
            x['caption'] = caption + ' #Mugello'
            return True, []
        result, x, _, _, _, sem = self.run_case(post(), ['{}', '{}'], racing=racing)
        self.assertFalse(result)
        self.assertEqual(sem.call_count, 0)

    def test_immutable_source_before_editor(self):
        x = item()
        def editor(record, reasons):
            self.assertIn('canonical_fact_object', record)
            record['summary'] += ' 99 points'
            return post()
        with patch.object(a, 'racing_relevant', return_value=True), patch.object(a, 'german_editor', side_effect=editor), patch.object(a, 'generate', return_value='{}'), patch.object(a, 'semantic_review_detailed') as sem:
            self.assertFalse(a.qualify_copy(x))
            self.assertEqual(sem.call_count, 0)

    def test_semantic_non_boolean_cannot_pass(self):
        import racing_semantic_qm as sem
        response = dict(hard_fact_ok='false', series_ok=True, rider_team_ok=True,
                        quote_ok=True, german_ok=True, style_ok=True,
                        hard_reasons=[], repair_reasons=[])
        with patch.object(sem, 'generate', return_value=json.dumps(response)):
            self.assertFalse(sem.review_detailed(item(), post())['hard_ok'])

    def test_technical_defer(self):
        with patch('racing_v855_hardening.time.sleep'):
            result, x, _, gen, _, sem = self.run_case(post(), sem=lambda x,c: {
                'hard_ok':False, 'language_ok':False,
                'hard_reasons':['Semantischer Fakten-QM technisch ungueltig'], 'repair_reasons':[]})
        self.assertFalse(result)
        self.assertEqual(x['semantic_qm'], 'TECHNICAL-DEFER')
        self.assertEqual(gen.call_count, 0)
        self.assertEqual(sem.call_count, 2)

    def test_real_editor_qm_and_artifact(self):
        import motogp_pipeline_diagnose as d
        editor_reply = json.dumps({'hook':'Agius vorne', 'body':'Agius holt P1 in San Marino.', 'question':'Was meint ihr dazu?'})
        x = item()
        with tempfile.TemporaryDirectory() as td, patch.object(d, 'ARTIFACT_DIR', Path(td)), patch.object(d, 'QM_ARTIFACT', Path(td)/'qm.json'), patch.object(a, 'generate', return_value=editor_reply), patch.object(a, 'semantic_review_detailed', return_value=semantic()), patch.object(a, 'racing_relevant', return_value=True):
            result, deferred = d.run_copy_qm('offline-v86', [x])
            self.assertEqual((len(result), deferred), (1, 0))
            saved = json.loads((Path(td)/'qm.json').read_text(encoding='utf-8'))
            row = saved['items'][0]
            for key in ('status','title','url','series','semantic_qm','racing_qm','rewrite_count','qm_errors','semantic_errors','technical_error','canonical_fact_object','guard_errors','guard_history','repair_history'):
                self.assertIn(key, row)
            self.assertNotIn('Senna', x['caption'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
