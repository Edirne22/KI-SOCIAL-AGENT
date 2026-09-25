"""Instagram Engagement V1: Queue, Community-Memory und Telegram-Kommandos."""
from __future__ import annotations
import hashlib, json, os, re, time
from instagram_reply_adapter import send_reply
from llm_router import quick_chat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
MEMORY_FILE=Path("memory/INSTAGRAM_COMMUNITY.md"); QUEUE_FILE=Path("memory/INSTAGRAM_ENGAGEMENT_QUEUE.jsonl"); SEEN_FILE=Path("memory/INSTAGRAM_ENGAGEMENT_SEEN.txt")
HUMAN_PROTOCOL_FILE=Path("config/HUMAN_WRITING_PROTOCOL.md"); BBL_VOICE_FILE=Path("memory/MOTOGP_VOICE_RULES.md")
TRIGGERS={"kurs","info","link","mehr"}
LOCK_DIR=Path("memory"); LOCK_TTL_SECONDS=300
# Zustände: PENDING_APPROVAL/NEW -> SEND_APPROVED -> SENT (terminal); NEW -> IGNORED (terminal).
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
def _community_history(username:str)->str:
 if not username or not MEMORY_FILE.exists():return ""
 lines=MEMORY_FILE.read_text(encoding="utf-8").splitlines()
 return "\n".join(x for x in lines if f"@{username} |" in x)[-3000:]

def _style_context()->str:
 parts=[]
 for path,label in ((HUMAN_PROTOCOL_FILE,"HUMAN WRITING PROTOCOL"),(BBL_VOICE_FILE,"BÜLENTS BIKE LIFE VOICE")):
  try:content=path.read_text(encoding="utf-8").strip()
  except (FileNotFoundError,OSError):content=""
  if content:parts.append(f"--- {label} ---\n{content}")
 return "\n\n".join(parts)

def _generate_reply_draft(e:dict[str,str])->str|None:
 history=_community_history(e.get("username",""))
 style=_style_context()
 prompt=(
  "Erstelle genau einen kurzen Instagram-Antwortvorschlag für Bülent (1-2 Sätze).\n"
  "Sprache: Deutsch. Nur wenn der Kommentar Türkisch ist, antworte Türkisch. Bei unklarer Sprache Deutsch. "
  "Keine erfundenen Fakten, keine Versprechen, keine automatische Aktion. Nur den Antworttext ausgeben.\n"
  f"Klassifizierung: {e.get('category','UNSICHER')}\n"
  f"Kommentar: {e.get('text','')}\n"
  f"Community-Historie dieses Users: {history or 'keine belegbare frühere Interaktion'}\n"
  f"Verbindlicher Schreibstil:\n{style or 'keine zusätzlichen Stilregeln geladen'}"
 )
 try:
  draft=_clean(quick_chat(prompt,task_type="default"))
  return draft or None
 except Exception as exc:
  print(f"ENGAGEMENT DRAFT: KI nicht verfügbar: {exc}")
  return None
def telegram_ticket(e:dict[str,str])->str:
 draft=e.get("reply_draft") or "Kein Vorschlag verfügbar – bitte ändern nutzen"
 return (
  f"{e['ticket_id']} | @{e.get('username') or 'unbekannt'} | {e.get('category','UNSICHER')}\n"
  f"Kommentar: {e.get('text','')}\n"
  f"Vorschlag: {draft}"
 )

def ingest(p):
 e=normalize_event(p); seen=set(SEEN_FILE.read_text(encoding="utf-8").split()) if SEEN_FILE.exists() else set()
 if e["event_id"] in seen:return {**e,"status":"DUPLICATE"}
 if not e.get("reply_draft"):e["reply_draft"]=_generate_reply_draft(e)
 items=_queue();items.append(e);_save(items);SEEN_FILE.parent.mkdir(parents=True,exist_ok=True)
 with SEEN_FILE.open("a",encoding="utf-8") as f:f.write(e["event_id"]+"\n")
 MEMORY_FILE.parent.mkdir(parents=True,exist_ok=True)
 if not MEMORY_FILE.exists():MEMORY_FILE.write_text("# Instagram Community Memory\n",encoding="utf-8")
 with MEMORY_FILE.open("a",encoding="utf-8") as f:f.write(f"\n- {e['timestamp']} | @{e['username'] or 'unbekannt'} | {e['event_type']} | {e['category']} | Media: {e['media_id'] or '-'}\n")
 return e
