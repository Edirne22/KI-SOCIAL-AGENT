import hashlib, unittest
from content_factory_core import *
from content_factory_golden_tablet import *

def ready_qm():
 j=ProductionJob("x"); j.status=JobStatus.QM
 j.metadata["creative_package:r1"]={"draft":{"caption":"Toprak gewann."}}
 return j
def report(j,ok=True): return FinalQM().evaluate(j,[QMCheck("facts",ok),QMCheck("render",ok)],audience_advisory=["SIMULATED: hook clarity"])
class Block8(unittest.TestCase):
 def test_pass_reaches_golden_tablet(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); self.assertEqual(JobStatus.READY_FOR_HUMAN,j.status); self.assertEqual("Toprak gewann.",t.caption)
 def test_failed_qm_blocked(self):
  j=ready_qm()
  with self.assertRaises(GoldenTabletError): present_golden_tablet(j,report(j,False))
 def test_audience_is_advisory_only(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); self.assertIn("SIMULATED",t.audience_advisory[0]); self.assertEqual(JobStatus.READY_FOR_HUMAN,j.status)
 def test_machine_cannot_approve(self):
  j=ready_qm(); present_golden_tablet(j,report(j))
  with self.assertRaises(PermissionError): j.transition(JobStatus.APPROVED,actor="system")
 def test_post_is_final_human_authority_and_queues(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); key=HumanDecisionService().post(j,t); self.assertEqual(JobStatus.PUBLISH_QUEUED,j.status); self.assertTrue(key)
 def test_no_second_ai_gate_after_post(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); HumanDecisionService().post(j,t)
  self.assertEqual(JobStatus.PUBLISH_QUEUED,j.status)
  with self.assertRaises(ValueError): j.transition(JobStatus.QM)
 def test_payload_tamper_after_preview_blocked(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); j.publish_payload["caption"]="tampered"
  with self.assertRaises(GoldenTabletError): HumanDecisionService().post(j,t)
 def test_media_tamper_after_preview_blocked(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); j.media.append(MediaRef("x","scratch://x","0"*64,1,"image/png","evil"))
  with self.assertRaises(GoldenTabletError): HumanDecisionService().post(j,t)
 def test_stale_tablet_after_change_blocked(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); HumanDecisionService().change(j,t,"caption ändern"); self.assertEqual(2,j.revision)
  with self.assertRaises(GoldenTabletError): HumanDecisionService().post(j,t)
 def test_discard_is_human_final(self):
  j=ready_qm(); t=present_golden_tablet(j,report(j)); HumanDecisionService().discard(j,t); self.assertEqual(JobStatus.REJECTED,j.status)
 def test_cross_job_report_blocked(self):
  a=ready_qm(); b=ready_qm(); r=report(a)
  with self.assertRaises(GoldenTabletError): present_golden_tablet(b,r)
 def test_missing_creative_blocked(self):
  j=ProductionJob("x"); j.status=JobStatus.QM; r=FinalQM().evaluate(j,[QMCheck("facts",True)])
  with self.assertRaises(GoldenTabletError): present_golden_tablet(j,r)
if __name__=="__main__": unittest.main()
