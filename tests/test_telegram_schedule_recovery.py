"""GitHub-only wakeups, read-only diagnostics and persisted morning dedupe."""
import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import yaml
import telegram_morning as morning

ROOT = Path(__file__).resolve().parents[1]

def workflow(name):
    return yaml.load((ROOT / '.github/workflows' / name).read_text(), Loader=yaml.BaseLoader)

class MorningRecovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = Path(self.tmp.name) / 'session.md'
        self.posts = [dict(number='1', title='Tour', hook='Wohin?', platform='Instagram',
                           description='Deine Route', source='https://example.com',
                           full_text='Titel: Tour\nInstagram-Caption:\nDeine Route')]
        self.patches = [patch.object(morning, 'SESSION_FILE', self.session),
                       patch.object(morning, 'load_latest_posts', return_value=self.posts)]
        for p in self.patches: p.start()
    def tearDown(self):
        for p in reversed(self.patches): p.stop()
        self.tmp.cleanup()
    def test_producer_then_cron_sends_once_and_preserves_session(self):
        with patch.object(morning, 'send_message') as send:
            morning.main()
            original = self.session.read_bytes()
            morning.main()
        send.assert_called_once()
        self.assertEqual(self.session.read_bytes(), original)
        self.assertIn('Plan-Fingerprint:', original.decode())
    def test_changed_plan_is_sent(self):
        with patch.object(morning, 'send_message') as send:
            morning.main()
            self.posts[0]['full_text'] = 'Neue belegte Tour-Idee'
            morning.main()
        self.assertEqual(send.call_count, 2)
    def test_failed_send_is_not_marked_delivered(self):
        with patch.object(morning, 'send_message', side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError): morning.main()
        self.assertFalse(self.session.exists())
        with patch.object(morning, 'send_message') as send: morning.main()
        send.assert_called_once()
    def test_legacy_session_does_not_resend_same_drafts(self):
        morning.save_session(self.posts)
        self.session.write_text('\n'.join(line for line in self.session.read_text().splitlines()
                                         if not line.startswith('Plan-Fingerprint:')))
        with patch.object(morning, 'send_message') as send: morning.main()
        send.assert_not_called()
    def test_no_posts_no_send_or_session(self):
        self.posts.clear()
        with patch.object(morning, 'send_message') as send: morning.main()
        send.assert_not_called()
        self.assertFalse(self.session.exists())
    def test_racing_separation_unchanged(self):
        self.assertTrue(morning._is_racing('MotoGP Bagnaia Pole'))
        self.assertFalse(morning._is_racing('Gemeinsame Motorradtour'))

class WorkflowRecovery(unittest.TestCase):
    def test_safe_main_only_serial_wakeups(self):
        receive = workflow('telegram-receive.yml')
        self.assertEqual(receive['on']['schedule'], [{'cron': '2-57/5 * * * *'}])
        self.assertEqual(receive['on']['workflow_run']['workflows'],
                         ['Telegram Morning Approval', 'MotoGP Content Agency', 'Daily Telegram Digest'])
        for name, job in [('telegram-receive.yml', 'receive-approval'),
                          ('telegram-morning.yml', 'send-approval-request')]:
            doc = workflow(name)
            trigger = doc['on']['workflow_run']
            self.assertEqual(trigger['branches'], ['main'])
            self.assertEqual(trigger['types'], ['completed'])
            self.assertNotIn(doc['name'], trigger['workflows'])
            self.assertEqual(doc['concurrency']['cancel-in-progress'], 'false')
            cfg = doc['jobs'][job]
            for condition in ["conclusion == 'success'", "head_branch == 'main'",
                              'head_repository.full_name == github.repository']:
                self.assertIn(condition, cfg['if'])
            self.assertLessEqual(int(cfg['timeout-minutes']), 10)
            checkout = next(s for s in cfg['steps'] if s.get('uses', '').startswith('actions/checkout@'))
            self.assertEqual(checkout['with']['ref'], 'main')
        self.assertEqual(workflow('telegram-morning.yml')['on']['workflow_run']['workflows'],
                         ['Generate Daily Content Idea'])
    def test_diagnostics_cannot_consume_or_send(self):
        doc = workflow('telegram-receive.yml')
        steps = doc['jobs']['receive-approval']['steps']
        diag = next(s for s in steps if s['name'].startswith('Telegram-Verbindung'))
        script = diag['run'].split("python - <<'PYTHON'\n", 1)[1].rsplit('\nPYTHON', 1)[0]
        tree = ast.parse(script)
        methods = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Name) and n.func.id == '_request']
        self.assertEqual(methods, ['getMe', 'getWebhookInfo'])
        self.assertIn('from None', script)
        for title in ['Route Telegram command', 'Commit Telegram results']:
            step = next(s for s in steps if s['name'] == title)
            self.assertEqual(step['if'], "github.event_name != 'workflow_dispatch' || !inputs.diagnose_only")

class LiveDiagnosticContract(unittest.TestCase):
    def script(self):
        steps = workflow('telegram-receive.yml')['jobs']['receive-approval']['steps']
        diag = next(s for s in steps if s['name'].startswith('Telegram-Verbindung'))
        return diag['run'].split("python - <<'PYTHON'\n", 1)[1].rsplit('\nPYTHON', 1)[0]
    def test_success_only_reads_connection_metadata(self):
        with patch('telegram_bot._request', side_effect=[{'ok': True}, {'result': {'url': ''}}]) as request:
            exec(self.script(), {})
        self.assertEqual([c.args[0] for c in request.call_args_list], ['getMe', 'getWebhookInfo'])
    def test_webhook_conflict_blocks_without_changing_webhook(self):
        with patch('telegram_bot._request', side_effect=[{}, {'result': {'url': 'https://example.com'}}]) as request:
            with self.assertRaisesRegex(SystemExit, 'Polling-Konflikt'): exec(self.script(), {})
        self.assertEqual(request.call_count, 2)
    def test_error_does_not_expose_credentials(self):
        with patch('telegram_bot._request', side_effect=RuntimeError('PRIVATE_TOKEN')):
            with self.assertRaises(SystemExit) as caught: exec(self.script(), {})
        self.assertNotIn('PRIVATE_TOKEN', str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)

if __name__ == '__main__': unittest.main()
