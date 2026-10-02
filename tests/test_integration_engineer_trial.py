"""Offline controls: malicious source never gains execution."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from integration_engineer_trial import extract_text, verify_source

VALID = ("def classify_machine(license_id, zero_cost, days_since_release):\n"
         "    return ('BLOCKED' if license_id not in ('MIT', 'Apache-2.0', 'BSD-3-Clause') or "
         "not zero_cost or days_since_release < 0 else "
         "'WATCH' if days_since_release > 365 else 'ELIGIBLE')\n")


class EngineerInterviewTests(unittest.TestCase):
    def test_good_sample_all_cases(self):
        self.assertEqual(verify_source(VALID)["behavior_cases"], 10)

    def test_opencode_text_stream(self):
        stream = json.dumps({"type": "text", "part": {"text": VALID}})
        self.assertEqual(extract_text(stream), VALID.strip())

    def test_missing_model_response_is_not_pass(self):
        with self.assertRaisesRegex(ValueError, "No valid"):
            extract_text('{"type":"metadata"}')

    def test_error_event_fails_closed(self):
        raw = json.dumps({"type": "error", "error": {"message": "provider limit"}})
        with self.assertRaisesRegex(ValueError, "error"):
            extract_text(raw)

    def test_import_prompt_injection_rejected(self):
        with self.assertRaises(ValueError):
            verify_source(VALID + "\nimport os\nos.system('echo hacked')\n")

    def test_calls_rejected(self):
        with self.assertRaises(ValueError):
            verify_source("def classify_machine(license_id, zero_cost, days_since_release):\n"
                          "    return __import__('os').system('true')\n")

    def test_file_write_rejected(self):
        with self.assertRaises(ValueError):
            verify_source("def classify_machine(license_id, zero_cost, days_since_release):\n"
                          "    return open('/tmp/pwned','w')\n")

    def test_wrong_behavior_rejected(self):
        with self.assertRaisesRegex(ValueError, "Incorrect"):
            verify_source("def classify_machine(license_id, zero_cost, days_since_release):\n"
                          "    return 'ELIGIBLE'\n")

    def test_misleading_license_rejected(self):
        with self.assertRaisesRegex(ValueError, "Incorrect"):
            verify_source("def classify_machine(license_id, zero_cost, days_since_release):\n"
                          "    return 'BLOCKED' if not zero_cost else 'ELIGIBLE'\n")

    def test_keyword_parameters_rejected(self):
        with self.assertRaises(ValueError):
            verify_source("def classify_machine(license_id, zero_cost=True, days_since_release=0):\n"
                          "    return 'ELIGIBLE'\n")


if __name__ == "__main__":
    unittest.main()
