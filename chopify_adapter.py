"""Block 6 LIVE Chopify bridge.

The upstream tool stays external and replaceable. This adapter binds immutable
factory MediaRefs to a pinned/self-hosted Chopify checkout without vendoring it.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from content_factory_handoff import ToolResult, ToolTask
from content_factory_media_production import ExecutionTruth, MediaProductionError
from media_storage import MediaStorageAdapter


class ChopifyAdapter:
    name = "chopify"
    truth = ExecutionTruth.LIVE

    def __init__(self, storage: MediaStorageAdapter, chopify_home: Path, *, python_bin: str = sys.executable, runner=None):
        self.storage = storage
        self.chopify_home = Path(chopify_home).resolve()
        self.python_bin = python_bin
        self.runner = runner or subprocess.run

    def _run(self, cmd: list[str], *, cwd: Path) -> None:
        result = self.runner(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=900, check=False)
        if result.returncode != 0:
            tail = (result.stderr or result.stdout or "")[-2000:]
            raise MediaProductionError(f"chopify stage failed: {tail}")

    def run(self, task: ToolTask) -> ToolResult:
        if len(task.inputs) != 1:
            raise MediaProductionError("chopify requires exactly one source video")
        required = ("download_and_transcribe.py", "score_clips.py", "render_clips.py")
        if any(not (self.chopify_home / name).is_file() for name in required):
            raise MediaProductionError("chopify checkout is incomplete")

        source = self.storage.resolve_local(task.inputs[0])
        model = str(task.parameters.get("whisper_model", "tiny")).strip() or "tiny"
        aspect = str(task.parameters.get("aspect", "9:16")).strip() or "9:16"
        style = str(task.parameters.get("style", "podcast")).strip() or "podcast"
        if aspect not in {"9:16", "16:9", "1:1"}:
            raise MediaProductionError("unsupported chopify aspect")

        with tempfile.TemporaryDirectory(prefix="factory-chopify-") as td:
            root = Path(td)
            work = root / "work"
            out = root / "clips"
            work.mkdir(); out.mkdir()
            local_source = work / ("source" + (source.suffix.lower() or ".mp4"))
            shutil.copy2(source, local_source)

            code = (
                "import sys; from pathlib import Path; "
                "sys.path.insert(0,sys.argv[1]); "
                "from download_and_transcribe import transcribe; "
                "transcribe(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4],'cpu','int8')"
            )
            self._run([self.python_bin, "-c", code, str(self.chopify_home), str(local_source), str(work), model], cwd=self.chopify_home)
            self._run([
                self.python_bin, str(self.chopify_home / "score_clips.py"), str(work),
                "--max-clips", str(task.parameters.get("max_clips", 3)),
                "--min-len", str(task.parameters.get("min_len", 8)),
                "--max-len", str(task.parameters.get("max_len", 60)),
            ], cwd=self.chopify_home)
            self._run([
                self.python_bin, str(self.chopify_home / "render_clips.py"), str(work),
                "--aspect", aspect, "--style", style, "--out", str(out.resolve()),
            ], cwd=self.chopify_home)

            clips = sorted(p for p in out.glob("*.mp4") if p.is_file() and p.stat().st_size)
            if not clips:
                raise MediaProductionError("chopify produced no clips")
            refs = [
                self.storage.put_file(
                    clip,
                    provenance=f"chopify:{task.task_id}:r{task.revision}",
                    mime_type="video/mp4",
                )
                for clip in clips
            ]
        return ToolResult(task.job_id, task.revision, task.task_id, refs, self.name)
