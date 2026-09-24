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
     self.assertIn("Bereits gesendet (reply_id: reply-1)",ie.telegram_command(f"antwort {ticket}"))
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

 def test_sent_is_terminal(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"):
    e=ie.ingest({"event_id":"sent","text":"Hi","reply_draft":"Antwort"})
    items=ie._queue();items[0]["status"]="SENT";items[0]["reply_id"]="reply-terminal";ie._save(items)
    with patch.object(ie,"send_reply") as send:
     result=ie.telegram_command("antwort "+e["ticket_id"])
     self.assertIn("Bereits gesendet (reply_id: reply-terminal)",result)
     send.assert_not_called()

 def test_parallel_lock_blocks_second_call(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"), patch.object(ie,"LOCK_DIR",r):
    e=ie.ingest({"event_id":"locked","text":"Hi","reply_draft":"Antwort"})
    acquired,lock=ie._acquire_ticket_lock(e["ticket_id"],"run-1");self.assertTrue(acquired)
    try:
     with patch.object(ie,"send_reply") as send:
      result=ie.telegram_command("antwort "+e["ticket_id"],run_id="run-2")
      self.assertIn("Verarbeitung läuft bereits",result);send.assert_not_called()
    finally:ie._release_ticket_lock(lock)

 def test_send_failure_keeps_approved_state(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"):
    e=ie.ingest({"event_id":"fail","text":"Frage?","reply_draft":"Antwort"})
    with patch.object(ie,"send_reply",side_effect=RuntimeError("API down")):
     result=ie.telegram_command("antwort "+e["ticket_id"])
    self.assertIn("Senden fehlgeschlagen",result)
    self.assertIn("SEND_APPROVED",ie.telegram_command("info "+e["ticket_id"]))

 def test_ingest_generates_reply_draft_and_ticket_contains_it(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"), patch.object(ie,"quick_chat",return_value="Danke dir! Gute Fahrt."):
    (r/"m.md").write_text("# Instagram Community Memory\n\n- früher | @rider | comment | LOB | Media: 1\n",encoding="utf-8")
    e=ie.ingest({"event_id":"draft","username":"rider","text":"Mega!","media_id":"42"})
    self.assertEqual(e["reply_draft"],"Danke dir! Gute Fahrt.")
    ticket=ie.telegram_ticket(e)
    self.assertIn("Kommentar: Mega!",ticket)
    self.assertIn("Vorschlag: Danke dir! Gute Fahrt.",ticket)

 def test_ingest_survives_llm_failure_without_draft(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with patch.object(ie,"MEMORY_FILE",r/"m.md"), patch.object(ie,"QUEUE_FILE",r/"q.jsonl"), patch.object(ie,"SEEN_FILE",r/"s.txt"), patch.object(ie,"quick_chat",side_effect=RuntimeError("LLM down")):
    e=ie.ingest({"event_id":"draft-fail","username":"rider","text":"Welche Reifen?","media_id":"42"})
    self.assertIsNone(e["reply_draft"])
    self.assertEqual(ie._queue()[0]["ticket_id"],e["ticket_id"])
    self.assertIn("Kein Vorschlag verfügbar – bitte ändern nutzen",ie.telegram_ticket(e))

if __name__=="__main__":
 unittest.main()
