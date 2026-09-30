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
 def test_video_without_source_uses_pollo(self):
  p=MediaProductionPlanner().plan(self.job(),brief()); self.assertEqual("pollo",p.steps[0].machine)
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
 def test_audience_or_creative_cannot_bypass_canonical_media(self):
  j=self.job(); j.media.append(ref("source"))
  p=MediaProductionPlan(j.job_id,j.revision,"b",(MediaStep("x",MediaStage.EDIT,"m",("forged",)),))
  with self.assertRaises(MediaProductionError): MediaProductionRunner().execute(j,p,{"m":ContractMediaAdapter("m",ref("out"))})
 def test_ffmpeg_requires_input(self):
  with tempfile.TemporaryDirectory() as td:
   a=FFmpegAdapter(LocalScratchStorage(Path(td)/"s"),Path(td)/"w")
   with self.assertRaises(MediaProductionError): a.run(ToolTask("j",1,"x",[]))

if __name__=="__main__": unittest.main()
