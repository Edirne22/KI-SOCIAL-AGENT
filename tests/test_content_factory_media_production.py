import hashlib, tempfile, unittest
from pathlib import Path
from content_factory_core import *
from content_factory_creative import *
from content_factory_media_production import *
from media_storage import LocalScratchStorage

def brief(fmt=ContentFormat.REEL):
 return CreativeBrief("b","p",fmt,("instagram",),"hook","angle",(StoryBeat("x","fact",("c",),"visual"),),("c",),"de")
def ref(mid,data=b"x"):
 return MediaRef(mid,f"scratch://{mid}",hashlib.sha256(data).hexdigest(),len(data),"video/mp4","test")

class Block6Tests(unittest.TestCase):
 def job(self):
  j=ProductionJob("media"); j.transition(JobStatus.INGESTING); j.transition(JobStatus.RESEARCHING); j.transition(JobStatus.WRITING); j.transition(JobStatus.STORYBOARDING); return j
 def test_video_plan_prefers_supoclip_edit_ffmpeg(self):
  j=self.job(); j.media.append(ref("source")); p=MediaProductionPlanner().plan(j,brief())
  self.assertEqual(("supoclip","openchatcut","ffmpeg"),tuple(x.machine for x in p.steps))
 def test_video_without_source_uses_live_agnes(self):
  p=MediaProductionPlanner().plan(self.job(),brief()); self.assertEqual("agnes_video",p.steps[0].machine)
  self.assertEqual("hook | angle | visual",dict(p.steps[0].parameters)["prompt"])
 def test_live_agnes_video_adapter_stores_immutable_media(self):
  calls=[]
  def generator(prompt): calls.append(prompt); return b"mp4-bytes"
  with tempfile.TemporaryDirectory() as td:
   storage=LocalScratchStorage(Path(td)/"s"); a=AgnesVideoAdapter(storage,generator)
   result=a.run(ToolTask("j",4,"generate",[],{"prompt":"vertical moto scene"})); media=result.outputs[0]
   self.assertEqual(ExecutionTruth.LIVE,a.truth); self.assertEqual(["vertical moto scene"],calls)
   self.assertEqual("video/mp4",media.mime_type); self.assertEqual("agnes_video:generate:r4",media.provenance)
   self.assertEqual(hashlib.sha256(b"mp4-bytes").hexdigest(),media.sha256)
   self.assertEqual(b"mp4-bytes",storage.resolve_local(media).read_bytes())
 def test_live_agnes_video_rejects_inputs_empty_prompt_and_empty_result(self):
  with tempfile.TemporaryDirectory() as td:
   a=AgnesVideoAdapter(LocalScratchStorage(Path(td)/"s"),lambda p:b"x")
   with self.assertRaises(MediaProductionError): a.run(ToolTask("j",1,"x",[ref("foreign")],{"prompt":"x"}))
   with self.assertRaises(MediaProductionError): a.run(ToolTask("j",1,"x",[],{"prompt":" "}))
   b=AgnesVideoAdapter(LocalScratchStorage(Path(td)/"s2"),lambda p:None)
   with self.assertRaises(MediaProductionError): b.run(ToolTask("j",1,"x",[],{"prompt":"x"}))
 def test_image_without_source_uses_live_image_router(self):
  p=MediaProductionPlanner().plan(self.job(),brief(ContentFormat.IMAGE))
  self.assertEqual("image_router",p.steps[0].machine)
  self.assertEqual("hook | angle | visual",dict(p.steps[0].parameters)["prompt"])
 def test_live_image_router_adapter_stores_immutable_media(self):
  class Router:
   def generate_image(self,prompt):
    self.prompt=prompt; return b"png-bytes"
  with tempfile.TemporaryDirectory() as td:
   router=Router(); storage=LocalScratchStorage(Path(td)/"s"); a=ImageRouterAdapter(storage,router)
   t=ToolTask("j",3,"generate",[],{"prompt":"race image"})
   result=a.run(t); media=result.outputs[0]
   self.assertEqual(ExecutionTruth.LIVE,a.truth)
   self.assertEqual("race image",router.prompt)
   self.assertEqual("image/png",media.mime_type)
   self.assertEqual("image_router:generate:r3",media.provenance)
   self.assertEqual(hashlib.sha256(b"png-bytes").hexdigest(),media.sha256)
   self.assertEqual(b"png-bytes",storage.resolve_local(media).read_bytes())
 def test_live_image_router_rejects_inputs_and_empty_prompt(self):
  with tempfile.TemporaryDirectory() as td:
   class Router:
    def generate_image(self,prompt): return b"x"
   a=ImageRouterAdapter(LocalScratchStorage(Path(td)/"s"),Router())
   with self.assertRaises(MediaProductionError): a.run(ToolTask("j",1,"x",[ref("foreign")],{"prompt":"x"}))
   with self.assertRaises(MediaProductionError): a.run(ToolTask("j",1,"x",[],{"prompt":" "}))
 def test_image_router_staffellauf_attaches_output_to_job(self):
  class Router:
   def generate_image(self,prompt): return b"factory-image"
  with tempfile.TemporaryDirectory() as td:
   j=self.job(); p=MediaProductionPlanner().plan(j,brief(ContentFormat.IMAGE))
   a=ImageRouterAdapter(LocalScratchStorage(Path(td)/"s"),Router())
   out=MediaProductionRunner().execute(j,p,{"image_router":a})
   self.assertEqual(1,len(out)); self.assertEqual(1,len(j.media))
   self.assertEqual(out[0].outputs[0],j.media[0])
 def test_post_needs_no_media_machine(self):
  self.assertEqual((),MediaProductionPlanner().plan(self.job(),brief(ContentFormat.POST)).steps)
 def test_plan_cross_job_rejected(self):
  j=self.job(); p=MediaProductionPlan("evil",j.revision,"b",())
  with self.assertRaises(MediaProductionError): MediaProductionRunner().execute(j,p,{})
 def test_foreign_media_id_rejected(self):
  j=self.job(); p=MediaProductionPlan(j.job_id,j.revision,"b",(MediaStep("x",MediaStage.EDIT,"m",("foreign",)),))
  with self.assertRaises(MediaProductionError): MediaProductionRunner().execute(j,p,{"m":ContractMediaAdapter("m",ref("o"))})
 def test_machine_provenance_mismatch_blocked_by_handoff(self):
  class Evil:
   name="expected"; truth=ExecutionTruth.SIMULATED
   def run(self,t): return ToolResult(t.job_id,t.revision,t.task_id,[ref("o")],"liar")
  j=self.job(); p=MediaProductionPlan(j.job_id,j.revision,"b",(MediaStep("x",MediaStage.EDIT,"expected",()),))
  with self.assertRaises(HandoffError): MediaProductionRunner().execute(j,p,{"expected":Evil()})
 def test_media_id_collision_blocked(self):
  j=self.job(); j.media.append(ref("same",b"a"))
  p=MediaProductionPlan(j.job_id,j.revision,"b",(MediaStep("x",MediaStage.EDIT,"m",()),))
  with self.assertRaises(HandoffError): MediaProductionRunner().execute(j,p,{"m":ContractMediaAdapter("m",ref("same",b"b"))})
 def test_simulated_adapter_truth_is_explicit(self):
  self.assertEqual(ExecutionTruth.SIMULATED,ContractMediaAdapter("supoclip",ref("x")).truth)
 def test_attach_plan_immutable(self):
  j=self.job(); p=MediaProductionPlanner().plan(j,brief(ContentFormat.POST)); attach_media_plan(j,p); attach_media_plan(j,p)
  q=MediaProductionPlan(j.job_id,j.revision,"other",())
  with self.assertRaises(MediaProductionError): attach_media_plan(j,q)
 def test_finalized_job_cannot_attach(self):
  j=self.job(); p=MediaProductionPlanner().plan(j,brief(ContentFormat.POST)); j.status=JobStatus.READY_FOR_HUMAN
  with self.assertRaises(MediaProductionError): attach_media_plan(j,p)
 def test_contract_staffellauf_outputs_chain(self):
  j=self.job(); j.media.append(ref("source"))
  p=MediaProductionPlanner().plan(j,brief())
  machines={"supoclip":ContractMediaAdapter("supoclip",ref("clip")),
            "openchatcut":ContractMediaAdapter("openchatcut",ref("master")),
            "ffmpeg":ContractMediaAdapter("ffmpeg",ref("render"))}
  out=MediaProductionRunner().execute(j,p,machines)
  self.assertEqual(("clip","master","render"),tuple(r.outputs[0].media_id for r in out))
  self.assertEqual(4,len(j.media))
 def test_stale_revision_rejected(self):
  j=self.job(); p=MediaProductionPlanner().plan(j,brief()); j.revision+=1
  with self.assertRaises(MediaProductionError): MediaProductionRunner().execute(j,p,{})
 def test_ffmpeg_requires_input(self):
  with tempfile.TemporaryDirectory() as td:
   a=FFmpegAdapter(LocalScratchStorage(Path(td)/"s"),Path(td)/"w")
   with self.assertRaises(MediaProductionError): a.run(ToolTask("j",1,"x",[]))

if __name__=="__main__": unittest.main()
