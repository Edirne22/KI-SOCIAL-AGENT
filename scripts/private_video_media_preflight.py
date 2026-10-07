"""Privacy-safe preflight for private video source media.

Validates local staged media with ffprobe before FFmpeg production. It prints
counts and technical error classes only; private filenames are never logged.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

IMAGE_EXT={".jpg",".jpeg",".png",".webp",".heic"}
VIDEO_EXT={".mp4",".mov",".m4v",".webm"}

def probe(path: Path) -> dict:
    p=subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size","-of","json",str(path)],capture_output=True,text=True,timeout=30)
    if p.returncode:
        raise RuntimeError("FFPROBE_REJECTED_MEDIA")
    return json.loads(p.stdout)

def validate(root: Path) -> dict:
    files=[p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXT|VIDEO_EXT]
    if not files: raise RuntimeError("PRIVATE_MEDIA_EMPTY")
    images=videos=0
    for p in files:
        d=probe(p); streams=d.get("streams") or []
        if p.suffix.lower() in IMAGE_EXT:
            images+=1
            v=next((s for s in streams if s.get("codec_type")=="video"),None)
            if not v or int(v.get("width") or 0)<1 or int(v.get("height") or 0)<1:
                raise RuntimeError("PRIVATE_IMAGE_INVALID")
        else:
            videos+=1
            if not any(s.get("codec_type")=="video" for s in streams):
                raise RuntimeError("PRIVATE_VIDEO_INVALID")
            try: dur=float((d.get("format") or {}).get("duration") or 0)
            except ValueError: dur=0
            if dur<=0: raise RuntimeError("PRIVATE_VIDEO_DURATION_INVALID")
    return {"schema":"PRIVATE-VIDEO-PREFLIGHT-V1","media_count":len(files),"images":images,"videos":videos,"ready":True}

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: private_video_media_preflight.py MEDIA_DIR")
    try: result=validate(Path(sys.argv[1]))
    except Exception as e:
        print("PRIVATE_VIDEO_PREFLIGHT_FAILED:"+e.__class__.__name__+":"+str(e))
        return 1
    print(json.dumps(result,separators=(",",":")))
    return 0
if __name__=="__main__": raise SystemExit(main())
