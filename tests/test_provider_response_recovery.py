"""Offline provider-chain regression; no API keys or network calls required."""
import contextlib
import io
import unittest
from unittest.mock import patch

import llm_client
import llm_router


class Response:
    def __init__(self, payload=None, status=200, invalid_json=False):
        self.payload = payload
        self.status_code = status
        self.ok = 200 <= status < 300
        self.headers = {}
        self.text = "PRIVATE_PROVIDER_BODY"
        self.invalid_json = invalid_json

    def json(self):
        if self.invalid_json:
            raise ValueError("PRIVATE_PROVIDER_BODY")
        return self.payload


def chat(text):
    return {"choices": [{"message": {"content": text}}]}


class ResponseRecoveryTests(unittest.TestCase):
    def setUp(self):
        llm_client._PROVIDER_COOLDOWNS.clear()
        self.env = patch.dict("os.environ", {
            "AGNES_API_KEY": "test-agnes", "GEMINI_API_KEY": "test-gemini",
            "NVIDIA_API_KEY": "test-nvidia", "OPENROUTER_API_KEY": "test-openrouter",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(llm_client._PROVIDER_COOLDOWNS.clear)

    def test_racing_bad_envelopes_reach_configured_fallback(self):
        for bad in (None, [], {}, {"choices": None}, chat(None), chat(""), chat("  "), chat([])):
            with self.subTest(payload=bad):
                responses = [Response(bad), Response({"candidates": [{"content": {"parts": [{"text": "OK"}]}}]})]
                with patch.object(llm_client.requests, "request", side_effect=responses) as request:
                    self.assertEqual(llm_client.generate("racing_semantic_qm", "synthetic"), "OK")
                    self.assertEqual(request.call_count, 2)

    def test_racing_non_json_response_reaches_fallback(self):
        good = {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
        with patch.object(llm_client.requests, "request", side_effect=[Response(invalid_json=True), Response(good)]) as request:
            self.assertEqual(llm_client.generate("racing_semantic_qm", "synthetic"), "OK")
            self.assertEqual(request.call_count, 2)

    def test_all_empty_racing_responses_fail_closed_in_three_calls(self):
        responses = [Response(chat("")), Response({"candidates": [{"content": {"parts": [{"text": " "}]}}]}), Response(chat(None))]
        with patch.object(llm_client.requests, "request", side_effect=responses) as request:
            with self.assertRaises(llm_client.ProviderUnavailableError):
                llm_client.generate("racing_semantic_qm", "synthetic")
            self.assertEqual(request.call_count, 3)

    def test_reasoning_rejects_bad_content_and_uses_next_provider(self):
        for bad in (None, [], {"choices": None}, chat(" "), chat([{"text": "untrusted shape"}]), chat({"text": "wrong"})):
            with self.subTest(payload=bad):
                worker = llm_router.LLMRouter()
                with patch.object(llm_router.requests, "post", side_effect=[Response(bad), Response(chat("OK"))]) as request:
                    self.assertEqual(worker.chat([{"role": "user", "content": "synthetic"}], "reasoning"), "OK")
                    self.assertEqual(request.call_count, 2)

    def test_reasoning_non_json_reaches_next_provider(self):
        worker = llm_router.LLMRouter()
        with patch.object(llm_router.requests, "post", side_effect=[Response(invalid_json=True), Response(chat("OK"))]):
            self.assertEqual(worker.chat([], "reasoning"), "OK")

    def test_reasoning_errors_do_not_log_provider_bodies(self):
        worker = llm_router.LLMRouter()
        output = io.StringIO()
        with patch.object(llm_router.requests, "post", return_value=Response(status=401)), contextlib.redirect_stdout(output):
            with self.assertRaises(RuntimeError):
                worker.chat([], "reasoning")
        self.assertNotIn("PRIVATE_PROVIDER_BODY", output.getvalue())
        self.assertIn("401", output.getvalue())

    def test_valid_response_returns_without_extra_provider_call(self):
        with patch.object(llm_client.requests, "request", return_value=Response(chat("OK"))) as request:
            self.assertEqual(llm_client.generate("racing_semantic_qm", "synthetic"), "OK")
            self.assertEqual(request.call_count, 1)

    def test_racing_http_errors_do_not_expose_provider_bodies(self):
        with patch.object(llm_client.requests, "request", return_value=Response(status=401)):
            with self.assertRaises(llm_client.ProviderUnavailableError) as caught:
                llm_client.generate("racing_semantic_qm", "synthetic")
        self.assertNotIn("PRIVATE_PROVIDER_BODY", str(caught.exception))
        self.assertIn("401", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
