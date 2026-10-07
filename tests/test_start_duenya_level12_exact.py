import io,json,unittest
from pathlib import Path
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
            value=self.runtime.pop(0)
            if value is None: raise Missing()
            return {"Body":Body(value)}
        return {"Body":Body(self.t),"ETag":'"e1"'}
    def put_object(self,**kw): self.writes.append(kw);return {"ETag":'"e2"'}
class Resp: status_code=202

class ExactStartTests(unittest.TestCase):
    def test_exact_task_claims_and_starts(self):
        r=R2(task(),[None,status("RUNNING")])
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
    def test_workflow_invokes_start_as_module_regression(self):
        text=Path(".github/workflows/start-duenya-level12-exact.yml").read_text(encoding="utf-8")
        self.assertIn("python -m scripts.start_duenya_level12_exact",text)
        self.assertNotIn("python scripts/start_duenya_level12_exact.py",text)

class V3StartTests(unittest.TestCase):
    def setUp(self):
        from scripts.start_duenya_level12_exact import RUNTIME_REVISION
        self.runtime_revision=RUNTIME_REVISION
        self.calls=[]
        self.reads=[]
        self.objects={"ai-central/v1/inbox/x.json":task("QUEUED_PRIVATE_VIDEO")}
        self.root=f"ai-central/v1/private-video/{TASK_ID}"
        self.objects[self.root+"/status.json"]=status("COMPLETED")
        self.objects[self.root+"/preview.json"]={"task_id":TASK_ID,"state":"READY_FOR_HUMAN","r2_key":"private/old.mp4"}
        self.writes=[]
        outer=self
        class Store:
            def get_paginator(self,n): return Pager()
            def get_object(self,Bucket,Key):
                outer.reads.append(Key)
                if Key not in outer.objects: raise Missing()
                return {"Body":Body(outer.objects[Key]),"ETag":'"old"'}
            def put_object(self,**kw):
                outer.writes.append(kw)
                outer.objects[kw["Key"]]=json.loads(kw["Body"])
                return {"ETag":'"saved"'}
        self.store=Store()

    def response(self, body, code=200):
        class Response:
            status_code=code
            def json(self): return body
        return Response()

    def health(self,*a,**kw):
        self.assertFalse(kw["allow_redirects"])
        return self.response({"ready":True,"private_video_runtime_revision":self.runtime_revision})

    def post(self,*a,**kw):
        self.calls.append(kw)
        self.objects[self.root+"/revisions/v3/status.json"]={**status("RUNNING"),"production_revision":"v3","runtime_revision":self.runtime_revision}
        return self.response({"status":"ACCEPTED","task_id":TASK_ID,"production_revision":"v3"},202)

    def start(self,**kw):
        return start_exact(self.store,"b","synthetic",production_revision="v3",get=kw.pop("get",self.health),
                           post=kw.pop("post",self.post),sleeper=lambda _:None,**kw)

    def test_legacy_completed_cannot_hide_v3_start_and_manifests_are_preserved(self):
        old=dict(self.objects[self.root+"/status.json"])
        self.assertEqual(self.start()["result"],"START_RUNNING")
        self.assertEqual(self.calls[0]["json"],{"task_id":TASK_ID,"production_revision":"v3"})
        self.assertEqual(self.objects[self.root+"/revisions/legacy-before-v3/status.json"],old)
        self.assertEqual(self.objects[self.root+"/status.json"],old)
        self.assertTrue(all(w["IfNoneMatch"]=="*" for w in self.writes))
        self.assertEqual(len(self.calls),1)

    def test_wrong_health_revision_not_ready_or_auth_error_never_posts(self):
        for body,code in (({"ready":True,"private_video_runtime_revision":"old"},200),
                          ({"ready":False,"private_video_runtime_revision":self.runtime_revision},200),
                          ({},401)):
            with self.assertRaisesRegex(RuntimeError,"HEALTH_"):
                self.start(get=lambda *a,**k:self.response(body,code))
        self.assertEqual(self.calls,[])
        self.assertEqual(self.writes,[])

    def test_v3_running_is_not_duplicated(self):
        self.objects[self.root+"/revisions/v3/status.json"]={**status("RUNNING"),"production_revision":"v3","runtime_revision":self.runtime_revision}
        self.assertEqual(self.start()["result"],"ALREADY_RUNNING")
        self.assertEqual(self.calls,[])
        self.assertEqual(self.writes,[])

    def test_old_revision_in_v3_slot_is_rejected(self):
        for revision in (None,"v2"):
            self.objects[self.root+"/revisions/v3/status.json"]={**status("COMPLETED"),"production_revision":revision,"runtime_revision":self.runtime_revision}
            with self.assertRaisesRegex(RuntimeError,"REVISION_MISMATCH"): self.start()
        self.assertEqual(self.calls,[])

    def test_acceptance_must_identify_exact_task_revision_and_active_status(self):
        for body in ({"status":"COMPLETED","task_id":TASK_ID,"production_revision":"v3"},
                     {"status":"ACCEPTED","task_id":TASK_ID,"production_revision":"v2"},
                     {"status":"ACCEPTED","task_id":"another","production_revision":"v3"},
                     {"status":"ACCEPTED","task_id":TASK_ID},[]):
            with self.assertRaisesRegex(RuntimeError,"ACCEPTANCE_NOT_PROVEN"):
                self.start(post=lambda *a,**k:self.response(body,202))

    def test_existing_archive_is_not_overwritten_and_failure_blocks_post(self):
        from scripts.start_duenya_level12_exact import _archive_previous
        class Exists(Exception):
            response={"Error":{"Code":"PreconditionFailed"}}
        old_write=self.store.put_object
        def exists(**kw): raise Exists()
        self.store.put_object=exists
        _archive_previous(self.store,"b")
        self.store.put_object=lambda **kw: (_ for _ in ()).throw(RuntimeError("storage unavailable"))
        with self.assertRaisesRegex(RuntimeError,"storage unavailable"):
            self.start()
        self.assertEqual(self.calls,[])
        self.store.put_object=old_write

    def test_uncertain_post_is_never_retried(self):
        import requests
        def uncertain(*a,**kw):
            self.calls.append(kw)
            raise requests.Timeout()
        with self.assertRaisesRegex(RuntimeError,"DISPATCH_UNCERTAIN"):
            self.start(post=uncertain)
        self.assertEqual(len(self.calls),1)


if __name__ == "__main__": unittest.main()