def _ticket_lock_path(ticket:str)->Path:return LOCK_DIR/f"TICKET_LOCK_{ticket}"
def _acquire_ticket_lock(ticket:str,run_id:str="")->tuple[bool,Path]:
 path=_ticket_lock_path(ticket);path.parent.mkdir(parents=True,exist_ok=True);now=time.time()
 if path.exists():
  try:data=json.loads(path.read_text(encoding="utf-8"));created=float(data.get("timestamp",0))
  except (ValueError,TypeError,json.JSONDecodeError,OSError):created=0
  if now-created<LOCK_TTL_SECONDS:
   print(f"ENGAGEMENT LOCK: {ticket} bereits gesperrt");return False,path
  print(f"ENGAGEMENT LOCK: {ticket} verwaist; wird überschrieben")
  try:path.unlink()
  except FileNotFoundError:pass
 payload=json.dumps({"timestamp":now,"run_id":str(run_id or os.environ.get("GITHUB_RUN_ID","local"))})
 try:
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
  with os.fdopen(fd,"w",encoding="utf-8") as handle:handle.write(payload)
  return True,path
 except FileExistsError:
  print(f"ENGAGEMENT LOCK: {ticket} parallel gesperrt");return False,path
def _release_ticket_lock(path:Path)->None:
 try:path.unlink()
 except FileNotFoundError:pass

def telegram_command(command:str,run_id:str="")->str:
 m=re.match(r"^\s*(antwort|ändern|ignorieren|info|memory)\s+(IG-[A-F0-9]{8})(?:\s+(.*))?\s*$",command,re.I)
 if not m:return "FEHLER: Befehl unbekannt."
 action,ticket,arg=m.group(1).casefold(),m.group(2).upper(),_clean(m.group(3));items=_queue();event=next((x for x in items if x.get("ticket_id")==ticket),None)
 if not event:return f"FEHLER: {ticket} nicht gefunden."
 if action in {"antwort","ändern"} and (event.get("status")=="SENT" or event.get("reply_id")):
  return f"FEHLER: Bereits gesendet (reply_id: {event.get('reply_id') or '-'})"
 if action=="info":return f"{ticket} | @{event.get('username') or 'unbekannt'} | {event['category']} | {event['status']} | {event.get('text','')}"
 if action=="memory":
  if not event.get("username"):return f"{ticket}: kein öffentlicher Accountname vorhanden."
  lines=MEMORY_FILE.read_text(encoding="utf-8").splitlines() if MEMORY_FILE.exists() else [];hits=[x for x in lines if f"@{event['username']} |" in x]
  return "\n".join(hits[-10:]) or f"{ticket}: keine früheren belegbaren Interaktionen."
 lock_path=None
 if action in {"antwort","ändern","ignorieren"}:
  acquired,lock_path=_acquire_ticket_lock(ticket,run_id)
  if not acquired:return f"{ticket}: Verarbeitung läuft bereits (Lock < 5 Min)."
 try:
  return _telegram_mutation(action,ticket,arg,event,items)
 finally:
  if lock_path:_release_ticket_lock(lock_path)

def _telegram_mutation(action,ticket,arg,event,items):
 if action=="ignorieren":event["status"]="IGNORED"
 elif action=="ändern":
  if not arg:return "FEHLER: Nach 'ändern' fehlt der neue Text."
  event["reply_draft"]=arg;event["status"]="SEND_APPROVED"
 elif action=="antwort":
  if not event.get("reply_draft"):return "FEHLER: Kein Antwortvorschlag vorhanden."
  event["status"]="SEND_APPROVED"
 if event.get("status")=="SEND_APPROVED":
  if event.get("reply_id"):return f"{ticket}: SENT | Reply-ID: {event['reply_id']}"
  try:
   reply_id=send_reply(event.get("event_id",""),event.get("reply_draft",""))
  except Exception as exc:
   _save(items);return f"{ticket}: SEND_APPROVED – Senden fehlgeschlagen: {exc}"
  event["status"]="SENT";event["reply_id"]=reply_id;event["sent_at"]=datetime.now(timezone.utc).isoformat()
 _save(items);return f"{ticket}: {event['status']}"
