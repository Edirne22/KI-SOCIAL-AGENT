import io
import unittest
from integrations.openmontage.private_request_store import get_request, put_request, request_key
from integrations.openmontage.request_contract import MontageRequestError


class MemoryStorage:
    def __init__(self):
        self.data = {}

    def put_object(self, *, Key, Body, ContentType):
        assert ContentType == "application/json"
        self.data[Key] = Body

    def get_object(self, *, Key):
        return {"Body": io.BytesIO(self.data[Key])}


class PrivateRequestStoreTests(unittest.TestCase):
    def test_roundtrip_without_public_url(self):
        storage = MemoryStorage()
        key = put_request(storage, request_id="tg-12", prompt="WorldSBK Türkçe", owner_chat="owner-private")
        self.assertEqual(key, "openmontage/requests/tg-12.json")
        self.assertNotIn(b"owner-private", storage.data[key])
        request = get_request(storage, request_id="tg-12")
        self.assertEqual(request["prompt"], "WorldSBK Türkçe")

    def test_mismatch_fails_closed(self):
        storage = MemoryStorage()
        put_request(storage, request_id="tg-12", prompt="MotoGP", owner_chat="owner")
        storage.data[request_key("tg-13")] = storage.data[request_key("tg-12")]
        with self.assertRaises(MontageRequestError):
            get_request(storage, request_id="tg-13")

    def test_path_traversal_rejected(self):
        with self.assertRaises(MontageRequestError):
            request_key("../bad")


if __name__ == "__main__":
    unittest.main()
