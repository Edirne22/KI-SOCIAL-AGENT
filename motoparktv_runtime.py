"""MotoParkTv runtime: YouTube metadata/audio -> local Whisper -> rider-close candidates."""
from __future__ import annotations
import json,re,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
from motoparktv_video_ingest import ingest

def _run(args,timeout=1800):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout,check=True)
 return p.stdout.strip()

def metadata(url):
 raw=_run(["yt-dlp","--dump-single-json","--skip-download",url],180)
 o=json.loads(raw)
 return {"url":o.get("webpage_url") or url,"title":o.get("title") or "",
         "description":o.get("description") or "","published_at":_published(o)}

def _published(o):
 ts=o.get("timestamp") or o.get("release_timestamp")
 if ts:return datetime.fromtimestamp(float(ts),timezone.utc).isoformat()
 d=str(o.get("upload_date") or "")
 if re.fullmatch(r"\d{8}",d):
  return datetime.strptime(d,"%Y%m%d").replace(tzinfo=timezone.utc).isoformat()
 return ""

def audio(url,outdir):
 target=str(Path(outdir)/"%(id)s.%(ext)s")
 _run(["yt-dlp","-x","--audio-format","mp3","--audio-quality","5","-o",target,url],1800)
 files=list(Path(outdir).glob("*.mp3"))
 if not files:raise RuntimeError("yt-dlp produced no mp3")
 return files[0]

def whisper(audio_path,model="small"):
 outdir=Path(audio_path).parent/"whisper";outdir.mkdir(exist_ok=True)
 _run(["whisper",str(audio_path),"--model",model,"--language","Turkish","--task","transcribe",
       "--output_format","txt","--output_dir",str(outdir)],1800)
 txt=outdir/(Path(audio_path).stem+".txt")
 if not txt.exists():raise RuntimeError("whisper produced no transcript")
 return txt.read_text(encoding="utf-8",errors="replace").strip()

def video_candidate(url,model="small"):
 meta=metadata(url)
 with tempfile.TemporaryDirectory(prefix="motoparktv-") as td:
  transcript=whisper(audio(meta["url"],td),model)
 return ingest(meta["url"],meta["title"],meta["description"],meta["published_at"],transcript=transcript)

def collect(urls,model="small"):
 out=[]
 for url in urls:
  try:
   row=video_candidate(url,model)
   if row.get("riders"):out.append(row)
  except Exception as e:print("MOTOPARKTV RUNTIME FAIL:",type(e).__name__,str(e)[:180])
 return out
