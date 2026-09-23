"""Instagram Engagement V1: Queue, Community-Memory und Telegram-Kommandos."""
from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
MEMORY_FILE=Path("memory/INSTAGRAM_COMMUNITY.md"); QUEUE_FILE=Path("memory/INSTAGRAM_ENGAGEMENT_QUEUE.jsonl"); SEEN_FILE=Path("memory/INSTAGRAM_ENGAGEMENT_SEEN.txt")
TRIGGERS={"kurs","info","link","mehr"}
def _clean(v:Any,limit:int=1000)->str:return re.sub(r"\s+"," ",str(v or "")).strip()[:limit]
def classify(text:str)->str:
 v=text.casefold().strip(); words=set(re.findall(r"[\wäöüß]+",v))
 if not v:return "UNSICHER"
 if words & TRIGGERS:return "TRIGGER"
 if "?" in v or words & {"wie","welche","welcher","wo","warum","was","wann","how","what","neden","nasıl"}:return "FRAGE"
 if words & {"danke","top","stark","super","mega","schön","nice","great","teşekkürler","harika"}:return "LOB"
 if words & {"schlecht","falsch","mist","unsinn","bad","yanlış"}:return "KRITIK"
 if len(v)>350 or v.count("http")>1:return "SPAM"
 return "UNSICHER"
def normalize_event(p:dict[str,Any])->dict[str,str]:
 eid=_clean(p.get("event_id") or p.get("id"),160); user=_clean(p.get("username"),100).lstrip("@"); txt=_clean(p.get("text")); media=_clean(p.get("media_id"),160); typ=_clean(p.get("event_type") or "comment",40).lower(); ts=_clean(p.get("timestamp"),80) or datetime.now(timezone.utc).isoformat()
 if not eid:eid=hashlib.sha256("|".join((typ,user,media,ts,txt)).encode()).hexdigest()[:32]
 ticket="IG-"+hashlib.sha256(eid.encode()).hexdigest()[:8].upper()
 return {"event_id":eid,"ticket_id":ticket,"event_type":typ,"username":user,"media_id":media,"text":txt,"timestamp":ts,"category":classify(txt),"status":"PENDING_APPROVAL","reply_draft":_clean(p.get("reply_draft"))}
def _queue():
 if not QUEUE_FILE.exists():return []
 return [json.loads(x) for x in QUEUE_FILE.read_text(encoding="utf-8").splitlines() if x.strip()]
def _save(items):
 QUEUE_FILE.parent.mkdir(parents=True,exist_ok=True); QUEUE_FILE.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in items),encoding="utf-8")
def ingest(p):
 e=normalize_event(p); seen=set(SEEN_FILE.read_text(encoding="utf-8").split()) if SEEN_FILE.exists() else set()
 if e["event_id"] in seen:return {**e,"status":"DUPLICATE"}
 items=_queue();items.append(e);_save(items);SEEN_FILE.parent.mkdir(parents=True,exist_ok=True)
 with SEEN_FILE.open("a",encoding="utf-8") as f:f.write(e["event_id"]+"\n")
 MEMORY_FILE.parent.mkdir(parents=True,exist_ok=True)
 if not MEMORY_FILE.exists():MEMORY_FILE.write_text("# Instagram Community Memory\n",encoding="utf-8")
 with MEMORY_FILE.open("a",encoding="utf-8") as f:f.write(f"\n- {e['timestamp']} | @{e['username'] or 'unbekannt'} | {e['event_type']} | {e['category']} | Media: {e['media_id'] or '-'}\n")
 return e
def telegram_command(command:str)->str:
 m=re.match(r"^\s*(antwort|ändern|ignorieren|info|memory)\s+(IG-[A-F0-9]{8})(?:\s+(.*))?\s*$",command,re.I)
 if not m:return "FEHLER: Befehl unbekannt."
 action,ticket,arg=m.group(1).casefold(),m.group(2).upper(),_clean(m.group(3));items=_queue();event=next((x for x in items if x.get("ticket_id")==ticket),None)
 if not event:return f"FEHLER: {ticket} nicht gefunden."
 if action=="info":return f"{ticket} | @{event.get('username') or 'unbekannt'} | {event['category']} | {event['status']} | {event.get('text','')}"
 if action=="memory":
  if not event.get("username"):return f"{ticket}: kein öffentlicher Accountname vorhanden."
  lines=MEMORY_FILE.read_text(encoding="utf-8").splitlines() if MEMORY_FILE.exists() else [];hits=[x for x in lines if f"@{event['username']} |" in x]
  return "\n".join(hits[-10:]) or f"{ticket}: keine früheren belegbaren Interaktionen."
 if action=="ignorieren":event["status"]="IGNORED"
 elif action=="ändern":
  if not arg:return "FEHLER: Nach 'ändern' fehlt der neue Text."
  event["reply_draft"]=arg;event["status"]="SEND_APPROVED"
 elif action=="antwort":
  if not event.get("reply_draft"):return "FEHLER: Kein Antwortvorschlag vorhanden."
  event["status"]="SEND_APPROVED"
 _save(items);return f"{ticket}: {event['status']}"
