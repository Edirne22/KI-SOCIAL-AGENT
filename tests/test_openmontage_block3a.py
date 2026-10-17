import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import openmontage_control as control


class Response:
    def __init__(self, status_code):
        self.status_code = status_code


class TelegramBridgeTests(unittest.TestCase):
    def test_command_parser(self):
        self.assertEqual(control.parse_command("/montage test starten"), "demo")
        self.assertEqual(control.parse_command("/montage diagnose"), "diagnose")
        self.assertEqual(control.parse_command("/montage status"), "status")
        self.assertIsNone(control.parse_command("/other test"))

    def test_reject_other_chat_without_dispatch(self):
        with self.assertRaises(PermissionError):
            control.handle("/montage test starten", 12, "wrong", "owner",
                           post=lambda *a, **kw: self.fail("unauthorized dispatch"))

    def test_explicit_demo_dispatch_once(self):
        calls = []
        def post(url, **kwargs):
            calls.append(kwargs["json"])
            return Response(204)
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
                state = Path(folder) / "requests.json"
                first = control.handle("/montage test starten", 42, "owner", "owner",
                                       state=state, post=post)
                second = control.handle("/montage test starten", 42, "owner", "owner",
                                        state=state, post=post)
        self.assertIn("angenommen", first)
        self.assertIn("bereits erfasst", second)
        self.assertEqual(calls, [{"ref": "main", "inputs": {"mode": "demo", "request_id": "tg-42"}}])

    def test_proposal_never_dispatches(self):
        result = control.handle("/montage test", 8, "owner", "owner",
                                post=lambda *a, **kw: self.fail("unexpected dispatch"))
        self.assertIn("Start nur", result)

    def test_failed_dispatch_not_retried(self):
        calls = []
        def post(*args, **kwargs):
            calls.append(1)
            return Response(403)
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
                state = Path(folder) / "requests.json"
                control.handle("/montage diagnose", 9, "owner", "owner", state=state, post=post)
                result = control.handle("/montage diagnose", 9, "owner", "owner", state=state, post=post)
        self.assertEqual(len(calls), 1)
        self.assertIn("bereits erfasst", result)


if __name__ == "__main__":
    unittest.main()
