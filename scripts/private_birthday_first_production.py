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
FPS=25

def run_ffmpeg(cmd, *, step, timeout):
    """Run FFmpeg without leaking private paths/media into persistent diagnostics."""
    try:
        return subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=timeout)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"PRIVATE_FFMPEG_FAILED:{step}:exit_{exc.returncode}") from None
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"PRIVATE_FFMPEG_TIMEOUT:{step}") from None

def render_segment(src, seg, *, is_image, seconds, effect="zoom_in", transition=("soft_fade",0.35)):
    # Concat demuxer stream-copy requires identical time bases. Previously photo
    # (10 fps) and video (15 fps) tracks stretched a 300s timeline to 324s.
    # V2: execute the Creative/Media scene assignment instead of rendering every
    # asset with the same slideshow filter. Keep a common output geometry/timebase.
    base="scale=620:1102:force_original_aspect_ratio=increase"
    motion={
        "zoom_in":"crop=540:960:x='40+20*t/{seconds:.3f}':y='71+35*t/{seconds:.3f}'",
        "zoom_out":"crop=540:960:x='60-20*t/{seconds:.3f}':y='106-35*t/{seconds:.3f}'",
        "pan_left":"crop=540:960:x='80-40*t/{seconds:.3f}':y=71",
        "pan_right":"crop=540:960:x='40+40*t/{seconds:.3f}':y=71",
    }.get(effect)
    if motion is None: raise ValueError("unknown private creative effect")
    vf=base+","+motion.format(seconds=seconds)+",setsar=1"
    vf+=f",fps={FPS},setpts=PTS-STARTPTS"
    if not is_image:
        # Short clips occupy their planned slot without moving later story cards.
        vf+=f",tpad=stop_mode=clone:stop_duration={seconds:.3f}"
    transition_id,fade_seconds=transition
    if transition_id not in {"soft_fade","quick_fade","long_fade"}: raise ValueError("unknown private transition")
    fade_seconds=max(0.12,min(float(fade_seconds),max(0.12,seconds/3)))
    vf+=f",fade=t=in:st=0:d={fade_seconds:.3f},fade=t=out:st={max(0.0,seconds-fade_seconds):.3f}:d={fade_seconds:.3f}"
    cmd=["ffmpeg","-y"]
    if is_image:
        cmd += ["-loop","1","-framerate",str(FPS)]
    cmd += ["-i",str(src),"-t",f"{seconds:.3f}","-vf",vf,"-an",
            "-c:v","libx264","-preset","ultrafast","-crf","28",
            "-pix_fmt","yuv420p","-video_track_timescale","25000",str(seg)]
    run_ffmpeg(cmd,step="segment",timeout=120)

