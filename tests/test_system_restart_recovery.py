import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import system_restart_agent as agent

def handoff():
    return {"schema":"AGENT21-TO-AGENT11-RECOVERY-V1","repair_id":"A21-FAULT-002",
      "job_id":"media-job-002","stage_id":"ffmpeg-render","machine":"private-media-container",
      "checkpoint":"segment-004","restart_required":True,"requested_action":"RESUME"}

class Agent11RecoveryTests(unittest.TestCase):
    def test_failed_job_requires_machine_action(self):
        current={"job_id":"media-job-002","stage_id":"ffmpeg-render","checkpoint":"segment-004","status":"FAILED"}
        result=agent.assess_production_recovery(handoff(),current,[])
        self.assertEqual(result["decision"],"RESUME")
        self.assertFalse(result["recovered"])

    def test_running_requires_two_healthy_heartbeats(self):
        current={"job_id":"media-job-002","stage_id":"ffmpeg-render","checkpoint":"segment-004","status":"RUNNING"}
        hb={"container_ready":True,"machine_ready":True,"job_status":"RUNNING"}
        self.assertFalse(agent.assess_production_recovery(handoff(),current,[hb])["recovered"])
        self.assertTrue(agent.assess_production_recovery(handoff(),current,[hb,hb])["recovered"])

    def test_completed_never_reports_recovered(self):
        current={"job_id":"media-job-002","stage_id":"ffmpeg-render","checkpoint":"segment-004","status":"COMPLETED"}
        hb={"container_ready":True,"machine_ready":True,"job_status":"RUNNING"}
        result=agent.assess_production_recovery(handoff(),current,[hb,hb])
        self.assertEqual(result["decision"],"NO_RESTART")
        self.assertFalse(result["recovered"])

    def test_log_contains_metadata_not_handoff_extras(self):
        result={"decision":"RESUME","reason":"VALIDATED_RECOVERY","recovered":False}
        with tempfile.TemporaryDirectory() as td:
            with patch.object(agent,"RECOVERY_LOG_PATH",Path(td)/"recovery.jsonl"):
                path=agent.log_production_recovery(handoff(),result)
                text=path.read_text(encoding="utf-8")
        self.assertIn("A21-FAULT-002",text)
        self.assertNotIn("Authorization",text)
        self.assertNotIn("token",text.lower())

if __name__=="__main__": unittest.main()
