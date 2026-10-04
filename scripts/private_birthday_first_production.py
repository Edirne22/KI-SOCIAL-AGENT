"""One-shot private birthday production from recent Telegram albums.

Owner-authorized 2026-10-04 production path. Reads only private R2 media,
renders locally on the ephemeral runner, stores the result back in private R2
and sends the finished MP4 only to the configured owner Telegram chat.
No social publisher and no GitHub artifact.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json, os, subprocess, tempfile
from pathlib import Path
import requests
from music_agent import mix_music, output_is_valid, probe_duration
from scripts.ai_central_shared_inbox import client_from_env
from scripts.r2_media_warehouse import job_prefix

INDEX="private/v1/telegram-album-index/"
SESSION_HOURS=3
MAX_ITEMS=80
TARGET_SECONDS=300
MUSIC=Path("assets/musik/chill/hypnotic-ambient.mp3")
TITLE="Dünya – Level 12"

def fftext(value):
    value=str(value or "")[:160]
    return value.replace("\\","\\\\").replace(":","\\:").replace("'","\\'")

def segment_timeout(seconds, image=False):
    factor=45 if image else 20
    return max(180,min(420,int(max(1.0,float(seconds))*factor)))

def recent_assets(client,bucket,now=None):
    # Bind to the latest private upload *session*, not the wall clock. The owner
    # may start rendering hours after upload; a 4h "now" cutoff must never force
    # a re-upload. Multiple Telegram albums sent close together are one session.
    page=client.list_objects_v2(Bucket=bucket,Prefix=INDEX,MaxKeys=1000)
    if page.get("IsTruncated"): raise RuntimeError("PRIVATE_INDEX_TOO_LARGE")
    albums=[]
    for entry in page.get("Contents",[]):
        rec=json.loads(client.get_object(Bucket=bucket,Key=entry["Key"])["Body"].read(4096))
        if rec.get("lane")!="private": continue
        try:
            created=datetime.fromisoformat(rec["created_at"])
        except (KeyError,TypeError,ValueError):
            continue
        if created.tzinfo is None: continue
        prefix=rec.get("prefix") or job_prefix("private",created,rec["job_id"])
        manifest=json.loads(client.get_object(Bucket=bucket,Key=prefix+"manifest.json")["Body"].read(300000))
        if manifest.get("lane")!="private" or manifest.get("status")!="INTAKE": continue
        assets=[a for a in manifest.get("assets",[])
                if a.get("mime") in {"image/jpeg","image/png","video/mp4","video/quicktime"}]
        if assets: albums.append((created,assets))
    if not albums: raise RuntimeError("PRIVATE_INPUT_COUNT_UNSAFE")
    newest=max(created for created,_ in albums)
    cutoff=newest-timedelta(hours=SESSION_HOURS)
    rows=[]
    for created,assets in albums:
        if created<cutoff: continue
        for asset in assets:
            rows.append((asset.get("received_at",created.isoformat()),asset))
    rows.sort(key=lambda x:x[0])
    if not rows or len(rows)>MAX_ITEMS: raise RuntimeError("PRIVATE_INPUT_COUNT_UNSAFE")
    return [x[1] for x in rows]

def run(*, task_id=None, prompt=None, plan=None, assets_override=None):
    client,bucket=client_from_env()
    assets=assets_override or recent_assets(client,bucket)
    plan=plan or {}
    target_seconds=int(plan.get("target_seconds") or TARGET_SECONDS)
    creative_plan=plan.get("creative") or {}
    overlays=list(creative_plan.get("overlays") or [TITLE,"12 Jahre voller Erinnerungen","Alles Gute zum 12. Geburtstag, Dünya!"])
    music_plan=plan.get("music_audio") or {}
    music=Path(music_plan.get("path") or MUSIC)
    image_count=sum(1 for a in assets if a["mime"].startswith("image/"))
    video_count=len(assets)-image_count
    image_seconds=max(1.35,(target_seconds-(video_count*4))/image_count) if image_count else 1.35
    token=os.environ["TELEGRAM_BOT_TOKEN"]; chat=os.environ["TELEGRAM_CHAT_ID"]
    with tempfile.TemporaryDirectory(prefix="duenya-private-") as td:
        root=Path(td); segments=[]
        for i,a in enumerate(assets):
            suffix={ "image/jpeg":".jpg","image/png":".png","video/mp4":".mp4","video/quicktime":".mov"}[a["mime"]]
            src=root/f"in-{i:03d}{suffix}"
            src.write_bytes(client.get_object(Bucket=bucket,Key=a["key"])["Body"].read())
            seg=root/f"seg-{i:03d}.mp4"
            vf="scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1"
            if a["mime"].startswith("image/"):
                frames=max(24,int(image_seconds*24))
                creative=vf+f",zoompan=z=min(zoom+0.00035\\,1.08):d={frames}:s=720x1280:fps=24,scale=1080:1920:flags=fast_bilinear,fade=t=in:st=0:d=0.35,fade=t=out:st={max(0.0,image_seconds-0.45):.3f}:d=0.45"
                cmd=["ffmpeg","-y","-loop","1","-t",f"{image_seconds:.3f}","-i",str(src),"-vf",creative,"-an","-c:v","libx264","-preset","veryfast","-crf","28","-pix_fmt","yuv420p",str(seg)]
            else:
                cmd=["ffmpeg","-y","-i",str(src),"-t","4","-vf",vf+",fps=24,scale=1080:1920:flags=fast_bilinear,fade=t=in:st=0:d=0.25,fade=t=out:st=3.55:d=0.45","-an","-c:v","libx264","-preset","veryfast","-crf","28","-pix_fmt","yuv420p",str(seg)]
            subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=segment_timeout(image_seconds if a["mime"].startswith("image/") else 4, image=a["mime"].startswith("image/")))
            segments.append(seg)
        concat=root/"concat.txt"; concat.write_text("".join("file '"+str(p).replace("'","'\\''")+"'\n" for p in segments))
        rough=root/"rough.mp4"
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(rough)],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=300)
        # Private creative lane: tasteful title/memory cards, then documented public-domain music.
        visual=root/"visual.mp4"
        title_text=fftext(overlays[0] if overlays else TITLE)
        mid_text=fftext(overlays[1] if len(overlays)>1 else "Unsere schönsten Erinnerungen")
        end_text=fftext(overlays[2] if len(overlays)>2 else "Alles Gute!")
        draw=(f"drawtext=text='{title_text}':fontcolor=white:fontsize=64:borderw=4:bordercolor=black:"
              "x=(w-text_w)/2:y=h*0.78:enable='between(t,1,7)',"
              f"drawtext=text='{mid_text}':fontcolor=white:fontsize=50:borderw=3:bordercolor=black:"
              "x=(w-text_w)/2:y=h*0.80:enable='between(t,105,112)',"
              f"drawtext=text='{end_text}':fontcolor=white:fontsize=48:borderw=3:bordercolor=black:"
              "x=(w-text_w)/2:y=h*0.80:enable='between(t,286,299)'")
        subprocess.run(["ffmpeg","-y","-i",str(rough),"-vf",draw,"-an","-c:v","libx264","-preset","veryfast",
                        "-b:v","850k","-maxrate","950k","-bufsize","1900k","-pix_fmt","yuv420p","-movflags","+faststart",str(visual)],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=600)
        if not music.exists(): raise RuntimeError("PRIVATE_BIRTHDAY_MUSIC_MISSING")
        out=root/"Duenya-Level-12-private.mp4"
        mix_music(visual,music,out)
        duration=probe_duration(out)
        if not max(1,target_seconds-15) <= duration <= target_seconds+5: raise RuntimeError(f"PRIVATE_RENDER_DURATION_UNSAFE:{duration:.2f}")
        if not output_is_valid(out): raise RuntimeError("PRIVATE_RENDER_STREAMS_INVALID")
        data=out.read_bytes()
        if not data or len(data)>49*1024*1024: raise RuntimeError("PRIVATE_RENDER_SIZE_UNSAFE")
        digest=sha256(data).hexdigest()
        key=f"private/v1/productions/duenya-level-12-{digest[:16]}.mp4"
        client.put_object(Bucket=bucket,Key=key,Body=data,ContentType="video/mp4")
        check=client.get_object(Bucket=bucket,Key=key)["Body"].read()
        if sha256(check).hexdigest()!=digest: raise RuntimeError("PRIVATE_R2_RENDER_VERIFY_FAILED")
        with out.open("rb") as fh:
            response=requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                data={"chat_id":chat,"caption":"🎬 Dünya – Level 12 · PRIVATE Kreativfassung\nMusik · Texte · Bewegungen · Übergänge\nKeine Veröffentlichung."},
                files={"video":("Duenya-Level-12-private.mp4",fh,"video/mp4")},timeout=120)
        if response.status_code!=200: raise RuntimeError("PRIVATE_TELEGRAM_DELIVERY_FAILED")
        print(f"PRIVATE_BIRTHDAY_PRODUCTION_PASS media_count={len(assets)} duration={duration:.2f}s audio=yes creative=yes sha256_prefix={digest[:12]} private=yes published=no")
        return {"duration":duration,"has_audio":True,"has_video":True,"r2_key":key,"sha256":digest}

if __name__=="__main__": run()
