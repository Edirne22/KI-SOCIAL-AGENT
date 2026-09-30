import unittest
from content_factory_core import *
from content_factory_golden_tablet import *
from content_factory_control_center import *

def queued():
 j=ProductionJob("x"); j.status=JobStatus.QM; j.metadata["creative_package:r1"]={"draft":{"caption":"Toprak gewann."}}
 r=FinalQM().evaluate(j,[QMCheck("all",True)]); t=present_golden_tablet(j,r); HumanDecisionService().post(j,t); return j
class Block9(unittest.TestCase):
 def test_unapproved_publish_blocked(self):
  j=ProductionJob("x")
  with self.assertRaises(ControlCenterError): PublisherBridge().publish(j,platform="instagram",publisher=ContractPublisher())
 def test_publish_is_idempotent_per_handoff_platform(self):
  j=queued(); b=PublisherBridge(); p=ContractPublisher(); a=b.publish(j,platform="instagram",publisher=p); c=b.publish(j,platform="instagram",publisher=p); self.assertEqual(a,c)
 def test_two_platforms_get_distinct_receipts(self):
  j=queued(); b=PublisherBridge(); p=ContractPublisher(); a=b.publish(j,platform="instagram",publisher=p); c=b.publish(j,platform="facebook",publisher=p); self.assertNotEqual(a.external_id,c.external_id)
 def test_bad_receipt_correlation_blocked(self):
  class Evil:
   name="evil"
   def publish(self,j,p,k): return PublishReceipt("wrong",p,"x","proof")
  with self.assertRaises(ControlCenterError): PublisherBridge().publish(queued(),platform="instagram",publisher=Evil())
 def test_publish_completion_requires_proof(self):
  j=queued()
  with self.assertRaises(ControlCenterError): PublisherBridge().mark_complete(j,[])
 def test_complete_sets_published_and_proof(self):
  j=queued(); b=PublisherBridge(); r=b.publish(j,platform="instagram",publisher=ContractPublisher()); b.mark_complete(j,[r]); self.assertEqual(JobStatus.PUBLISHED,j.status); self.assertIn("publish_proof:r1",j.metadata)
 def test_web_and_telegram_share_same_authority_boundary(self):
  j=ProductionJob("x"); j.status=JobStatus.READY_FOR_HUMAN
  c=ControlCenter()
  for ch in ("web","telegram"): self.assertTrue(c.validate(j,ControlRequest(ch,ch,"buelent","post",j.job_id,j.revision)))
 def test_nonhuman_actor_blocked(self):
  j=ProductionJob("x"); j.status=JobStatus.READY_FOR_HUMAN
  with self.assertRaises(ControlCenterError): ControlCenter().validate(j,ControlRequest("1","web","bot","post",j.job_id,j.revision))
 def test_stale_revision_control_blocked(self):
  j=ProductionJob("x"); j.status=JobStatus.READY_FOR_HUMAN
  with self.assertRaises(ControlCenterError): ControlCenter().validate(j,ControlRequest("1","web","buelent","post",j.job_id,99))
 def test_contract_publisher_truth_explicit(self): self.assertEqual("SIMULATED",ContractPublisher.truth)
 def test_duplicate_publish_after_published_blocked(self):
  j=queued(); b=PublisherBridge(); r=b.publish(j,platform="instagram",publisher=ContractPublisher()); b.mark_complete(j,[r])
  with self.assertRaises(ControlCenterError): b.publish(j,platform="instagram",publisher=ContractPublisher())
if __name__=="__main__": unittest.main()
