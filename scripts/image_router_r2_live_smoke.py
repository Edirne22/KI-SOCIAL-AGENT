"""Live smoke: existing ImageRouter -> factory adapter -> private R2 -> verified download."""
from pathlib import Path
import tempfile

from content_factory_handoff import ToolTask
from content_factory_media_production import ImageRouterAdapter, ExecutionTruth
from image_router import ImageRouter
from media_storage import R2Storage

PROMPT = "Editorial motorcycle racing image, red sport motorcycle on a race track, no logos, no text"

with tempfile.TemporaryDirectory(prefix="image-r2-live-") as td:
    root=Path(td)
    storage=R2Storage.from_env(cache_root=root/"cache")
    adapter=ImageRouterAdapter(storage,ImageRouter())
    if adapter.truth != ExecutionTruth.LIVE:
        raise RuntimeError("image adapter is not LIVE")
    task=ToolTask("live-image-r2-smoke",1,"generate",[],{"prompt":PROMPT,"language":"de"})
    result=adapter.run(task)
    if len(result.outputs) != 1:
        raise RuntimeError("expected exactly one media output")
    media=result.outputs[0]
    if not media.uri.startswith("r2://"):
        raise RuntimeError("output was not persisted to private R2")
    local=storage.resolve_local(media)
    if local.stat().st_size != media.size_bytes or storage._sha256(local) != media.sha256:
        raise RuntimeError("downloaded image integrity mismatch")
    print("IMAGE ROUTER -> FACTORY ADAPTER -> R2 -> SHA-256: PASS")
