"""Live smoke: Agnes video API -> factory adapter -> private R2 -> verified download."""
from pathlib import Path
import tempfile
from content_factory_handoff import ToolTask
from content_factory_media_production import AgnesVideoAdapter, ExecutionTruth
from media_storage import R2Storage

PROMPT="Cinematic vertical 9:16 motorcycle travel scene on a winding European road at golden hour, no logos, no text, no real racer, 7 seconds"

with tempfile.TemporaryDirectory(prefix="agnes-video-r2-live-") as td:
    storage=R2Storage.from_env(cache_root=Path(td)/"cache")
    adapter=AgnesVideoAdapter(storage)
    if adapter.truth != ExecutionTruth.LIVE:
        raise RuntimeError("Agnes video adapter is not LIVE")
    result=adapter.run(ToolTask("live-agnes-video-r2",1,"generate",[],{"prompt":PROMPT,"language":"de"}))
    if len(result.outputs)!=1:
        raise RuntimeError("expected exactly one video output")
    media=result.outputs[0]
    if media.mime_type!="video/mp4" or not media.uri.startswith("r2://"):
        raise RuntimeError("video was not persisted as private R2 MP4")
    local=storage.resolve_local(media)
    if local.stat().st_size!=media.size_bytes or storage._sha256(local)!=media.sha256:
        raise RuntimeError("downloaded video integrity mismatch")
    print("AGNES VIDEO -> FACTORY ADAPTER -> R2 -> SHA-256: PASS")
