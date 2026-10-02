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

def run(*, live_r2: bool, register_preview: bool = False):
    if register_preview and not live_r2:
        raise ValueError('dashboard registration requires real private R2, not scratch storage')
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
        if register_preview:
            # Source remains in private R2 as verified input, never part of
            # the approval media set. Only the actual FFmpeg OUTPUT is shown.
            from content_factory_golden_tablet import FinalQM, QMCheck
            from content_factory_dashboard_preview import register_verified_video_preview
            job.metadata[f"input_source_provenance:r{job.revision}"] = {
                "media_id": source.media_id, "sha256": source.sha256, "uri": source.uri
            }
            job.media = [rendered]
            job.metadata[f"creative_package:r{job.revision}"] = {
                "draft": {"caption": "EDIRNE 22 – TECHNISCHES TESTVIDEO (NICHT VERÖFFENTLICHEN)"}
            }
            # These checks prove only the locked synthetic fixture,
            # 15-second FFmpeg audio/video and private R2 integrity, never
            # editorial/source-fact clearance for a real social post.
            job.transition(JobStatus.RENDERING)
            job.transition(JobStatus.QM)
            report = FinalQM().evaluate(job, [
                QMCheck("test_fixture", SOURCE.is_file() and SOURCE.stat().st_size > 0),
                QMCheck("actual_ffprobe_15s_av", details["seconds"] == 15 and
                        set(details["tracks"]) == {"audio", "video"}),
                QMCheck("actual_private_r2_roundtrip", verified.is_file() and
                        digest == rendered.sha256 and verified.stat().st_size == rendered.size_bytes),
            ])
            if not report.passed:
                raise RuntimeError("SYNTHETIC_PREVIEW_QM_FAILED")
            preview_id = register_verified_video_preview(job, report, storage=storage)
            print(f"BLOCK6_DASHBOARD_PREVIEW_REGISTERED id={preview_id} job={job.job_id} "
                  f"revision={job.revision} synthetic_test_only=true")
        print(f"BLOCK6_FACTORY_FFMPEG_{'LIVE_R2' if live_r2 else 'LOCAL'}_PASS seconds={details['seconds']} tracks={','.join(details['tracks'])} sha256_prefix={digest[:12]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-r2", action="store_true")
    parser.add_argument("--register-preview", action="store_true")
    args = parser.parse_args()
    run(live_r2=args.live_r2, register_preview=args.register_preview)
