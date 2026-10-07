import io
import json
import unittest

from scripts.agent11_private_video_recovery import execute_recovery


def handoff():
    return {
        "schema": "AGENT21-TO-AGENT11-RECOVERY-V1",
        "repair_id": "A21-PRIVATE-VIDEO-001",
        "job_id": "f6f50c9f4c2690e4eb1fe978",
        "stage_id": "video_editor_ffmpeg",
        "machine": "private-media-container",
        "checkpoint": "video_editor_ffmpeg",
        "restart_required": True,
        "requested_action": "RESUME",
    }


class FakeClient:
    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.last = self.statuses[-1]
        self.writes = []

    def get_object(self, Bucket, Key):
        if self.statuses:
            self.last = self.statuses.pop(0)
        return {"Body": io.BytesIO(json.dumps(self.last).encode())}

    def put_object(self, **kwargs):
        self.writes.append(kwargs)
        return {"ETag": '"ok"'}


def status(value, stamp, stage="video_editor_ffmpeg"):
    return {
        "schema": "PRIVATE-VIDEO-STATUS-V1",
        "task_id": "f6f50c9f4c2690e4eb1fe978",
        "status": value,
        "stage": stage,
        "updated_at": stamp,
    }


class Agent11PrivateVideoRecoveryTests(unittest.TestCase):
    def http_ok(self, calls):
        def call(method, path, token, payload=None):
            calls.append((method, path, payload))
            if path == "/admin/container-restart":
                return 202, {"status": "container_restart_requested"}
            if path == "/health":
                return 200, {"ready": True}
            if path == "/private-video/resume-duenya":
                return 202, {"status": "ACCEPTED", "task_id": "f6f50c9f4c2690e4eb1fe978"}
            raise AssertionError(path)
        return call

    def test_failed_job_restarts_then_requires_two_distinct_running_heartbeats(self):
        client = FakeClient([
            status("FAILED", "2026-10-06T21:00:00+00:00"),
            status("RUNNING", "2026-10-06T21:01:00+00:00"),
            status("RUNNING", "2026-10-06T21:01:10+00:00"),
        ])
        calls = []
        result = execute_recovery(client, "bucket", handoff(), "token",
                                  http=self.http_ok(calls), sleeper=lambda _: None)
        self.assertTrue(result["recovered"])
        self.assertNotIn(("POST", "/admin/container-restart", None), calls)
        self.assertFalse(any(call[0:2] == ("GET", "/health") for call in calls[:1]))
        self.assertIn(("POST", "/private-video/jobs", {"task_id": "f6f50c9f4c2690e4eb1fe978"}), calls)
        self.assertEqual(len(client.writes), 1)
        body = json.loads(client.writes[0]["Body"])
        self.assertEqual(body["schema"], "PRODUCTION-RECOVERY-R2-V1")
        self.assertTrue(body["recovered"])
        self.assertNotIn("token", json.dumps(body).lower())

    def test_same_running_record_twice_is_not_two_heartbeats(self):
        client = FakeClient([
            status("FAILED", "2026-10-06T21:00:00+00:00"),
            status("RUNNING", "2026-10-06T21:01:00+00:00"),
            status("RUNNING", "2026-10-06T21:01:00+00:00"),
        ])
        with self.assertRaisesRegex(RuntimeError, "TWO_RUNNING_HEARTBEATS_NOT_PROVEN"):
            execute_recovery(client, "bucket", handoff(), "token", http=self.http_ok([]),
                             sleeper=lambda _: None, max_heartbeat_attempts=2)

    def test_completed_job_never_restarts(self):
        client = FakeClient([status("COMPLETED", "2026-10-06T21:00:00+00:00")])
        calls = []
        result = execute_recovery(client, "bucket", handoff(), "token",
                                  http=self.http_ok(calls), sleeper=lambda _: None)
        self.assertEqual(result["decision"], "NO_RESTART")
        self.assertFalse(result["recovered"])
        self.assertEqual(calls, [])

    def test_failed_again_stops_without_blind_retry(self):
        client = FakeClient([
            status("FAILED", "2026-10-06T21:00:00+00:00"),
            status("FAILED", "2026-10-06T21:01:00+00:00"),
        ])
        with self.assertRaisesRegex(RuntimeError, "JOB_FAILED_AGAIN"):
            execute_recovery(client, "bucket", handoff(), "token",
                             http=self.http_ok([]), sleeper=lambda _: None)

    def test_arbitrary_machine_is_rejected_before_http(self):
        h = handoff()
        h["machine"] = "curl-evil-command"
        client = FakeClient([status("FAILED", "2026-10-06T21:00:00+00:00")])
        with self.assertRaises(ValueError):
            execute_recovery(client, "bucket", h, "token", http=self.http_ok([]), sleeper=lambda _: None)


if __name__ == "__main__":
    unittest.main()
