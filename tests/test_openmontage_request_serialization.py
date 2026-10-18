import json
import unittest
from integrations.openmontage.request_contract import serialize_request, load_request, MontageRequestError


class RequestSerializationTests(unittest.TestCase):
    def test_roundtrip_with_nonascii_prompt(self):
        data = serialize_request(request_id="tg-123", prompt="MotoGP Türkçe – 90 Sekunden", owner_chat="private-chat")
        result = load_request(data, expected_request_id="tg-123")
        self.assertEqual(result["prompt"], "MotoGP Türkçe – 90 Sekunden")
        self.assertNotIn(b"private-chat", data)
        self.assertEqual(result["state"], "PENDING")

    def test_reject_invalid_request_id(self):
        with self.assertRaises(MontageRequestError):
            serialize_request(request_id="../../oops", prompt="MotoGP", owner_chat="private-chat")


if __name__ == "__main__":
    unittest.main()
