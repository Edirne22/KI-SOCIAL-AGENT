import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import instagram_engagement as ie

class InstagramEngagementTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(ie.classify("Welche Reifen fährst du?"), "FRAGE")
        self.assertEqual(ie.classify("Mega, sieht super aus"), "LOB")
        self.assertEqual(ie.classify("KURS"), "TRIGGER")

    def test_dedup_and_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(ie, "MEMORY_FILE", root/"community.md"),                  patch.object(ie, "QUEUE_FILE", root/"queue.jsonl"),                  patch.object(ie, "SEEN_FILE", root/"seen.txt"):
                payload = {"event_id":"abc","username":"rider","text":"Welche Reifen?","media_id":"42"}
                first = ie.ingest(payload)
                second = ie.ingest(payload)
                self.assertEqual(first["status"], "PENDING_APPROVAL")
                self.assertEqual(second["status"], "DUPLICATE")
                self.assertIn("@rider", (root/"community.md").read_text(encoding="utf-8"))

    def test_no_guessing_from_empty_event(self):
        event = ie.normalize_event({"event_id":"x","event_type":"profile_view"})
        self.assertEqual(event["category"], "UNSICHER")
        self.assertEqual(event["username"], "")

if __name__ == "__main__":
    unittest.main()
