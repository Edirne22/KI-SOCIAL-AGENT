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
from scripts.ai_central_shared_inbox import client_from_env
from scripts.r2_media_warehouse import job_prefix

INDEX="private/v1/telegram-album-index/"
WINDOW_HOURS=4
MAX_ITEMS=80

def recent_assets(client,bucket,now=None):
    now=now or datetime.now(timezone.utc); cutoff=now-timedelta(hours=WINDOW_HOURS)
    page=client.list_objects_v2(Bucket=bucket,Prefix=INDEX,MaxKeys=1000)
    if page.get("IsTruncated"): raise RuntimeError("PRIVATE_INDEX_TOO_LARGE")
    rows=[]
    for entry in page.get("Contents",[]):
        rec=json.loads(client.get_object(Bucket=bucket,Key=entry["Key"])["Body"].read(4096))
        if rec.get("lane")!="private": continue
        created=datetime.fromisoformat(rec["created_at"])
        if created<cutoff: continue
        prefix=rec.get("prefix") or job_prefix("private",created,rec["job_id"])
        manifest=json.loads(client.get_object(Bucket=bucket,Key=prefix+"manifest.json")["Body"].read(300000))
        if manifest.get("lane")!="private" or manifest.get("status")!="INTAKE": continue
        for asset in manifest.get("assets",[]):
            if asset.get("mime") in {"image/jpeg","image/png","video/mp4","video/quicktime"}:
                rows.append((asset.get("received_at",rec["created_at"]),asset))
    rows.sort(key=lambda x:x[0])
    if not rows or len(rows)>MAX_ITEMS: raise RuntimeError("PRIVATE_INPUT_COUNT_UNSAFE")
    return [x[1] for x in rows]

def run():
    client,bucket=client_from_env()
    assets=recent_assets(client,bucket)
    token=os.environ["TELEGRAM_BOT_TOKEN"]; chat=os.environ["TELEGRAM_CHAT_ID"]
    with tempfile.TemporaryDirectory(prefix="duenya-private-") as td:
        root=Path(td); segments=[]
        for i,a in enumerate(assets):
            suffix={ "image/jpeg":".jpg","image/png":".png","video/mp4":".mp4","video/quicktime":".mov"}[a["mime"]]
            src=root/f"in-{i:03d}{suffix}"
            src.write_bytes(client.get_object(Bucket=bucket,Key=a["key"])["Body"].read())
            seg=root/f"seg-{i:03d}.mp4"
            vf="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1"
            if a["mime"].startswith("image/"):
                cmd=["ffmpeg","-y","-loop","1","-t","1.35","-i",str(src),"-vf",vf+",zoompan=z='min(zoom+0.0015,1.10)':d=41:s=1080x1920:fps=30","-an","-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p",str(seg)]
            else:
                cmd=["ffmpeg","-y","-i",str(src),"-t","4","-vf",vf+",fps=30","-an","-c:v","libx264","-pix_fmt","yuv420p",str(seg)]
            subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120)
            segments.append(seg)
        concat=root/"concat.txt"; concat.write_text("".join("file '"+str(p).replace("'","'\\''")+"'\n" for p in segments))
        out=root/"Duenya-Level-12-private.mp4"
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(out)],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=300)
        data=out.read_bytes()
        if not data or len(data)>49*1024*1024: raise RuntimeError("PRIVATE_RENDER_SIZE_UNSAFE")
        digest=sha256(data).hexdigest()
        key=f"private/v1/productions/duenya-level-12-{digest[:16]}.mp4"
        client.put_object(Bucket=bucket,Key=key,Body=data,ContentType="video/mp4")
        check=client.get_object(Bucket=bucket,Key=key)["Body"].read()
        if sha256(check).hexdigest()!=digest: raise RuntimeError("PRIVATE_R2_RENDER_VERIFY_FAILED")
        with out.open("rb") as fh:
            response=requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                data={"chat_id":chat,"caption":"🎬 Dünya – Level 12 · PRIVATE Erstfassung\nKeine Veröffentlichung."},
                files={"video":("Duenya-Level-12-private.mp4",fh,"video/mp4")},timeout=120)
        if response.status_code!=200: raise RuntimeError("PRIVATE_TELEGRAM_DELIVERY_FAILED")
        print(f"PRIVATE_BIRTHDAY_PRODUCTION_PASS media_count={len(assets)} sha256_prefix={digest[:12]} private=yes published=no")

if __name__=="__main__": run()