def fftext(value):
    return str(value).replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")

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
    target_seconds=int(getattr(plan,"duration_seconds",TARGET_SECONDS) if plan else TARGET_SECONDS)
    overlays=list(getattr(plan,"overlays",[]) if plan else [TITLE,"12 Jahre voller Erinnerungen","Alles Gute zum 12. Geburtstag, Dünya! ❤️"])
    music=MUSIC
    effects=list(getattr(plan,"asset_effects",[]) if plan else [])
    if plan and len(effects)!=len(assets):
        raise RuntimeError("PRIVATE_CREATIVE_ASSIGNMENT_MISMATCH")
    if not effects:
        effects=["zoom_in","pan_left","zoom_out","pan_right"][:len(assets)]
        while len(effects)<len(assets): effects.append(("zoom_in","pan_left","zoom_out","pan_right")[len(effects)%4])
    transitions=list(getattr(plan,"asset_transitions",[]) if plan else [])
    pacing=list(getattr(plan,"asset_pacing",[]) if plan else [])
    if plan and (len(transitions)!=len(assets) or len(pacing)!=len(assets)):
        raise RuntimeError("PRIVATE_CREATIVE_TIMING_ASSIGNMENT_MISMATCH")
    if not transitions: transitions=[("soft_fade",0.35)]*len(assets)
    if not pacing: pacing=[1.0]*len(assets)
    image_count=sum(1 for a in assets if a["mime"].startswith("image/"))
    video_count=len(assets)-image_count
    image_seconds=max(1.35,(target_seconds-(video_count*4))/image_count) if image_count else 1.35
    # Pacing is relative creative timing, not permission to stretch the master.
    # Normalize all planned slots back to the requested total duration.
    base_slots=[image_seconds if a["mime"].startswith("image/") else 4 for a in assets]
    weighted_slots=[max(1.0,base*pacing[i]) for i,base in enumerate(base_slots)]
    timing_scale=target_seconds/sum(weighted_slots)
    planned_slots=[slot*timing_scale for slot in weighted_slots]
    token=os.environ["TELEGRAM_BOT_TOKEN"]; chat=os.environ["TELEGRAM_CHAT_ID"]
    with tempfile.TemporaryDirectory(prefix="duenya-private-") as td:
        root=Path(td); segments=[]
        for i,a in enumerate(assets):
            suffix={ "image/jpeg":".jpg","image/png":".png","video/mp4":".mp4","video/quicktime":".mov"}[a["mime"]]
            src=root/f"in-{i:03d}{suffix}"
            src.write_bytes(client.get_object(Bucket=bucket,Key=a["key"])["Body"].read())
            seg=root/f"seg-{i:03d}.mp4"
            is_image=a["mime"].startswith("image/")
            planned_seconds=planned_slots[i]
            render_segment(src,seg,is_image=is_image,seconds=planned_seconds,effect=effects[i],transition=transitions[i])
            segments.append(seg)
        concat=root/"concat.txt"; concat.write_text("".join("file '"+str(p).replace("'","'\\''")+"'\n" for p in segments))
        rough=root/"rough.mp4"
        run_ffmpeg(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(rough)],step="concat",timeout=300)
        # Private creative lane: tasteful title/memory cards, then documented public-domain music.
        visual=root/"visual.mp4"
        title_text=fftext(overlays[0] if overlays else TITLE)
        mid_text=fftext(overlays[1] if len(overlays)>1 else "Unsere schönsten Erinnerungen")
        end_text=fftext(overlays[2] if len(overlays)>2 else "Alles Gute!")
        draw=(f"drawtext=text='{title_text}':fontcolor=white:fontsize=44:borderw=4:bordercolor=black:"
              "x=(w-text_w)/2:y=h*0.78:enable='between(t,1,7)',"
              f"drawtext=text='{mid_text}':fontcolor=white:fontsize=30:borderw=3:bordercolor=black:"
              "x=(w-text_w)/2:y=h*0.80:enable='between(t,105,112)',"
              f"drawtext=text='{end_text}':fontcolor=white:fontsize=24:borderw=3:bordercolor=black:"
              "x=(w-text_w)/2:y=h*0.80:enable='between(t,286,299)'")
        run_ffmpeg(["ffmpeg","-y","-i",str(rough),"-vf",draw,"-an","-c:v","libx264","-preset","veryfast",
                        "-b:v","850k","-maxrate","950k","-bufsize","1900k","-pix_fmt","yuv420p","-movflags","+faststart",str(visual)],step="title_cards",timeout=600)
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
        evidence={"creative_revision":getattr(plan,"creative_revision","legacy"),
                  "applied_effects":tuple(sorted(set(effects))),
                  "scene_count":len(getattr(plan,"scene_plan",())),
                  "applied_transitions":tuple(sorted(set(t[0] for t in transitions))),
                  "pacing_applied":len(pacing)==len(assets) and len(set(pacing))>=2,
                  "overlays_rendered":min(3,len(overlays))}
        return {"duration":duration,"has_audio":True,"has_video":True,"r2_key":key,"sha256":digest,
                "creative_evidence":evidence}

if __name__=="__main__": run()
