import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import instagram_engagement as ie
class Tests(unittest.TestCase):
 def test_commands(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"),patch.object(ie,"QUEUE_FILE",r/"q.jsonl"),patch.object(ie,"SEEN_FILE",r/"s.txt"):
    e=ie.ingest({"event_id":"abc","username":"rider","text":"Welche Reifen?","media_id":"42","reply_draft":"Michelin."});ticket=e["ticket_id"]
    self.assertIn("FRAGE",ie.telegram_command(f"info {ticket}"));self.assertIn("@rider",ie.telegram_command(f"memory {ticket}"));self.assertIn("SEND_APPROVED",ie.telegram_command(f"antwort {ticket}"))
 def test_change_ignore_no_guess(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"),patch.object(ie,"QUEUE_FILE",r/"q.jsonl"),patch.object(ie,"SEEN_FILE",r/"s.txt"):
    e=ie.ingest({"event_id":"xyz","text":"Hi"});self.assertEqual(e["username"],"");self.assertIn("SEND_APPROVED",ie.telegram_command(f"ändern {e['ticket_id']} Neu"));self.assertIn("IGNORED",ie.telegram_command(f"ignorieren {e['ticket_id']}"))
if __name__=="__main__":unittest.main()
