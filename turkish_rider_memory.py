"""Persistent Turkish-rider discovery memory.

This is operational memory, not a source of truth. Candidates become verified only
when an official/public racing source provides the evidence.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

MEMORY_PATH=Path("memory/TURKISH_RIDER_MEMORY.json")
EVENTS_PATH=Path("memory/MEMORY_EVENTS.jsonl")

def _now():
 return datetime.now(timezone.utc).isoformat()

def load():
 if not MEMORY_PATH.exists(): return {"version":1,"riders":{},"discovery_candidates":{}}
 try:
  data=json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
  if isinstance(data,dict):
   data.setdefault("version",1);data.setdefault("riders",{});data.setdefault("discovery_candidates",{})
   return data
 except (OSError,json.JSONDecodeError): pass
 return {"version":1,"riders":{},"discovery_candidates":{}}

def save(data):
 MEMORY_PATH.parent.mkdir(parents=True,exist_ok=True)
 data["updated_at"]=_now()
 MEMORY_PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def remember_verified(rider,series,sources,seen_url=""):
 data=load();now=_now();row=data["riders"].setdefault(rider,{"first_seen":now})
 row.update({"status":"verified","series":series,"official_sources":list(dict.fromkeys(sources or [])),"last_seen":now})
 if seen_url: row["last_seen_url"]=seen_url
 data["discovery_candidates"].pop(rider,None);save(data);return row

def remember_candidate(name,series,source_url,evidence=""):
 """Remember a discovery lead without promoting it to verified rider truth."""
 data=load();now=_now();row=data["discovery_candidates"].setdefault(name,{"first_seen":now,"sightings":0})
 row["sightings"]=int(row.get("sightings",0))+1
 row.update({"status":"candidate","series":series or row.get("series",""),"last_seen":now,"last_seen_url":source_url,"evidence":evidence[:500]})
 save(data);return row

def known_names():
 data=load();return set(data["riders"])|set(data["discovery_candidates"])
