import unittest
from scripts.production_machine_watchdog import inspect

def sample(status="RUNNING",progress=42):
    return {"job_id":"media-job-003","stage_id":"ffmpeg-render","machine":"private-media-container",
      "checkpoint":"segment-005","status":status,"heartbeat_at":"2026-10-05T12:20:00Z","progress":progress}

class MachineWatchdogTests(unittest.TestCase):
    def test_running_is_observation_only(self):
        r=inspect(sample())
        self.assertEqual(r["decision"],"OBSERVE")
    def test_failure_routes_to_agent21_only(self):
        r=inspect(sample("FAILED"))
        self.assertEqual(r["route_to"],"agent21")
        self.assertEqual(r["requested_action"],"DIAGNOSE_ONLY")
        self.assertEqual(r["checkpoint"],"segment-005")
    def test_stall_routes_to_agent21(self):
        self.assertEqual(inspect(sample("STALLED"))["reason"],"MACHINE_REPORTED_STALLED")
    def test_unknown_machine_fails_closed(self):
        s=sample();s["machine"]="arbitrary-shell"
        with self.assertRaises(ValueError): inspect(s)
    def test_extra_command_field_rejected(self):
        s=sample("FAILED");s["command"]="anything"
        with self.assertRaises(ValueError): inspect(s)
    def test_invalid_progress_rejected(self):
        with self.assertRaises(ValueError): inspect(sample(progress=101))

if __name__=="__main__": unittest.main()
