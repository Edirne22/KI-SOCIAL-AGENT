import hashlib, unittest
from content_factory_core import *
from content_factory_av import *

def ref(mid): return MediaRef(mid,f"scratch://{mid}",hashlib.sha256(mid.encode()).hexdigest(),1,"audio/mpeg","test")
def job():
 j=ProductionJob("av"); j.transition(JobStatus.INGESTING); j.transition(JobStatus.RESEARCHING); j.transition(JobStatus.WRITING); j.transition(JobStatus.STORYBOARDING); return j
def registry(): return VoiceRegistry([VoiceProfile("buelent-authorized","Bülent",("de","tr"),"consent:owner")])

class Block7(unittest.TestCase):
 def test_authorized_de_voice(self):
  p=AVPlanner(registry()).create(job(),script="Hallo Racing-Fans",language="de",voice_id="buelent-authorized"); self.assertEqual("de",p.language)
 def test_unauthorized_voice_blocked(self):
  with self.assertRaises(AVError): AVPlanner(registry()).create(job(),script="x",language="de",voice_id="celebrity")
 def test_missing_consent_blocked(self):
  r=VoiceRegistry([VoiceProfile("x","x",("de",),"")])
  with self.assertRaises(AVError): AVPlanner(r).create(job(),script="x",language="de",voice_id="x")
 def test_language_scope_blocked(self):
  with self.assertRaises(AVError): AVPlanner(registry()).create(job(),script="x",language="en",voice_id="buelent-authorized")
 def test_caption_overlap_blocked(self):
  with self.assertRaises(AVError): AVPlanner(registry()).create(job(),script="x",language="de",voice_id="buelent-authorized",cues=[CaptionCue(0,1000,"a"),CaptionCue(900,1500,"b")])
 def test_bad_caption_rejected(self):
  with self.assertRaises(ValueError): CaptionCue(10,10,"x")
 def test_cross_job_plan_blocked(self):
  j=job(); p=AVPlanner(registry()).create(j,script="x",language="de",voice_id="buelent-authorized")
  with self.assertRaises(AVError): execute_av(job(),p,voice_machine=ContractAVAdapter("voice",ref("v")))
 def test_avatar_requires_machine(self):
  j=job(); p=AVPlanner(registry()).create(j,script="x",language="de",voice_id="buelent-authorized",avatar_mode="paddock")
  with self.assertRaises(AVError): execute_av(j,p,voice_machine=ContractAVAdapter("voice",ref("v")))
 def test_voice_avatar_chain(self):
  j=job(); p=AVPlanner(registry()).create(j,script="x",language="tr",voice_id="buelent-authorized",avatar_mode="paddock")
  out=execute_av(j,p,voice_machine=ContractAVAdapter("voice",ref("v")),avatar_machine=ContractAVAdapter("avatar",ref("a")))
  self.assertEqual(("v","a"),tuple(x.outputs[0].media_id for x in out))
 def test_truth_label_simulated(self): self.assertEqual(AVTruth.SIMULATED,ContractAVAdapter("voice",ref("v")).truth)
 def test_attach_immutable(self):
  j=job(); p=AVPlanner(registry()).create(j,script="x",language="de",voice_id="buelent-authorized"); attach_narration(j,p); attach_narration(j,p)
  q=AVPlanner(registry()).create(j,script="anderer text",language="de",voice_id="buelent-authorized")
  with self.assertRaises(AVError): attach_narration(j,q)
 def test_finalized_mutation_blocked(self):
  j=job(); p=AVPlanner(registry()).create(j,script="x",language="de",voice_id="buelent-authorized"); j.status=JobStatus.READY_FOR_HUMAN
  with self.assertRaises(AVError): attach_narration(j,p)
 def test_stale_revision_blocked(self):
  j=job(); p=AVPlanner(registry()).create(j,script="x",language="de",voice_id="buelent-authorized"); j.revision+=1
  with self.assertRaises(AVError): execute_av(j,p,voice_machine=ContractAVAdapter("voice",ref("v")))
if __name__=="__main__": unittest.main()
