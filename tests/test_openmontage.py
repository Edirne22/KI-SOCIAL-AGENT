"""Offline contract + attack controls; no provider, Telegram or render calls."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import requests
import yaml
from scripts import openmontage_control as control

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('om_runtime', ROOT / 'integrations/openmontage/runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / 'state.json'
        self.env = patch.dict(os.environ, {'GITHUB_TOKEN': 'FAKE_TEST_TOKEN'})
        self.env.start()
        self.post = Mock(return_value=Mock(status_code=204))
    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()
    def handle(self, text, **kw):
        return control.handle(text, 44, '1', '1', state=self.state, post=self.post, **kw)
    def test_explicit_start_has_fixed_main_workflow_and_inputs(self):
        result = self.handle('/montage test starten')
        self.assertIn('angenommen', result)
        call = self.post.call_args
        self.assertEqual(call.args[0], control.API + '/actions/workflows/openmontage.yml/dispatches')
        self.assertEqual(call.kwargs['json'], {'ref': 'main', 'inputs': {'mode': 'demo', 'request_id': 'tg-44'}})
        self.assertNotIn('FAKE_TEST_TOKEN', self.state.read_text())
    def test_renew_dispatch_uses_media_id_not_demo_inputs(self):
        media_id = '4b3e8b9c-4449-4586-a048-0e6f77f41813'
        result = self.handle('/montage link neu ' + media_id)
        self.assertIn('angenommen', result)
        call = self.post.call_args
        self.assertEqual(call.args[0], control.API + '/actions/workflows/openmontage-renew-link.yml/dispatches')
        self.assertEqual(call.kwargs['json'], {'ref': 'main', 'inputs': {'media_id': media_id}})

    def test_help_proposal_and_injection_never_start(self):
        for text in ['/montage', '/montage test', '/montage test starten; curl attacker',
                     '/montage diagnose $(id)', '/montage fremde-private-datei', '/montage status ../']:
            self.handle(text)
        self.post.assert_not_called()
    def test_bot_suffix_and_normal_commands(self):
        self.assertEqual(control.parse_command('/montage@MyBot diagnose'), 'diagnose')
        self.assertIsNone(control.parse_command('motogp 1'))
        self.assertIsNone(control.parse_command('/montagefake test starten'))
    def test_owner_check_before_api_or_state(self):
        for owner, chat in [('1', '2'), ('', '')]:
            with self.assertRaises(PermissionError):
                control.handle('/montage diagnose', 44, chat, owner, post=self.post, state=self.state)
        self.post.assert_not_called()
        self.assertFalse(self.state.exists())
    def test_repeat_and_process_restart_do_not_redispatch(self):
        self.handle('/montage diagnose')
        self.handle('/montage diagnose')
        self.assertEqual(self.post.call_count, 1)
    def test_ambiguous_timeout_does_not_retry_or_leak(self):
        self.post.side_effect = requests.Timeout('FAKE_TEST_TOKEN private response')
        result = self.handle('/montage diagnose')
        self.assertIn('unklar', result)
        self.assertNotIn('FAKE_TEST_TOKEN', result)
        self.handle('/montage diagnose')
        self.assertEqual(self.post.call_count, 1)
    def test_rejected_dispatch_is_not_success(self):
        self.post.return_value.status_code = 403
        self.assertIn('HTTP 403', self.handle('/montage diagnose'))
        self.assertEqual(json.loads(self.state.read_text())['tg-44'], 'rejected-http-403')
    def test_missing_token_and_corrupt_state_fail_closed(self):
        with patch.dict(os.environ, {'GITHUB_TOKEN': ''}):
            with self.assertRaises(ValueError): self.handle('/montage diagnose')
        self.state.write_text('not json')
        with self.assertRaises(ValueError): self.handle('/montage diagnose')
        self.post.assert_not_called()
    def test_status_reports_actual_failure_and_fixed_run_url(self):
        get = Mock(return_value=Mock(status_code=200, json=lambda: {'workflow_runs': [
            {'id': 7, 'conclusion': 'failure', 'status': 'completed', 'html_url': 'https://attacker'}]}))
        result = self.handle('/montage status', get=get)
        self.assertIn('failure', result)
        self.assertIn('/actions/runs/7', result)
        self.assertNotIn('attacker', result)
        self.post.assert_not_called()
    def test_durable_claim_blocks_duplicate_crash_and_rerun(self):
        api = Mock(side_effect=[Mock(status_code=201), Mock(status_code=422)])
        self.assertTrue(control.claim_request('tg-44', 'fake', 'a'*40, api))
        self.assertFalse(control.claim_request('tg-44', 'fake', 'a'*40, api))
        self.assertEqual(api.call_args.kwargs['json']['ref'], 'refs/tags/openmontage-requests/tg-44')
    def test_claim_injection_timeout_and_permission_failure(self):
        api = Mock()
        for bad in ['../../main', 'tg-1;echo', 'manual-abc', 'tg-1\n']:
            with self.assertRaises(ValueError): control.claim_request(bad, 'fake', 'a'*40, api)
        api.assert_not_called()
        api.side_effect = requests.Timeout('secret')
        with self.assertRaisesRegex(RuntimeError, 'unklar'): control.claim_request('tg-1', 'fake', 'a'*40, api)
        api.side_effect = None
        api.return_value.status_code = 403
        with self.assertRaisesRegex(RuntimeError, 'HTTP 403'): control.claim_request('tg-1', 'fake', 'a'*40, api)


class WorkflowTests(unittest.TestCase):
    def doc(self):
        return yaml.load((ROOT / '.github/workflows/openmontage.yml').read_text(), Loader=yaml.BaseLoader)
    def test_no_schedule_or_pr_secrets_or_untrusted_ref(self):
        doc = self.doc()
        self.assertEqual(set(doc['on']), {'workflow_dispatch'})
        self.assertEqual(doc['jobs']['run']['if'], "github.ref == 'refs/heads/main'")
        self.assertEqual(doc['concurrency']['cancel-in-progress'], 'false')
        steps = doc['jobs']['run']['steps']
        checkout = next(s for s in steps if s.get('with', {}).get('repository') == 'calesthio/OpenMontage')
        self.assertEqual(checkout['with']['ref'], runtime.PIN['revision'])
        self.assertEqual(checkout['with']['persist-credentials'], 'false')
        self.assertNotIn('${{ inputs.', '\n'.join(s.get('run', '') for s in steps))
    def test_secrets_scoped_inventory_only_and_gemini_alias(self):
        steps = self.doc()['jobs']['run']['steps']
        diag = next(s for s in steps if 'Secret-Verfügbarkeit' in s.get('name', ''))
        self.assertEqual(set(diag['env']), set(runtime.KEYS))
        self.assertIn('secrets.GEMINI_API_KEY', diag['env']['GOOGLE_API_KEY'])
        for step in steps:
            if step is not diag:
                self.assertFalse(set(runtime.KEYS) & set(step.get('env', {})))
    def test_inventory_is_boolean_not_credentials(self):
        report = runtime.key_inventory({'PEXELS_API_KEY': 'SENSITIVE_VALUE', 'FAL_KEY': ' '})
        self.assertTrue(report['PEXELS_API_KEY'])
        self.assertFalse(report['FAL_KEY'])
        self.assertNotIn('SENSITIVE_VALUE', json.dumps(report))
    def test_runtime_cannot_inherit_secrets(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runtime, 'BASE', Path(tmp)), patch.dict(os.environ, {
                'OPENAI_API_KEY': 'secret', 'GITHUB_TOKEN': 'token', 'TELEGRAM_BOT_TOKEN': 'bot'}):
            env = runtime.local_env()
            self.assertNotIn('OPENAI_API_KEY', env)
            self.assertNotIn('GITHUB_TOKEN', env)
            self.assertNotIn('TELEGRAM_BOT_TOKEN', env)
            self.assertTrue(env['npm_config_cache'].startswith(tmp))
    def test_artifacts_are_allowlisted_not_env_or_private_media(self):
        steps = self.doc()['jobs']['run']['steps']
        upload = next(s for s in steps if s.get('uses', '').startswith('actions/upload-artifact'))
        self.assertEqual(upload['with']['path'].splitlines(), [
            'integrations/openmontage/.runtime/diagnose.json',
            'integrations/openmontage/.runtime/plan.json',
            'integrations/openmontage/upstream/projects/demos/renders/code-to-screen.mp4'])
    def test_diagnose_workflow_never_runs_demo_implicitly(self):
        step = next(s for s in self.doc()['jobs']['run']['steps'] if s.get('run', '').endswith('runtime.py demo'))
        self.assertEqual(step['if'], "inputs.mode == 'demo'")

if __name__ == '__main__': unittest.main()
