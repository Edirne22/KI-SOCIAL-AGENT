import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import facebook_engagement as fe

class FacebookEngagementTests(unittest.TestCase):
 def test_commands_and_memory(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(fe,"MEMORY_FILE",r/"m.md"),patch.object(fe,"QUEUE_FILE",r/"q.jsonl"),patch.object(fe,"SEEN_FILE",r/"s.txt"):
    e=fe.ingest({"event_id":"abc","actor_name":"Rider","text":"Welche Reifen?","post_id":"42","reply_draft":"Michelin Power GP."})
    self.assertTrue(e["ticket_id"].startswith("FB-"))
    self.assertIn("FRAGE",fe.telegram_command(f"info {e['ticket_id']}"))
    self.assertIn("Rider",fe.telegram_command(f"memory {e['ticket_id']}"))
    self.assertIn("SEND_APPROVED",fe.telegram_command(f"antwort {e['ticket_id']}"))
 def test_change_ignore_and_no_guess(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(fe,"MEMORY_FILE",r/"m.md"),patch.object(fe,"QUEUE_FILE",r/"q.jsonl"),patch.object(fe,"SEEN_FILE",r/"s.txt"):
    e=fe.ingest({"event_id":"xyz","text":"Hi"})
    self.assertEqual(e["actor_name"],"")
    self.assertIn("SEND_APPROVED",fe.telegram_command(f"ändern {e['ticket_id']} Neuer Text"))
    self.assertIn("IGNORED",fe.telegram_command(f"ignorieren {e['ticket_id']}"))

if __name__=="__main__":unittest.main()
