import io,json,unittest
from unittest.mock import patch
from scripts.start_duenya_level12_exact import TASK_ID,start_exact

class Missing(Exception):
    def __init__(self):
        self.response={"Error":{"Code":"NoSuchKey"}}

def task(state="DRAFT_REQUIRES_REVIEW"):
    return {"schema":"AI-INBOX-V1","id":TASK_ID,"kind":"message","message":"PRIVATE VIDEOPRODUKTION: Dünya wird 12.",
            "status":state,"auto_dispatch":False,"created_at":"2026-10-04T12:00:00+00:00"}
def status(state,stamp="2026-10-06T21:00:00+00:00"):
    return {"schema":"PRIVATE-VIDEO-STATUS-V1","task_id":TASK_ID,"status":state,
            "stage":"video_editor_ffmpeg","updated_at":stamp}
class Body:
    def __init__(self,v): self.v=v
    def read(self,n=-1): return json.dumps(self.v).encode()
class Pager:
    def paginate(self,**k): return [{"Contents":[{"Key":"ai-central/v1/inbox/x.json"}]}]
class R2:
    def __init__(self,t,runtime=None): self.t=t;self.runtime=list(runtime or []);self.writes=[]
    def get_paginator(self,n): return Pager()
    def get_object(self,Bucket,Key):
        if Key.endswith("/status.json"):
            if not self.runtime: raise Missing()
            return {"Body":Body(self.runtime.pop(0))}
        return {"Body":Body(self.t),"ETag":'"e1"'}
    def put_object(self,**kw): self.writes.append(kw);return {"ETag":'"e2"'}
class Resp: status_code=202

class ExactStartTests(unittest.TestCase):
    def test_exact_task_claims_and_starts(self):
        r=R2(task(),[status("RUNNING")])
        out=start_exact(r,"b","tok",post=lambda *a,**k:Resp(),sleeper=lambda _:None)
        self.assertEqual(out["result"],"START_RUNNING");self.assertEqual(len(r.writes),1)
        claimed=json.loads(r.writes[0]["Body"]);self.assertEqual(claimed["dispatch_target"],"private-media-container")
    def test_failed_job_routes_to_agent21_without_post(self):
        r=R2(task("QUEUED_PRIVATE_VIDEO"),[status("FAILED")]);calls=[]
        with self.assertRaisesRegex(RuntimeError,"FAILED_NEEDS_AGENT21"):
            start_exact(r,"b","tok",post=lambda *a,**k:calls.append(1),sleeper=lambda _:None)
        self.assertEqual(calls,[])
    def test_running_job_is_not_duplicated(self):
        r=R2(task("QUEUED_PRIVATE_VIDEO"),[status("RUNNING")]);calls=[]
        out=start_exact(r,"b","tok",post=lambda *a,**k:calls.append(1),sleeper=lambda _:None)
        self.assertEqual(out["result"],"ALREADY_RUNNING");self.assertEqual(calls,[])
    def test_wrong_task_shape_fails_closed(self):
        x=task();x["auto_dispatch"]=True
        with self.assertRaisesRegex(RuntimeError,"NOT_AUTHORIZED"):
            start_exact(R2(x),"b","tok",post=lambda *a,**k:Resp(),sleeper=lambda _:None)
if __name__=="__main__":unittest.main()
