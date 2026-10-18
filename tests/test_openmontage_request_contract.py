import json
import unittest
from integrations.openmontage.request_contract import build_request, load_request, MontageRequestError


class MontageRequestContractTests(unittest.TestCase):
    def test_valid_request(self):
        payload = build_request(request_id="tg-42", prompt="MotoGP News", owner_chat="owner")
        self.assertEqual(load_request(json.dumps(payload).encode(), expected_request_id="tg-42"), payload)
        self.assertNotIn('"owner_chat":', json.dumps(payload))

    def test_wrong_request_id(self):
        payload = build_request(request_id="tg-42", prompt="MotoGP", owner_chat="owner")
        with self.assertRaises(MontageRequestError):
            load_request(json.dumps(payload).encode(), expected_request_id="tg-43")

    def test_missing_prompt(self):
        with self.assertRaises(MontageRequestError):
            build_request(request_id="tg-42", prompt=" ", owner_chat="owner")

    def test_replay_state_rejected(self):
        payload = build_request(request_id="tg-42", prompt="MotoGP", owner_chat="owner")
        payload["state"] = "DONE"
        with self.assertRaises(MontageRequestError):
            load_request(json.dumps(payload).encode(), expected_request_id="tg-42")


if __name__ == "__main__":
    unittest.main()
