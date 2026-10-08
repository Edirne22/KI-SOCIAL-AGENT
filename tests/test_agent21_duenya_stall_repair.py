import json
import unittest
from datetime import datetime,timezone

from scripts.agent21_duenya_stall_repair import (
    INCIDENT_KEY, REPAIR_ID, STAGE, STATUS_KEY, TASK_ID, reconcile,
)


class Body:
    def __init__(self,value): self.value=value
    def read(self,n=-1): return json.dumps(self.value).encode()


class R2:
    def __init__(self,state,incident):
        self.state=state; self.incident=incident; self.writes=[]
    def get_object(self,Bucket,Key):
        if Key==STATUS_KEY: return {"Body":Body(self.state)}
        if Key==INCIDENT_KEY: return {"Body":Body(self.incident)}
        raise AssertionError(Key)
    def put_object(self,**kw):
        self.writes.append(kw)


def incident():
    return {
      "schema":"MACHINE-WATCHDOG-INCIDENT-V1",
      "incident_id":f"WD-{TASK_ID}-{STAGE}-v4",
      "job_id":TASK_ID,"stage_id":STAGE,"machine":"private-media-container",
      "checkpoint":STAGE,"last_progress":0,
      "last_heartbeat_at":"2026-10-06T21:00:00+00:00",
      "reason":"MACHINE_REPORTED_STALLED","route_to":"agent21",
      "requested_action":"DIAGNOSE_ONLY",
    }


def state(status="RUNNING",stamp="2026-10-06T21:00:00+00:00",stage=STAGE):
    return {"schema":"PRIVATE-VIDEO-STATUS-V1","task_id":TASK_ID,
            "status":status,"stage":stage,"updated_at":stamp,"production_revision":"v4","runtime_revision":"duenya-creative-chain-v3"}


class Tests(unittest.TestCase):
    def test_stale_running_is_failed_for_guarded_agent11_handoff(self):
        r=R2(state(),incident())
        out=reconcile(r,"b",now=datetime(2026,10,6,21,2,0,tzinfo=timezone.utc))
        self.assertEqual(out["action"],"HANDOFF_AGENT11")
        self.assertEqual(out["repair_id"],REPAIR_ID)
        self.assertEqual(STATUS_KEY, f"ai-central/v1/private-video/{TASK_ID}/revisions/v4/status.json")
        self.assertTrue(INCIDENT_KEY.endswith(f"WD-{TASK_ID}-{STAGE}-v4.json"))
        self.assertIn("-V4", REPAIR_ID)
        self.assertEqual(len(r.writes),1)
        body=json.loads(r.writes[0]["Body"])
        self.assertEqual(body["status"],"FAILED")
        self.assertEqual(body["error_code"],"AGENT21_CONFIRMED_STALLED")
        self.assertEqual(body["production_revision"],"v4")
        self.assertEqual(body["runtime_revision"],"duenya-creative-chain-v3")

    def test_fresh_running_never_gets_restarted(self):
        r=R2(state(stamp="2026-10-06T21:01:30+00:00"),incident())
        out=reconcile(r,"b",now=datetime(2026,10,6,21,2,0,tzinfo=timezone.utc))
        self.assertEqual(out["action"],"NO_RECOVERY")
        self.assertEqual(r.writes,[])

    def test_completed_never_gets_restarted(self):
        r=R2(state(status="COMPLETED",stage="private_preview"),incident())
        out=reconcile(r,"b",now=datetime(2026,10,6,21,2,0,tzinfo=timezone.utc))
        self.assertEqual(out["action"],"NO_RECOVERY")
        self.assertEqual(r.writes,[])

    def test_wrong_incident_fails_closed(self):
        bad=incident(); bad["job_id"]="other-task"
        with self.assertRaisesRegex(RuntimeError,"INCIDENT_INVALID"):
            reconcile(R2(state(),bad),"b",now=datetime(2026,10,6,21,2,0,tzinfo=timezone.utc))


class SourceRegression(unittest.TestCase):
    def test_service_renews_worker_activity_during_private_video_heartbeat(self):
        text=open("infra/private-asr/service.py",encoding="utf-8").read()
        self.assertIn('_private_runtime_origin = "https://edirne22-private-asr.butupeli.workers.dev"',text)
        self.assertIn("def _renew_private_video_activity(",text)
        self.assertIn("if ticks % 3 == 0:",text)
        self.assertIn("_renew_private_video_activity()",text)
        self.assertNotIn('PRIVATE_ASR_SELF_ORIGIN',text)

    def test_recovery_is_gated_by_media_revision_not_whole_deploy_conclusion(self):
        workflow=open(".github/workflows/recover-duenya-after-agent21.yml",encoding="utf-8").read()
        service=open("infra/private-asr/service.py",encoding="utf-8").read()
        self.assertIn('_private_video_runtime_revision = "duenya-creative-chain-v3"',service)
        self.assertIn('"private_video_runtime_revision": _private_video_runtime_revision',service)
        self.assertIn("github.event.workflow_run.head_branch == 'main'",workflow)
        self.assertNotIn("github.event.workflow_run.conclusion == 'success'",workflow)
        self.assertIn("DUENYA_MEDIA_RUNTIME_REVISION_OK",workflow)
        self.assertLess(workflow.index("DUENYA_MEDIA_RUNTIME_REVISION_OK"),
                        workflow.index("Agent 21 validate incident"))
        agent11=open("scripts/agent11_private_video_recovery.py",encoding="utf-8").read()
        self.assertIn("Agent 11 recovery-mode exact Dünya resume",workflow)
        self.assertIn("python -m scripts.agent11_private_video_recovery",workflow)
        self.assertIn('http("POST", "/private-video/jobs", token, resume_payload)',agent11)
        self.assertIn('"production_revision": production_revision',agent11)
        self.assertIn("DUENYA_PRODUCTION_REVISION: v4",workflow)
        self.assertIn('--production-revision "$DUENYA_PRODUCTION_REVISION"',workflow)
        self.assertNotIn("/health?recovery=duenya-level12",workflow)
        self.assertNotIn("/private-video/resume-duenya",agent11)
        self.assertIn("Persist exact V4 watchdog incident before Agent 21",workflow)
        self.assertLess(workflow.index("Persist exact V4 watchdog incident before Agent 21"),
                        workflow.index("Agent 21 validate incident"))
        self.assertIn("max_checks=1",workflow)
        self.assertIn("timeout-minutes: 25",workflow)
        self.assertIn("steps.watchdog.outputs.action == 'HANDOFF_AGENT21'",workflow)


if __name__=="__main__": unittest.main()
