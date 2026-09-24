import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import instagram_engagement as ie

class Tests(unittest.TestCase):
 def test_commands(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"):
    e=ie.ingest({"event_id":"abc","username":"rider","text":"Welche Reifen?","media_id":"42","reply_draft":"Michelin."})
    ticket=e["ticket_id"]
    self.assertIn("FRAGE",ie.telegram_command(f"info {ticket}"))
    self.assertIn("@rider",ie.telegram_command(f"memory {ticket}"))
    with patch.object(ie,"send_reply",return_value="reply-1") as send:
     self.assertIn("SENT",ie.telegram_command(f"antwort {ticket}"))
     send.assert_called_once_with("abc","Michelin.")
     self.assertIn("SENT",ie.telegram_command(f"antwort {ticket}"))
     send.assert_called_once()

 def test_change_ignore_no_guess(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"):
    e=ie.ingest({"event_id":"xyz","text":"Hi"})
    self.assertEqual(e["username"],"")
    with patch.object(ie,"send_reply",return_value="reply-2") as send:
     self.assertIn("SENT",ie.telegram_command(f"ändern {e['ticket_id']} Neu"))
     send.assert_called_once_with("xyz","Neu")
    e2=ie.ingest({"event_id":"ignore","text":"Hi"})
    self.assertIn("IGNORED",ie.telegram_command(f"ignorieren {e2['ticket_id']}"))

 def test_send_failure_keeps_approved_state(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"):
    e=ie.ingest({"event_id":"fail","text":"Frage?","reply_draft":"Antwort"})
    with patch.object(ie,"send_reply",side_effect=RuntimeError("API down")):
     result=ie.telegram_command("antwort "+e["ticket_id"])
    self.assertIn("Senden fehlgeschlagen",result)
    self.assertIn("SEND_APPROVED",ie.telegram_command("info "+e["ticket_id"]))

if __name__=="__main__":
 unittest.main()
