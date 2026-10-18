import unittest
from unittest.mock import Mock
from scripts.openmontage_control import handle


class Storage:
    def __init__(self):
        self.data = {}

    def put_object(self, *, Key, Body, ContentType):
        self.data[Key] = Body


class TelegramPrivateStagingTests(unittest.TestCase):
    def test_stage_then_dispatch(self):
        storage = Storage()
        sent = []
        def dispatch(url, **kwargs):
            self.assertIn("openmontage.yml/dispatches", url)
            self.assertIn("openmontage/requests/tg-42.json", storage.data)
            self.assertEqual(kwargs["json"]["inputs"], {"mode": "planen", "request_id": "tg-42"})
            sent.append(True)
            return Mock(status_code=204)
        with unittest.mock.patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            result = handle("/montage planen MotoGP Türkçe", 42, "owner", "owner", request_storage=storage, post=dispatch)
        self.assertIn("angenommen", result)
        self.assertEqual(sent, [True])
        self.assertIn("tg-42", result)
        self.assertIn("openmontage/requests/tg-42.json", storage.data)

    def test_missing_storage_fails_closed(self):
        result = handle("/montage erstellen MotoGP", 43, "owner", "owner")
        self.assertIn("NICHT AUSFÜHRBAR", result)

    def test_unauthorized_cannot_stage(self):
        with self.assertRaises(PermissionError):
            handle("/montage planen MotoGP", 44, "intruder", "owner", request_storage=Storage())


if __name__ == "__main__":
    unittest.main()
