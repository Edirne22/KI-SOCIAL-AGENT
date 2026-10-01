"""Block6 alternative: bounded real FFmpeg caption+audio -> private R2 -> verified ffprobe.

This explicit synthetic benchmark does NOT replace user approval or claim that
OpenChatCut, SupoClip or the whole Factory staffellauf passed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from media_storage import R2Storage

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/test/test-video-portrait.mp4"
SIZES=(7,15,30)
LABEL="EDIRNE 22 TEST"
MAX_BYTES=45*1024*1024

def run_ffmpeg(source:Path,dest:Path,seconds:int,runner=subprocess.run):
    if seconds not in SIZES:raise ValueError("unsupported bounded clip duration")
    if source.resolve()!=SOURCE.resolve() or not source.is_file():
        raise ValueError("only tracked synthetic sample clip is allowed")
    # The overlay is a literal constant, not user/LLM-origin text.
    args=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
        "-stream_loop","-1","-i",str(source),
        "-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
        "-map","0:v:0","-map","1:a:0",
        "-vf","drawtext=text='EDIRNE 22 TEST':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-90,scale=720:-2,setsar=1",
        "-c:v","libx264","-preset","veryfast","-crf","27",
        "-pix_fmt","yuv420p","-r","24",
        "-c:a","aac","-b:a","96k","-t",str(seconds),
        "-movflags","+faststart",str(dest)]
    result=runner(args,capture_output=True,text=True,timeout=180,check=False)
    if result.returncode!=0 or not dest.exists() or dest.stat().st_size==0:
        raise RuntimeError("FFMPEG_RENDER_FAILED")
    if dest.stat().st_size>MAX_BYTES:
        dest.unlink(missing_ok=True)
        raise RuntimeError("FFMPEG_OUTPUT_EXCEEDS_BUDGET")

def inspect_ffprobe(path:Path,seconds:int,runner=subprocess.run):
    result=runner(["ffprobe","-v","error","-show_entries",
        "format=duration,size:stream=codec_type,codec_name",
        "-of","json",str(path)],capture_output=True,text=True,timeout=20,check=False)
    if result.returncode!=0:raise RuntimeError("FFPROBE_FAILED")
    try:
        payload=json.loads(result.stdout)
        duration=float(payload["format"]["duration"])
        codecs={stream["codec_type"] for stream in payload["streams"]}
        size=int(payload["format"]["size"])
    except (KeyError,ValueError,TypeError,IndexError):
        raise RuntimeError("FFPROBE_INVALID")
    if not seconds-0.5<=duration<=seconds+0.5 or codecs!={"video","audio"} or not 0<size<=MAX_BYTES:
        raise RuntimeError("FFPROBE_MEDIA_CONTRACT_FAILED")
    return {"seconds":seconds,"duration":round(duration,2),"tracks":sorted(codecs),"size":size}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--live-synthetic-r2",action="store_true",required=True)
    args=p.parse_args()
    if not args.live_synthetic_r2 or os.getenv("BLOCK6_SYNTHETIC_R2_TEST_APPROVED")!="true":
        raise RuntimeError("SYNTHETIC_R2_TEST_NOT_APPROVED")
    if not SOURCE.is_file():raise RuntimeError("FIXTURE_NOT_FOUND")
    with tempfile.TemporaryDirectory(prefix="b6-ffmpeg-") as td:
        scratch=Path(td)
        storage=R2Storage.from_env(cache_root=scratch/"download")
        results=[]
        for seconds in SIZES:
            dest=scratch/f"block6-synthetic-{seconds}.mp4"
            run_ffmpeg(SOURCE,dest,seconds)
            checked=inspect_ffprobe(dest,seconds)
            src_hash=hashlib.sha256(dest.read_bytes()).hexdigest()
            # Source/medium identity is created by existing Factory storage
            # contract. A successful PUT alone is never enough.
            ref=storage.put_file(dest,provenance=f"block6-synthetic-ffmpeg:{seconds}s",
                                 mime_type="video/mp4")
            restored=storage.resolve_local(ref)
            if restored.stat().st_size!=checked["size"]:
                raise RuntimeError("R2_ROUNDTRIP_SIZE_MISMATCH")
            restored_hash=hashlib.sha256(restored.read_bytes()).hexdigest()
            if src_hash!=restored_hash or ref.sha256!=src_hash:
                raise RuntimeError("R2_ROUNDTRIP_SHA256_MISMATCH")
            inspect_ffprobe(restored,seconds)
            results.append({"seconds":seconds,"r2_verified":True,
                            "sha256_prefix":src_hash[:12],"duration":checked["duration"],
                            "tracks":checked["tracks"]})
        print("BLOCK6_SYNTHETIC_FFMPEG_R2_PASS="+json.dumps(results,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
