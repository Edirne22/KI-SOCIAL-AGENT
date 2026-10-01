"""Bounded full Factory input -> FFmpeg -> storage -> verified playback handoff.
Offline mode uses local storage; live mode uses private R2 credentials on main only.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import tempfile

from content_factory_core import ProductionJob, JobStatus
from content_factory_creative import CreativeBrief, StoryBeat, ContentFormat
from content_factory_media_production import MediaProductionPlanner, MediaProductionRunner, FFmpegAdapter
from media_storage import LocalScratchStorage, R2Storage
from scripts.block6_ffmpeg_r2_fallback import SOURCE, inspect_ffprobe

def run(*, live_r2: bool):
    if not SOURCE.is_file() or not SOURCE.stat().st_size:
        raise RuntimeError("TRACKED_SOURCE_MISSING")
    with tempfile.TemporaryDirectory(prefix="block6-factory-") as td:
        base = Path(td)
        storage = (R2Storage.from_env(cache_root=base / "cache") if live_r2
                   else LocalScratchStorage(base / "store"))
        source = storage.put_file(SOURCE, provenance="block6-locked-factory-source", mime_type="video/mp4")
        job = ProductionJob("block6-verified-source")
        for state in (JobStatus.INGESTING, JobStatus.RESEARCHING, JobStatus.WRITING,
                      JobStatus.STORYBOARDING):
            job.transition(state)
        job.media.append(source)
        brief = CreativeBrief("block6-verified", "locked", ContentFormat.REEL,
                              ("instagram",), "EDIRNE 22 TEST", "test",
                              (StoryBeat("clip", "verified fixture", (), "portrait video"),),
                              (), "de")
        plan = MediaProductionPlanner().plan(job, brief, independent_ffmpeg=True)
        if tuple(x.machine for x in plan.steps) != ("ffmpeg",):
            raise RuntimeError("UNEXPECTED_FALLBACK_PLAN")
        out = MediaProductionRunner().execute(job, plan,
                                              {"ffmpeg": FFmpegAdapter(storage, base / "work")})
        if len(out) != 1 or len(job.media) != 2:
            raise RuntimeError("FACTORY_HANDOFF_FAILED")
        rendered = out[0].outputs[0]
        if rendered not in job.media or rendered.provenance != f"ffmpeg:render:r{job.revision}":
            raise RuntimeError("FACTORY_PROVENANCE_MISMATCH")
        verified = storage.resolve_local(rendered)
        details = inspect_ffprobe(verified, 15)
        digest = hashlib.sha256(verified.read_bytes()).hexdigest()
        if digest != rendered.sha256 or verified.stat().st_size != rendered.size_bytes:
            raise RuntimeError("STORAGE_INTEGRITY_MISMATCH")
        if live_r2 and not rendered.uri.startswith("r2://"):
            raise RuntimeError("NOT_PRIVATE_R2")
        print(f"BLOCK6_FACTORY_FFMPEG_{'LIVE_R2' if live_r2 else 'LOCAL'}_PASS seconds={details['seconds']} tracks={','.join(details['tracks'])} sha256_prefix={digest[:12]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-r2", action="store_true")
    args = parser.parse_args()
    run(live_r2=args.live_r2)
