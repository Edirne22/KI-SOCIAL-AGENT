import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("r2_review", ROOT / "scripts/openchatcut_review_r2.py")
r2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r2)

class FakeR2:
    def __init__(self):
        self.calls = []
    def upload_file(self, *args, **kwargs):
        self.calls.append((args, kwargs))

class R2ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = pathlib.Path(self.tmp.name) / "openchatcut-multi-review.json"
        self.path.write_text(json.dumps({"schema":"OPENCHATCUT-ADVISORY-REVIEW-V1","advisory_only":True,
            "results":[{"provider":"nvidia","state":"SKIPPED_NO_KEY"}],"peer_review":[]}), encoding="utf-8")
        self.client = FakeR2()
    def test_upload_is_scoped_and_private(self):
        key = r2.upload_report(self.path,client=self.client,bucket="private-media",run_id="123456")
        self.assertEqual(key,"ai-diagnostics/openchatcut/run-123456/multi-model-review.json")
        self.assertEqual(self.client.calls[0][0][1:3],("private-media",key))
        self.assertEqual(self.client.calls[0][1]["ExtraArgs"],{"ContentType":"application/json"})
    def test_rejects_bad_schema_and_never_uploads(self):
        self.path.write_text('{"schema":"other","advisory_only":true}')
        with self.assertRaises(ValueError):
            r2.upload_report(self.path,client=self.client,bucket="private-media",run_id="123")
        self.assertFalse(self.client.calls)
    def test_rejects_unsafe_run_id(self):
        with self.assertRaises(ValueError):
            r2.upload_report(self.path,client=self.client,bucket="private-media",run_id="../../etc")
        self.assertFalse(self.client.calls)
    def test_rejects_unexpected_filename(self):
        another=self.path.with_name("unreviewed.json")
        another.write_text(self.path.read_text())
        with self.assertRaises(ValueError):
            r2.upload_report(another,client=self.client,bucket="private-media",run_id="123")
        self.assertFalse(self.client.calls)

if __name__ == "__main__":
    unittest.main()
