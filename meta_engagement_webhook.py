"""Fail-closed Meta webhook adapter for Instagram/Facebook engagement.

This module does not publish or reply. It verifies Meta webhook requests and
normalizes supported comment/feed events for the engagement agents.
"""
from __future__ import annotations
import hashlib, hmac, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

INBOX=Path("memory/META_ENGAGEMENT_INBOX.jsonl")

def verify_challenge(query:dict[str,str])->tuple[int,str]:
    expected=os.environ.get("META_WEBHOOK_VERIFY_TOKEN","")
    if expected and query.get("hub.mode")=="subscribe" and hmac.compare_digest(query.get("hub.verify_token",""),expected):
        return 200,query.get("hub.challenge","")
    return 403,"Forbidden"

def valid_signature(raw:bytes,header:str)->bool:
    secret=os.environ.get("META_APP_SECRET","")
    if not secret or not header.startswith("sha256="):return False
    expected=hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest()
    return hmac.compare_digest(header[7:],expected)

def normalize(payload:dict[str,Any])->list[dict[str,Any]]:
    out=[]
    obj=str(payload.get("object","")).lower()
    platform="instagram" if "instagram" in obj else "facebook" if obj=="page" else ""
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value=change.get("value") or {}; field=str(change.get("field",""))
            if platform=="instagram" and field=="comments":
                out.append({"platform":"instagram","event_id":str(value.get("id") or ""),"event_type":"comment","username":str((value.get("from") or {}).get("username") or ""),"media_id":str((value.get("media") or {}).get("id") or ""),"text":str(value.get("text") or ""),"timestamp":str(entry.get("time") or "")})
            elif platform=="facebook" and field=="feed" and value.get("item")=="comment":
                actor=value.get("from") or {}
                out.append({"platform":"facebook","event_id":str(value.get("comment_id") or value.get("post_id") or ""),"event_type":"comment","actor_name":str(actor.get("name") or ""),"post_id":str(value.get("post_id") or ""),"text":str(value.get("message") or ""),"timestamp":str(entry.get("time") or "")})
    return [x for x in out if x["event_id"]]

def persist(events:list[dict[str,Any]])->int:
    if not events:return 0
    INBOX.parent.mkdir(parents=True,exist_ok=True)
    with INBOX.open("a",encoding="utf-8") as f:
        for e in events:f.write(json.dumps(e,ensure_ascii=False)+"\n")
    return len(events)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import parse_qs,urlparse
        q={k:v[-1] for k,v in parse_qs(urlparse(self.path).query).items()}
        code,body=verify_challenge(q);self.send_response(code);self.end_headers();self.wfile.write(body.encode())
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0"));raw=self.rfile.read(n)
        if not valid_signature(raw,self.headers.get("X-Hub-Signature-256","")):
            self.send_response(403);self.end_headers();return
        try:payload=json.loads(raw)
        except ValueError:self.send_response(400);self.end_headers();return
        persist(normalize(payload));self.send_response(200);self.end_headers();self.wfile.write(b"EVENT_RECEIVED")
    def log_message(self,fmt,*args):print("META-WEBHOOK:",fmt%args)

if __name__=="__main__":
    port=int(os.environ.get("PORT","8080"))
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()
