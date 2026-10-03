import unittest
from content_factory_container_readiness import guarded_container_dispatch, ReadinessError

class ReadinessTests(unittest.TestCase):
    def test_wake_then_dispatch_once(self):
        seen = []
        def probe():
            seen.append("probe")
            return (len(seen) > 1, 200 if len(seen) > 1 else 503)
        def post():
            seen.append("post")
            return 202
        result = guarded_container_dispatch(authorized=True, consented=True,
            probe=probe, dispatch_once=post)
        self.assertEqual(result.status, "ACCEPTED_NOT_COMPLETED")
        self.assertEqual(seen, ["probe", "probe", "post"])
    def test_denied_never_probes(self):
        with self.assertRaises(PermissionError):
            guarded_container_dispatch(authorized=False, consented=True,
                probe=lambda: self.fail("probed"), dispatch_once=lambda: self.fail("posted"))
    def test_not_ready_never_posts(self):
        with self.assertRaises(ReadinessError):
            guarded_container_dispatch(authorized=True, consented=True,
                probe=lambda: (False, 503), dispatch_once=lambda: self.fail("posted"))
    def test_429_probe_stops(self):
        with self.assertRaises(ReadinessError) as raised:
            guarded_container_dispatch(authorized=True, consented=True,
                probe=lambda: (False, 429), dispatch_once=lambda: self.fail("posted"))
        self.assertEqual(raised.exception.status, 429)
    def test_422_post_never_retries(self):
        calls = []
        def post():
            calls.append(1)
            return 422
        with self.assertRaises(ReadinessError):
            guarded_container_dispatch(authorized=True, consented=True,
                probe=lambda: (True, 200), dispatch_once=post)
        self.assertEqual(len(calls), 1)
    def test_ambiguous_post_never_retries(self):
        calls = []
        def post():
            calls.append(1)
            raise TimeoutError()
        with self.assertRaises(ReadinessError) as raised:
            guarded_container_dispatch(authorized=True, consented=True,
                probe=lambda: (True, 200), dispatch_once=post)
        self.assertEqual(raised.exception.stage, "dispatch_ambiguous")
        self.assertEqual(len(calls), 1)
if __name__ == "__main__":
    unittest.main()
