import unittest
from scripts.production_recovery_contract import recovery_decision,healthy_after_restart

def handoff(action="RESUME"):
    return {"schema":"AGENT21-TO-AGENT11-RECOVERY-V1","repair_id":"A21-FAULT-001",
      "job_id":"duenya-job-001","stage_id":"ffmpeg-render","machine":"private-media-container",
      "checkpoint":"segment-012","restart_required":True,"requested_action":action}

class RecoveryContractTests(unittest.TestCase):
    def test_valid_resume(self):
        state={"job_id":"duenya-job-001","stage_id":"ffmpeg-render","checkpoint":"segment-012","status":"FAILED"}
        self.assertEqual(recovery_decision(handoff(),state)["decision"],"RESUME")
    def test_completed_never_restarts(self):
        state={"job_id":"duenya-job-001","stage_id":"ffmpeg-render","checkpoint":"segment-012","status":"COMPLETED"}
        self.assertEqual(recovery_decision(handoff("RESTART_JOB"),state)["decision"],"NO_RESTART")
    def test_active_never_duplicates(self):
        state={"job_id":"duenya-job-001","stage_id":"ffmpeg-render","checkpoint":"segment-012","status":"RUNNING"}
        self.assertEqual(recovery_decision(handoff("RESTART_JOB"),state)["decision"],"OBSERVE_ONLY")
    def test_wrong_job_rejected(self):
        state={"job_id":"other-job","stage_id":"ffmpeg-render","checkpoint":"segment-012","status":"FAILED"}
        with self.assertRaises(ValueError): recovery_decision(handoff(),state)
    def test_arbitrary_machine_rejected(self):
        h=handoff();h["machine"]="curl-evil-command"
        state={"job_id":"duenya-job-001","stage_id":"ffmpeg-render","checkpoint":"segment-012","status":"FAILED"}
        with self.assertRaises(ValueError): recovery_decision(h,state)
    def test_extra_field_rejected(self):
        h=handoff();h["command"]="rm-anything"
        state={"job_id":"duenya-job-001","stage_id":"ffmpeg-render","checkpoint":"segment-012","status":"FAILED"}
        with self.assertRaises(ValueError): recovery_decision(h,state)
    def test_checkpoint_mismatch_rejected(self):
        state={"job_id":"duenya-job-001","stage_id":"ffmpeg-render","checkpoint":"segment-999","status":"FAILED"}
        with self.assertRaises(ValueError): recovery_decision(handoff(),state)
    def test_cancelled_never_restarts(self):
        state={"job_id":"duenya-job-001","stage_id":"ffmpeg-render","checkpoint":"segment-012","status":"CANCELLED"}
        self.assertEqual(recovery_decision(handoff("RESTART_JOB"),state)["decision"],"NO_RESTART")
    def test_two_healthy_heartbeats_required(self):
        one=[{"container_ready":True,"machine_ready":True,"job_status":"RUNNING"}]
        two=one+one
        self.assertFalse(healthy_after_restart(one))
        self.assertTrue(healthy_after_restart(two))
    def test_unhealthy_sample_breaks_streak(self):
        samples=[
          {"container_ready":True,"machine_ready":True,"job_status":"RUNNING"},
          {"container_ready":False,"machine_ready":True,"job_status":"RUNNING"},
          {"container_ready":True,"machine_ready":True,"job_status":"RUNNING"}]
        self.assertFalse(healthy_after_restart(samples))

if __name__=="__main__":unittest.main()
