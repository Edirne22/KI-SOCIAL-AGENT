import io
import json
import unittest
from datetime import datetime, timezone

from scripts.watch_duenya_level12_production import TASK_ID, watch


class Body:
    def __init__(self, value): self.value=value
    def read(self, n=-1): return json.dumps(self.value).encode()


class R2:
    def __init__(self, statuses, preview=None):
        self.statuses=list(statuses); self.last=self.statuses[-1] if self.statuses else None
        self.preview=preview; self.writes=[]
    def get_object(self, Bucket, Key):
        if Key.endswith("/status.json"):
            if self.statuses: self.last=self.statuses.pop(0)
            return {"Body":Body(self.last)}
        if Key.endswith("/preview.json"):
            return {"Body":Body(self.preview)}
        raise AssertionError(Key)
    def put_object(self, **kwargs):
        self.writes.append(kwargs); return {"ETag":'"ok"'}


def status(state, stamp, stage="video_editor_ffmpeg", **extra):
    return {"schema":"PRIVATE-VIDEO-STATUS-V1","task_id":TASK_ID,"status":state,
            "stage":stage,"updated_at":stamp,**extra}


def preview():
    return {"schema":"PRIVATE-VIDEO-PREVIEW-V1","task_id":TASK_ID,"state":"READY_FOR_HUMAN",
            "r2_key":"private/v1/productions/duenya-level-12-deadbeef.mp4",
            "sha256":"a"*64,"private":True,"publishable":False}


class WatchTests(unittest.TestCase):
    def test_completed_requires_private_nonpublishable_preview(self):
        r=R2([status("COMPLETED","2026-10-06T21:58:00+00:00","private_preview")],preview())
        out=watch(r,"b",sleeper=lambda _:None,now_fn=lambda:datetime(2026,10,6,21,58,1,tzinfo=timezone.utc),max_checks=1)
        self.assertEqual(out["status"],"COMPLETED")
        self.assertTrue(out["preview"]["private"]); self.assertFalse(out["preview"]["publishable"])

    def test_failed_routes_once_to_agent21_without_restart(self):
        r=R2([status("FAILED","2026-10-06T21:58:00+00:00",error_code="RuntimeError",detail="bounded failure")])
        out=watch(r,"b",sleeper=lambda _:None,now_fn=lambda:datetime(2026,10,6,21,58,1,tzinfo=timezone.utc),max_checks=1)
        self.assertEqual(out["status"],"FAILED"); self.assertEqual(len(r.writes),1)
        body=json.loads(r.writes[0]["Body"])
        self.assertEqual(body["route_to"],"agent21"); self.assertEqual(body["requested_action"],"DIAGNOSE_ONLY")
        self.assertNotIn("Authorization",json.dumps(body))

    def test_stale_running_becomes_agent21_stalled_incident(self):
        r=R2([status("RUNNING","2026-10-06T21:56:00+00:00")])
        out=watch(r,"b",sleeper=lambda _:None,now_fn=lambda:datetime(2026,10,6,21,58,0,tzinfo=timezone.utc),
                  max_checks=1,stall_after_seconds=75)
        self.assertEqual(out["status"],"STALLED"); self.assertEqual(len(r.writes),1)

    def test_live_running_then_completed(self):
        r=R2([
            status("RUNNING","2026-10-06T21:58:00+00:00"),
            status("COMPLETED","2026-10-06T21:58:15+00:00","private_preview"),
        ],preview())
        times=iter([
            datetime(2026,10,6,21,58,1,tzinfo=timezone.utc),
            datetime(2026,10,6,21,58,16,tzinfo=timezone.utc),
        ])
        out=watch(r,"b",sleeper=lambda _:None,now_fn=lambda:next(times),max_checks=2)
        self.assertEqual(out["status"],"COMPLETED")


if __name__=="__main__": unittest.main()
