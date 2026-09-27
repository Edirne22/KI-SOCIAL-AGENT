"""MotoParkTv rider-close video ingest.

Discovery stays lightweight. Transcription is delegated to a configured command so the
runtime can use local Whisper/faster-whisper without sending video/audio through the LLM.
"""
from __future__ import annotations
import os,re,shlex,subprocess
from datetime import datetime,timezone
import requests
from turkish_rider_names import CANONICAL_ALIASES,fold
from turkish_rider_memory import remember_video

CHANNEL_URL="https://www.youtube.com/@MotoParkTv"
UA={"User-Agent":"Mozilla/5.0 KI-SOCIAL-AGENT MotoParkTv Scout"}

def discover(limit=10):
 r=requests.get(CHANNEL_URL+"/videos",headers=UA,timeout=30);r.raise_for_status()
 ids=list(dict.fromkeys(re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"',r.text)))
 return ["https://www.youtube.com/watch?v="+v for v in ids[:limit]]

def transcribe(url):
 cmd=os.getenv("MOTOPARKTV_TRANSCRIBE_CMD","").strip()
 if not cmd: raise RuntimeError("MOTOPARKTV_TRANSCRIBE_CMD is not configured")
 p=subprocess.run(shlex.split(cmd)+[url],capture_output=True,text=True,timeout=1800,check=True)
 text=p.stdout.strip()
 if not text: raise RuntimeError("transcriber returned empty transcript")
 return text

def riders_in(text):
 haystack=fold(text);names=[]
 for rider,aliases in CANONICAL_ALIASES.items():
  if any(re.search(r"(?<![a-z])"+re.escape(fold(alias))+r"(?![a-z])",haystack) for alias in aliases):
   names.append(rider)
 return names

def freshness_hours(published_at,now=None):
 if not published_at:return 9999
 now=now or datetime.now(timezone.utc)
 dt=datetime.fromisoformat(published_at.replace("Z","+00:00"))
 return max(0,(now-dt).total_seconds()/3600)

def freshness_score(hours):
 if hours<=24:return 100
 if hours<=72:return 75
 if hours<=168:return 50
 return 10

def ingest(url,title,description,published_at,transcript=None):
 transcript=(transcript if transcript is not None else transcribe(url)).strip()
 riders=riders_in(" ".join((title,description,transcript)))
 row={"source":"MotoParkTv","source_url":url,"url":url,"title":title,"summary":description,
      "published_at":published_at,"video_transcript":transcript,
      "freshness_score":freshness_score(freshness_hours(published_at)),
      "riders":riders,"transcript":transcript}
 remember_video(row)
 return row
