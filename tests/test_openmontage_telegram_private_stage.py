import unittest
from scripts.openmontage_control import handle


class Storage:
    def __init__(self):
        self.data = {}

    def put_object(self, *, Key, Body, ContentType):
        self.data[Key] = Body


class TelegramPrivateStagingTests(unittest.TestCase):
    def test_stage_without_dispatch(self):
        storage = Storage()
        result = handle("/montage planen MotoGP Türkçe", 42, "owner", "owner",
                        request_storage=storage,
                        post=lambda *a, **kw: self.fail("must not dispatch"))
        self.assertIn("NICHT gestartet", result)
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
