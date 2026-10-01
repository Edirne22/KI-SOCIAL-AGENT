"""Block 6 factory adapter for a pinned local Chopify checkout."""
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
    name="chopify"
    truth=ExecutionTruth.LIVE
    def __init__(self,storage:MediaStorageAdapter,chopify_home:Path,*,python_bin:str=sys.executable,runner=None):
        self.storage=storage; self.chopify_home=Path(chopify_home).resolve()
        self.python_bin=python_bin; self.runner=runner or subprocess.run
    def run(self,task:ToolTask)->ToolResult:
        if len(task.inputs)!=1: raise MediaProductionError("chopify requires exactly one source video")
        required=("download_and_transcribe.py","score_clips.py","render_clips.py")
        if any(not (self.chopify_home/n).is_file() for n in required): raise MediaProductionError("chopify checkout is incomplete")
        source=self.storage.resolve_local(task.inputs[0])
        aspect=str(task.parameters.get("aspect","9:16"))
        if aspect not in {"9:16","16:9","1:1"}: raise MediaProductionError("unsupported chopify aspect")
        bridge=Path(__file__).resolve().parent/"scripts"/"chopify_local_bridge.py"
        with tempfile.TemporaryDirectory(prefix="factory-chopify-") as td:
            root=Path(td); work=root/"work"; out=root/"clips"
            local=root/("source"+(source.suffix.lower() or ".mp4")); shutil.copy2(source,local)
            cmd=[self.python_bin,str(bridge),"--home",str(self.chopify_home),"--source",str(local),
                 "--work",str(work),"--out",str(out),"--model",str(task.parameters.get("whisper_model","tiny")),
                 "--aspect",aspect,"--style",str(task.parameters.get("style","podcast")),
                 "--max-clips",str(task.parameters.get("max_clips",3)),
                 "--min-len",str(task.parameters.get("min_len",8)),
                 "--max-len",str(task.parameters.get("max_len",60))]
            p=self.runner(cmd,capture_output=True,text=True,timeout=900,check=False)
            if p.returncode!=0: raise MediaProductionError("chopify bridge failed: "+(p.stderr or p.stdout or "")[-2000:])
            clips=sorted(x for x in out.glob("*.mp4") if x.is_file() and x.stat().st_size)
            if not clips: raise MediaProductionError("chopify produced no clips")
            refs=[self.storage.put_file(x,provenance=f"chopify:{task.task_id}:r{task.revision}",mime_type="video/mp4") for x in clips]
        return ToolResult(task.job_id,task.revision,task.task_id,refs,self.name)
