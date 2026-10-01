import unittest
from unittest.mock import patch
from scripts import ai_central_direct_provider_probe as p

class FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self.body = body or {"model": "exact-model", "choices": [{"message": {"content": "READY"}}]}
    def json(self):
        return self.body

class CandidateAuditTests(unittest.TestCase):
    def test_deny_unknown_paid_or_unconfirmed_route_before_network(self):
        for name in ("claude", "grok", "openrouter", "nvidia", "../gemini"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "UNLISTED_PROVIDER"):
                p.plan(name, {})
        for name in ("gemini", "groq"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "ACCOUNT_FREE_TIER_NOT_CONFIRMED"):
                p.one_probe(name, {}, transport=lambda *a, **k: self.fail("network forbidden"))
            c=p.CANDIDATES[name]
            with self.assertRaisesRegex(ValueError, "PROVIDER_KEY_MISSING"):
                p.one_probe(name, {c["confirmed"]: "true"}, transport=lambda *a, **k: self.fail("network forbidden"))
            with self.assertRaisesRegex(ValueError, "ACCOUNT_FREE_TIER_NOT_CONFIRMED"):
                p.one_probe(name, {c["confirmed"]: "TRUE", c["key"]: "dummy"}, transport=lambda *a, **k: self.fail("network forbidden"))

    def test_exact_pinned_routes_one_request_and_no_private_prompt(self):
        for name,c in p.CANDIDATES.items():
            with self.subTest(name=name):
                seen=[]
                def fake(url, **kw):
                    seen.append((url, kw))
                    return FakeResponse()
                result=p.one_probe(name, {c["confirmed"]:"true",c["key"]:"test-secret"}, transport=fake)
                self.assertEqual(result["status"], "ANSWER")
                self.assertEqual(len(seen),1)
                self.assertEqual(seen[0][0],c["url"])
                self.assertEqual(seen[0][1]["json"]["model"],c["model"])
                self.assertEqual(seen[0][1]["json"]["max_tokens"],40)
                self.assertNotIn("test-secret",str(result))
                self.assertNotIn("answer",str(result).lower())

    def test_http_rate_limit_not_marked_success_or_retried(self):
        c=p.CANDIDATES["groq"]
        calls=[]
        def fake(*a, **k):
            calls.append(1)
            return FakeResponse(429)
        result=p.one_probe("groq",{c["confirmed"]:"true",c["key"]:"dummy"},transport=fake)
        self.assertEqual((result["status"],result["http_status"]),("HTTP_ERROR",429))
        self.assertEqual(len(calls),1)

    def test_malformed_or_empty_response_does_not_pass(self):
        c=p.CANDIDATES["gemini"]
        for body in ({"choices":[]},{"choices":[{"message":{"content":""}}]}, {"model":12,"choices":[]}):
            with self.subTest(body=body):
                result=p.one_probe("gemini",{c["confirmed"]:"true",c["key"]:"dummy"},
                                   transport=lambda *a,**k: FakeResponse(body=body))
                self.assertEqual(result["status"],"INVALID_RESPONSE")

if __name__=="__main__":
    unittest.main()
