"""Manual live smoke: real yt-dlp + local Whisper, no publish side effects."""
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
import motoparktv_runtime as rt
import motoparktv_video_ingest as ingest_mod

def run(url,model="tiny"):
    # Isolate operational memory: live smoke must not mutate production memory.
    captured=[]
    old=ingest_mod.remember_video
    ingest_mod.remember_video=lambda row: captured.append(dict(row))
    try:
        meta=rt.metadata(url)
        with tempfile.TemporaryDirectory(prefix="motoparktv-live-") as td:
            audio=rt.audio(meta["url"],td)
            if not Path(audio).is_file() or Path(audio).stat().st_size<=0:
                raise RuntimeError("live audio missing or empty")
            transcript=rt.whisper(audio,model)
        if not transcript.strip(): raise RuntimeError("live transcript empty")
        row=ingest_mod.ingest(meta["url"],meta["title"],meta["description"],meta["published_at"],transcript=transcript)
    finally:
        ingest_mod.remember_video=old
    lineage=row.get("source_lineage") or {}
    assert row.get("source_url")==meta["url"]
    assert lineage.get("source_url")==row["source_url"]
    assert lineage.get("transcription")=="local-whisper"
    assert lineage.get("original_wording_reuse") is False
    assert captured and captured[-1].get("source_lineage")==lineage
    return {"source_url":row["source_url"],"published_at":row.get("published_at",""),
            "riders":row.get("riders",[]),"transcript_chars":len(row.get("video_transcript","")),
            "source_lineage":lineage,"publish_side_effect":False}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--url",default=os.environ.get("MOTOPARKTV_LIVE_URL",""))
    ap.add_argument("--model",default=os.environ.get("WHISPER_MODEL","tiny"))
    a=ap.parse_args()
    if not a.url: raise SystemExit("MOTOPARKTV_LIVE_URL/--url required")
    print(json.dumps(run(a.url,a.model),ensure_ascii=False,sort_keys=True))
    print("LIVE E2E – yt-dlp -> audio -> Whisper -> ingest -> lineage: PASS")
