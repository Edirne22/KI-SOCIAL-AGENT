"""Run a local Chopify checkout against an already-materialized source video."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--home",required=True)
    ap.add_argument("--source",required=True)
    ap.add_argument("--work",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--model",default="tiny")
    ap.add_argument("--aspect",default="9:16")
    ap.add_argument("--style",default="podcast")
    ap.add_argument("--max-clips",type=int,default=3)
    ap.add_argument("--min-len",type=int,default=8)
    ap.add_argument("--max-len",type=int,default=60)
    args=ap.parse_args()
    home=Path(args.home).resolve()
    sys.path.insert(0,str(home))
    from download_and_transcribe import transcribe
    import score_clips
    import render_clips
    work=Path(args.work).resolve(); out=Path(args.out).resolve()
    work.mkdir(parents=True,exist_ok=True); out.mkdir(parents=True,exist_ok=True)
    source=Path(args.source).resolve(strict=True)
    transcribe(source,work,args.model,"cpu","int8")
    score_clips.run(work,max_clips=args.max_clips,min_len=args.min_len,max_len=args.max_len)
    transcript=__import__("json").loads((work/"transcript.json").read_text(encoding="utf-8-sig"))
    segments=__import__("json").loads((work/"segments.json").read_text(encoding="utf-8-sig"))
    words=transcript["words"]; width,height=render_clips.ffprobe_dims(source)
    saved=[]
    for seg in segments:
        saved.append(render_clips.render(seg,words,source,width,height,work,args.aspect,out_dir=out,style=args.style))
    if not saved:
        raise SystemExit("chopify produced no clips")
    print("CHOPIFY_BRIDGE_PASS",len(saved))

if __name__=="__main__":
    main()
