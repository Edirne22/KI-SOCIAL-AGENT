import hashlib, tempfile, unittest
from pathlib import Path
from chopify_adapter import ChopifyAdapter
from content_factory_handoff import ToolTask
from content_factory_media_production import ExecutionTruth, MediaProductionError
from media_storage import LocalScratchStorage

class Result:
 def __init__(self,code=0): self.returncode=code; self.stdout=""; self.stderr=""

class ChopifyAdapterTests(unittest.TestCase):
 def test_truth_and_input_guard(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); home=root/"c"; home.mkdir()
   for n in ("download_and_transcribe.py","score_clips.py","render_clips.py"): (home/n).write_text("# fixture\n")
   a=ChopifyAdapter(LocalScratchStorage(root/"s"),home,runner=lambda *a,**k:Result())
   self.assertEqual(ExecutionTruth.LIVE,a.truth)
   with self.assertRaises(MediaProductionError): a.run(ToolTask("j",1,"clip",[],{}))
 def test_persists_bridge_output(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); home=root/"c"; home.mkdir()
   for n in ("download_and_transcribe.py","score_clips.py","render_clips.py"): (home/n).write_text("# fixture\n")
   storage=LocalScratchStorage(root/"s"); src=root/"in.mp4"; src.write_bytes(b"video")
   ref=storage.put_file(src,provenance="test",mime_type="video/mp4")
   def runner(cmd,**kwargs):
    out=Path(cmd[cmd.index("--out")+1]); out.mkdir(parents=True,exist_ok=True); (out/"clip.mp4").write_bytes(b"rendered"); return Result()
   result=ChopifyAdapter(storage,home,runner=runner).run(ToolTask("j",2,"clip",[ref],{"aspect":"9:16"}))
   media=result.outputs[0]
   self.assertEqual("chopify",result.machine); self.assertEqual("chopify:clip:r2",media.provenance)
   self.assertEqual(hashlib.sha256(b"rendered").hexdigest(),media.sha256)
   self.assertEqual(b"rendered",storage.resolve_local(media).read_bytes())

if __name__=="__main__": unittest.main()
