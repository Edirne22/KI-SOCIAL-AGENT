"""Synthetic tests only: no real Telegram or private media.\n\nFinal Telegram acceptance touch: 2026-10-04.\n"""
import io
import json
import unittest
from unittest.mock import patch
from scripts.telegram_private_media import receive

class Missing(Exception):
    response={"Error":{"Code":"NoSuchKey"}}

class R2:
    def __init__(self):self.data={}
    def get_object(self,*,Bucket,Key):
        if Key not in self.data:raise Missing()
        return {"Body":io.BytesIO(self.data[Key]),"ETag":'"fake"'}
    def put_object(self,*,Bucket,Key,Body,**kw):
        if kw.get("IfNoneMatch")=="*" and Key in self.data:
            class Precondition(Exception):
                response={"Error":{"Code":"PreconditionFailed"}}
            raise Precondition()
        self.data[Key]=Body
    def list_objects_v2(self,*,Bucket,Prefix,**kw):
        return {"Contents":[{"Key":k} for k in self.data if k.startswith(Prefix)]}
    def delete_object(self,*,Bucket,Key):
        self.data.pop(Key,None)

class Reply:
    def __init__(self,info=False):self.info=info
    def raise_for_status(self):pass
    def json(self):return {"ok":True,"result":{"file_path":"photos/synthetic.jpg","file_size":9}}
    def iter_content(self,chunk_size):yield b"synthetic"

def get(url,**kwargs):return Reply()

class AlbumTests(unittest.TestCase):
    def test_caption_then_uncaptioned_album_shared_private_manifest(self):
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"abc123","date":1791059000}
        a={**base,"caption":"/privat","photo":[{"file_id":"a"}]}
        b={**base,"photo":[{"file_id":"b"}]}
        receive(a,update_id=200,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        receive(b,update_id=201,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        manifests=[json.loads(v) for k,v in r2.data.items() if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),2)
        self.assertEqual(manifests[0]["lane"],"private")
        self.assertTrue(all(k.startswith("private/") for k in r2.data))
    def test_uncaptioned_without_private_manifest_quarantined(self):
        r2=R2()
        b={"chat":{"id":42},"media_group_id":"abc123","date":1791059000,"photo":[{"file_id":"b"}]}
        reply=receive(b,update_id=201,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        self.assertIn("zurückgehalten",reply)
        self.assertTrue(any("/quarantine/" in k for k in r2.data))
        self.assertFalse(any(k.endswith("manifest.json") for k in r2.data))
    def test_out_of_order_album_item_requires_explicit_replay(self):
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"abc123","date":1791059000}
        first={**base,"photo":[{"file_id":"b"}]}
        captioned={**base,"caption":"/privat","photo":[{"file_id":"a"}]}
        self.assertIn("zurückgehalten",receive(first,update_id=201,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42))
        receive(captioned,update_id=200,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        self.assertFalse(any("/quarantine/" in k for k in r2.data))
        manifests=[json.loads(v) for k,v in r2.data.items() if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),2)

    def test_repeated_update_does_not_duplicate_asset(self):
        r2=R2()
        msg={"chat":{"id":42},"media_group_id":"abc123","date":1791059000,"caption":"/privat","photo":[{"file_id":"a"}]}
        receive(msg,update_id=200,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        result=receive(msg,update_id=200,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        self.assertIn("bereits gespeichert",result)
        manifests=[json.loads(v) for k,v in r2.data.items() if k.endswith("manifest.json")]
        self.assertEqual(len(manifests[0]["assets"]),1)

    def test_router_does_not_exit_after_first_album_item(self):
        from pathlib import Path
        router=Path("telegram_router.py").read_text()
        section=router.split("# Intercept albums before legacy Vision processing;",1)[1].split("if _is_photo_message(upd):",1)[0]
        self.assertNotIn("return",section)
        self.assertGreaterEqual(section.count("continue"),2)

    def test_other_chat_rejected(self):
        with self.assertRaises(PermissionError):
            receive({"chat":{"id":99},"caption":"/privat","photo":[{"file_id":"a"}]},update_id=1,token="synthetic",authorized_chat=42)

    def test_interrupted_original_write_recovers_without_overwrite(self):
        from scripts.r2_media_warehouse import new_manifest, store_original
        from datetime import datetime, timezone
        class Precondition(Exception):
            response={"Error":{"Code":"PreconditionFailed"}}
        class StrictR2(R2):
            def put_object(self,*,Bucket,Key,Body,**kw):
                if kw.get("IfNoneMatch")=="*" and Key in self.data:
                    raise Precondition()
                super().put_object(Bucket=Bucket,Key=Key,Body=Body,**kw)
        r2=StrictR2()
        manifest=new_manifest(lane="private",title="test",job_id="recoverytest12345",
                              created_at=datetime(2026,10,3,tzinfo=timezone.utc))
        from scripts.r2_media_warehouse import append_asset
        _,key=append_asset(manifest,asset_id="file1234567890",filename="a.jpg",
                           mime="image/jpeg",payload=b"synthetic")
        r2.data[key]=b"synthetic"  # Original persisted, manifest interrupted.
        updated=store_original(r2,"test",manifest,asset_id="file1234567890",
                               filename="a.jpg",mime="image/jpeg",payload=b"synthetic")
        self.assertEqual(len(updated["assets"]),1)
        self.assertEqual(r2.data[key],b"synthetic")

    def test_interrupted_original_collision_fails_closed(self):
        from scripts.r2_media_warehouse import new_manifest, store_original, append_asset
        from datetime import datetime, timezone
        class Precondition(Exception):
            response={"Error":{"Code":"PreconditionFailed"}}
        class StrictR2(R2):
            def put_object(self,*,Bucket,Key,Body,**kw):
                if kw.get("IfNoneMatch")=="*" and Key in self.data:
                    raise Precondition()
                super().put_object(Bucket=Bucket,Key=Key,Body=Body,**kw)
        r2=StrictR2()
        manifest=new_manifest(lane="private",title="test",job_id="recoverytest12345",
                              created_at=datetime(2026,10,3,tzinfo=timezone.utc))
        _,key=append_asset(manifest,asset_id="file1234567890",filename="a.jpg",
                           mime="image/jpeg",payload=b"synthetic")
        r2.data[key]=b"tampered"
        with self.assertRaisesRegex(RuntimeError,"immutable original collision"):
            store_original(r2,"test",manifest,asset_id="file1234567890",
                           filename="a.jpg",mime="image/jpeg",payload=b"synthetic")
        self.assertEqual(r2.data[key],b"tampered")


    def test_quarantine_limit_rejects_new_item_but_allows_retry(self):
        from scripts.telegram_private_media import MAX_QUARANTINE_ITEMS
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"bounded","date":1791059000}
        for i in range(MAX_QUARANTINE_ITEMS):
            receive({**base,"photo":[{"file_id":str(i)}]},update_id=1000+i,
                    token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        receive({**base,"photo":[{"file_id":"0"}]},update_id=1000,
                token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        with self.assertRaisesRegex(ValueError,"quarantine limit"):
            receive({**base,"photo":[{"file_id":"extra"}]},update_id=9999,
                    token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        self.assertEqual(len([k for k in r2.data if "/quarantine/" in k]),MAX_QUARANTINE_ITEMS)

    def test_invalid_group_and_unsupported_uncaptioned_mime_rejected(self):
        r2=R2()
        with self.assertRaises(ValueError):
            receive({"chat":{"id":42},"media_group_id":"../bad","date":1791059000,
                     "photo":[{"file_id":"x"}]},update_id=1,token="synthetic",
                    client=r2,bucket="test",get=get,authorized_chat=42)
        with self.assertRaises(ValueError):
            receive({"chat":{"id":42},"media_group_id":"safe","date":1791059000,
                     "document":{"file_id":"x","mime_type":"application/x-executable"}},
                    update_id=2,token="synthetic",client=r2,bucket="test",
                    get=get,authorized_chat=42)
        self.assertFalse(r2.data)

    def test_oversize_download_fails_without_manifest(self):
        class Large(Reply):
            def json(self):
                return {"ok":True,"result":{"file_path":"photos/synthetic.jpg",
                                              "file_size":20*1024*1024}}
        r2=R2()
        with self.assertRaisesRegex(ValueError,"zu groß"):
            receive({"chat":{"id":42},"caption":"/privat","photo":[{"file_id":"x"}]},
                    update_id=2,token="synthetic",client=r2,bucket="test",
                    get=lambda *args,**kwargs:Large(),authorized_chat=42)
        self.assertFalse(r2.data)


    def test_parallel_manifest_conflict_reloads_and_preserves_both(self):
        from scripts.r2_media_warehouse import new_manifest, store_original
        from datetime import datetime, timezone
        from hashlib import sha256
        class Conflict(Exception):
            response={"Error":{"Code":"PreconditionFailed"}}
        class RacingR2(R2):
            def __init__(self):
                super().__init__()
                self.injected=False
                self.manifest_key=None
            def get_object(self,*,Bucket,Key):
                result=super().get_object(Bucket=Bucket,Key=Key)
                if Key.endswith("manifest.json"):
                    result["ETag"]='"'+sha256(self.data[Key]).hexdigest()+'"'
                return result
            def put_object(self,*,Bucket,Key,Body,**kw):
                if kw.get("IfMatch"):
                    current='"'+sha256(self.data[Key]).hexdigest()+'"'
                    if not self.injected:
                        self.injected=True
                        # Simulate another upload committing between read and CAS.
                        previous=json.loads(self.data[Key])
                        previous["assets"].append({"asset_id":"file_parallel","key":"synthetic"})
                        self.data[Key]=json.dumps(previous).encode()
                        current='"'+sha256(self.data[Key]).hexdigest()+'"'
                    if kw["IfMatch"]!=current:
                        raise Conflict()
                return super().put_object(Bucket=Bucket,Key=Key,Body=Body,**kw)
        r2=RacingR2()
        manifest=new_manifest(lane="private",title="parallel",job_id="paralleltest12345",
                              created_at=datetime(2026,10,3,tzinfo=timezone.utc))
        store_original(r2,"test",manifest,asset_id="file_first12345",
                       filename="first.jpg",mime="image/jpeg",payload=b"first")
        msg={"chat":{"id":42},"media_group_id":"paralleltest",
             "date":1791059000,"caption":"/privat","photo":[{"file_id":"second"}]}
        # Use same manifest key as the Telegram album.
        from scripts.telegram_private_media import receive
        album={"chat":{"id":42},"media_group_id":"paralleltest",
               "date":1791059000,"caption":"/privat","photo":[{"file_id":"first"}]}
        r2=RacingR2()
        receive(album,update_id=10,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        receive(msg,update_id=11,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        manifests=[json.loads(v) for k,v in r2.data.items() if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),3)
        self.assertIn("file_parallel",{a["asset_id"] for a in manifests[0]["assets"]})


    def test_router_end_to_end_private_ack_after_r2_commit(self):
        # Execute the real router main function with synthetic Telegram and R2.
        import ast
        from pathlib import Path
        from scripts.telegram_private_media import receive
        tree=ast.parse(Path("telegram_router.py").read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        namespace={}
        exec(compile(ast.Module(body=[main],type_ignores=[]),"telegram_router.py","exec"),namespace)
        r2=R2()
        sent=[]
        acked=[]
        base={"chat":{"id":42},"media_group_id":"routere2e","date":1791059000}
        updates=[
            {"update_id":11,"message":{**base,"photo":[{"file_id":"first"}]}},
            {"update_id":12,"message":{**base,"caption":"/privat","photo":[{"file_id":"second"}]}}
        ]
        namespace.update({
            "get_chat_id":lambda:42,
            "_read_last_update_id":lambda:10,
            "get_updates":lambda **kw:updates if kw.get("offset")==11 else [],
            "_ack":lambda uid:acked.append(uid),
            "receive_private_media":lambda msg,**kw:receive(msg,client=r2,bucket="test",get=get,**kw),
            "send_message":lambda msg:sent.append(msg),
            "os":type("FakeOS",(),{"environ":{"TELEGRAM_BOT_TOKEN":"synthetic"}})(),
        })
        namespace["main"]()
        manifests=[json.loads(v) for k,v in r2.data.items() if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),2)
        self.assertEqual(acked,[11,12])
        self.assertTrue(any("Privat in R2 gespeichert" in s for s in sent))
        self.assertTrue(all(k.startswith("private/") for k in r2.data))

    def test_router_does_not_ack_transient_r2_failure(self):
        import ast
        from pathlib import Path
        tree=ast.parse(Path("telegram_router.py").read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        ns={}
        exec(compile(ast.Module(body=[main],type_ignores=[]),"telegram_router.py","exec"),ns)
        acked=[]
        ns.update({
            "get_chat_id":lambda:42,
            "_read_last_update_id":lambda:10,
            "get_updates":lambda **kw:[{"update_id":11,"message":{
                "chat":{"id":42},"media_group_id":"fail","date":1791059000,
                "caption":"/privat","photo":[{"file_id":"first"}]}}],
            "_ack":lambda uid:acked.append(uid),
            "receive_private_media":lambda *args,**kwargs:(_ for _ in ()).throw(RuntimeError("R2 offline")),
            "send_message":lambda msg:None,
            "os":__import__("os"),
        })
        with self.assertRaisesRegex(RuntimeError,"R2 offline"):
            ns["main"]()
        self.assertFalse(acked)


    def test_album_crossing_utc_midnight_stays_single_job(self):
        r2=R2()
        from datetime import datetime,timezone
        first=int(datetime(2026,10,3,23,59,59,tzinfo=timezone.utc).timestamp())
        second=first+2
        base={"chat":{"id":42},"media_group_id":"midnightalbum"}
        receive({**base,"date":first,"caption":"/privat","photo":[{"file_id":"first"}]},
                update_id=100,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        receive({**base,"date":second,"photo":[{"file_id":"second"}]},
                update_id=101,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        manifests=[json.loads(v) for k,v in r2.data.items() if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1,"Same Telegram album must not split at midnight")
        self.assertEqual(len(manifests[0]["assets"]),2)


    def test_live_metadata_verifier_positive_and_negative_guards(self):
        from hashlib import sha256
        from scripts.telegram_private_album_live_verify import verify

        class MetadataR2(R2):
            def __init__(self):
                super().__init__()
                self.mime = {}
            def put_object(self, *, Bucket, Key, Body, **kw):
                out = super().put_object(Bucket=Bucket, Key=Key, Body=Body, **kw)
                self.mime[Key] = kw.get("ContentType")
                return out
            def head_object(self, *, Bucket, Key):
                if Key not in self.data:
                    raise Missing()
                return {"ContentLength": len(self.data[Key]),
                        "ContentType": self.mime.get(Key)}
        r2 = MetadataR2()
        base = {"chat": {"id": 42}, "media_group_id": "liveverifier",
                "date": 1791059000}
        for ident, uid, caption in (("first", 400, "/privat"),
                                    ("second", 401, None)):
            message = {**base, "photo": [{"file_id": ident}]}
            if caption:
                message["caption"] = caption
            receive(message, update_id=uid, token="synthetic", client=r2,
                    bucket="test", get=get, authorized_chat=42)
        job_id = "tgalbum" + sha256(b"42:liveverifier").hexdigest()[:32]
        actual = verify(r2, "test", job_id=job_id, expected_count=2)
        self.assertEqual(len(actual["assets"]), 2)
        with self.assertRaisesRegex(RuntimeError, "LIVE_ASSET_COUNT_MISMATCH"):
            verify(r2, "test", job_id=job_id, expected_count=3)
        first_key = actual["assets"][0]["key"]
        r2.mime[first_key] = "text/plain"
        with self.assertRaisesRegex(RuntimeError, "LIVE_ORIGINAL_HEAD_MISMATCH"):
            verify(r2, "test", job_id=job_id, expected_count=2)
        r2.mime[first_key] = "image/jpeg"
        r2.data[actual["prefix"] + "quarantine/test.json"] = b'{}'
        with self.assertRaisesRegex(RuntimeError, "LIVE_UNREPLAYED_QUARANTINE"):
            verify(r2, "test", job_id=job_id, expected_count=2)
        r2.data.pop(actual["prefix"] + "quarantine/test.json")
        r2.data[actual["prefix"] + "rejected/filebad.json"] = b'{}'
        with self.assertRaisesRegex(RuntimeError, "LIVE_ALBUM_HAS_REJECTED_FILE"):
            verify(r2, "test", job_id=job_id, expected_count=2)


    def test_boto3_supports_conditional_manifest_writes(self):
        # A fake R2 can support headers which the installed botocore lacks.
        # Fail during premerge CI rather than only in the real R2 run.
        from botocore.session import Session
        members = Session().get_service_model("s3").operation_model("PutObject").input_shape.members
        self.assertIn("IfNoneMatch", members)
        self.assertIn("IfMatch", members)


    def test_real_r2_script_offline_dry_run_not_live(self):
        # Run the real acceptance script against a locking CAS fake. This
        # detects broken orchestration before the opt-in LIVE run with secrets.
        # Capture the LIVE success marker so fake success cannot appear in CI logs.
        import contextlib
        import os
        import threading
        from hashlib import sha256
        from pathlib import Path
        from scripts import telegram_private_album_real_r2_smoke as smoke

        class Conflict(Exception):
            response = {"Error": {"Code": "PreconditionFailed"}}

        class StrictR2(R2):
            def __init__(self):
                super().__init__()
                self.lock = threading.RLock()
            def get_object(self, *, Bucket, Key):
                with self.lock:
                    obj = super().get_object(Bucket=Bucket, Key=Key)
                    obj["ETag"] = '"' + sha256(self.data[Key]).hexdigest() + '"'
                    return obj
            def put_object(self, *, Bucket, Key, Body, **kw):
                with self.lock:
                    if (kw.get("IfNoneMatch") == "*" and Key in self.data):
                        raise Conflict()
                    if kw.get("IfMatch"):
                        if Key not in self.data:
                            raise Conflict()
                        etag = '"' + sha256(self.data[Key]).hexdigest() + '"'
                        if kw["IfMatch"] != etag:
                            raise Conflict()
                    self.data[Key] = bytes(Body)
            def list_objects_v2(self, *, Bucket, Prefix, **kw):
                with self.lock:
                    return super().list_objects_v2(Bucket=Bucket, Prefix=Prefix, **kw)
            def delete_object(self, *, Bucket, Key):
                with self.lock:
                    return super().delete_object(Bucket=Bucket, Key=Key)

        fake = StrictR2()
        def fake_ffmpeg(command, **kw):
            name = Path(command[-1])
            name.write_bytes(b"synthetic-image" if name.suffix == ".jpg"
                             else b"synthetic-video")

        captured = io.StringIO()
        with (
            patch.object(smoke, "client_from_env", return_value=(fake, "offline")),
            patch.object(smoke.subprocess, "run", side_effect=fake_ffmpeg),
            patch.dict(os.environ, {"TELEGRAM_ALBUM_REAL_R2_SYNTHETIC_APPROVED": "true"}),
            contextlib.redirect_stdout(captured),
        ):
            smoke.main()
        self.assertIn("cas_concurrency=yes", captured.getvalue())
        self.assertEqual(
            len([k for k in fake.data if k.endswith("manifest.json")]), 1)
        manifests = [json.loads(v) for k, v in fake.data.items()
                     if k.endswith("manifest.json")]
        self.assertEqual(len(manifests[0]["assets"]), 5)


    def test_real_incident_getfile_http_400_oversize_is_permanent_and_private(self):
        # Real incident: Bot API rejects getFile before returning file_size,
        # despite two other private album files already being acknowledged.
        import requests
        class TooLarge:
            status_code = 400
            def json(self):
                return {"ok": False, "error_code": 400,
                        "description": "Bad Request: file is too big"}
            def raise_for_status(self):
                raise requests.HTTPError("https://api.telegram.org/botSECRET/getFile?file_id=PRIVATE")
        from scripts.telegram_private_media import download
        with self.assertRaises(ValueError) as cm:
            download("PRIVATE", "SECRET", get=lambda *args,**kw:TooLarge())
        self.assertIn("Dashboard-Upload", str(cm.exception))
        self.assertNotIn("SECRET", str(cm.exception))
        self.assertNotIn("PRIVATE", str(cm.exception))
        r2 = R2()
        base={"chat":{"id":42},"media_group_id":"size-incident","date":1791059000}
        receive({**base,"caption":"/privat","photo":[{"file_id":"ok1"}]},
                update_id=80, token="synthetic",client=r2,bucket="test",
                get=get,authorized_chat=42)
        response=receive({**base,"video":{"file_id":"oversized","mime_type":"video/mp4"}},
                         update_id=81,token="SECRET",client=r2,bucket="test",
                         get=lambda *args,**kw:TooLarge(),authorized_chat=42)
        self.assertIn("Downloadlimit",response)
        self.assertIn("1 Datei(en) abgewiesen",response)
        self.assertNotIn("SECRET",response)
        self.assertEqual(len([k for k in r2.data if "/rejected/" in k]),1)
        receive({**base,"photo":[{"file_id":"ok2"}]},
                update_id=82,token="synthetic",client=r2,bucket="test",
                get=get,authorized_chat=42)
        manifests=[json.loads(v) for k,v in r2.data.items() if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),2)
        self.assertEqual(manifests[0]["lane"],"private")

    def test_unknown_bot_getfile_400_cannot_poison_or_leak_credentials(self):
        import requests
        from scripts.telegram_private_media import download
        class BadFile:
            status_code=400
            def json(self):
                return {"ok":False,"error_code":400,"description":"Bad Request: wrong file identifier"}
            def raise_for_status(self):
                raise requests.HTTPError("botPRIVATE_TOKEN/getFile?file_id=PRIVATE_FILE")
        with self.assertRaises(ValueError) as cm:
            download("PRIVATE_FILE","PRIVATE_TOKEN",get=lambda *args,**kw:BadFile())
        self.assertNotIn("PRIVATE_TOKEN",str(cm.exception))
        self.assertNotIn("PRIVATE_FILE",str(cm.exception))

    def test_transient_getfile_http_503_retryable_without_token_exposure(self):
        import requests
        from scripts.telegram_private_media import download
        class ServerDown:
            status_code=503
            def json(self):
                return {"ok":False,"error_code":503,"description":"temporarily unavailable"}
            def raise_for_status(self):
                raise requests.HTTPError("botSECRET/getFile?file_id=SENSITIVE")
        with self.assertRaises(RuntimeError) as cm:
            download("SENSITIVE","SECRET",get=lambda *args,**kw:ServerDown())
        self.assertIn("erneuter Versuch",str(cm.exception))
        self.assertNotIn("SECRET",str(cm.exception))
        self.assertNotIn("SENSITIVE",str(cm.exception))

    def test_router_acknowledges_permanent_file_error_and_processes_next_update(self):
        import ast
        from pathlib import Path
        tree=ast.parse(Path("telegram_router.py").read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        ns={}
        exec(compile(ast.Module(body=[main],type_ignores=[]),"telegram_router.py","exec"),ns)
        handled=[]
        acked=[]
        replies=[]
        updates=[
            {"update_id":81,"message":{"chat":{"id":42},"media_group_id":"incident",
                                        "date":1791059000,
                                        "video":{"file_id":"too-big","mime_type":"video/mp4"}}},
            {"update_id":82,"message":{"chat":{"id":42},"media_group_id":"incident",
                                        "date":1791059000,
                                        "photo":[{"file_id":"following"}]}}
        ]
        def fake_receive(msg,**kwargs):
            handled.append(msg)
            if msg.get("video"):
                raise ValueError("Telegram-Datei überschreitet das Bot-Downloadlimit")
            return "Privat in R2 gespeichert · synthetic"
        ns.update({
            "get_chat_id":lambda:42,
            "_read_last_update_id":lambda:80,
            "get_updates":lambda **kw:updates if kw.get("offset")==81 else [],
            "_ack":lambda uid:acked.append(uid),
            "receive_private_media":fake_receive,
            "send_message":lambda msg:replies.append(msg),
            "os":__import__("os"),
        })
        ns["main"]()
        self.assertEqual(acked,[81,82])
        self.assertEqual(len(handled),2)
        self.assertIn("Bot-Downloadlimit",replies[0])
        self.assertIn("Privat in R2 gespeichert",replies[1])


    def test_oversized_pre_caption_video_is_durably_rejected_and_does_not_block_album(self):
        # A pre-caption video quarantined before a small owner-captioned
        # photo must not poison later photo processing if getFile returns 400.
        import requests
        class TooLarge:
            status_code = 400
            def json(self):
                return {"ok":False,"error_code":400,
                        "description":"Bad Request: file is too big"}
            def raise_for_status(self):
                raise requests.HTTPError("botSECRET/getFile?file_id=PRIVATE")
        def fake_get(url, **kw):
            if kw.get("params",{}).get("file_id") == "oversized":
                return TooLarge()
            return get(url,**kw)
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"quarantine-large",
              "date":1791059000}
        self.assertIn("zurückgehalten",receive(
            {**base,"video":{"file_id":"oversized","mime_type":"video/mp4"}},
            update_id=201,token="synthetic",client=r2,bucket="test",
            get=fake_get,authorized_chat=42))
        result=receive(
            {**base,"caption":"/privat","photo":[{"file_id":"owner-photo"}]},
            update_id=202,token="synthetic",client=r2,bucket="test",
            get=fake_get,authorized_chat=42)
        self.assertIn("Privat in R2 gespeichert",result)
        self.assertIn("dauerhaft abgewiesen",result)
        next_result=receive(
            {**base,"photo":[{"file_id":"second-photo"}]},
            update_id=203,token="synthetic",client=r2,bucket="test",
            get=fake_get,authorized_chat=42)
        self.assertIn("Privat in R2 gespeichert",next_result)
        self.assertEqual(len([k for k in r2.data if "/quarantine/" in k]),0)
        self.assertEqual(len([k for k in r2.data if "/rejected/" in k]),1)
        manifests=[json.loads(v) for k,v in r2.data.items()
                   if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),2)
        self.assertEqual(manifests[0]["lane"],"private")


    def test_file_stream_http_failure_never_leaks_bot_token(self):
        import requests
        from scripts.telegram_private_media import download
        class FileUnavailable:
            status_code=503
            def raise_for_status(self):
                raise requests.HTTPError("https://api.telegram.org/file/botSECRET/privatepath")
        def fake_get(url, **kwargs):
            if url.endswith("/getFile"):
                return Reply()
            return FileUnavailable()
        with self.assertRaises(RuntimeError) as cm:
            download("FILEID","SECRET",get=fake_get)
        self.assertNotIn("SECRET",str(cm.exception))
        self.assertNotIn("privatepath",str(cm.exception))
        self.assertIn("erneuter Versuch",str(cm.exception))

    def test_getfile_network_failure_does_not_ack_or_log_token(self):
        import requests
        from scripts.telegram_private_media import download
        def fake_get(url, **kwargs):
            raise requests.ConnectionError("https://api.telegram.org/botSECRET/getFile")
        with self.assertRaises(RuntimeError) as cm:
            download("PRIVATE","SECRET",get=fake_get)
        self.assertNotIn("SECRET",str(cm.exception))
        self.assertNotIn("PRIVATE",str(cm.exception))
        self.assertIn("erneuter Versuch",str(cm.exception))


    def test_oversized_caption_leaves_album_authorized_for_following_items(self):
        # Previously the rejected leading video created no manifest, so all
        # valid following members were permanently left in quarantine.
        from scripts.telegram_private_media import handle_private_command
        from hashlib import sha256
        from datetime import datetime, timezone
        import requests
        class TooLarge:
            status_code = 400
            def json(self):
                return {"ok":False, "error_code":400,
                        "description":"Bad Request: file is too big"}
            def raise_for_status(self):
                raise requests.HTTPError("botSECRET/getFile")
        def get_mixed(url, **kw):
            if (kw.get("params") or {}).get("file_id") == "large-video":
                return TooLarge()
            return get(url, **kw)
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"leading-oversized",
              "date":int(datetime.now(timezone.utc).timestamp())}
        lead={**base,"caption":"/privat",
              "video":{"file_id":"large-video","mime_type":"video/mp4"}}
        msg=receive(lead, update_id=100, token="synthetic",
                    client=r2,bucket="test",get=get_mixed,authorized_chat=42)
        self.assertIn("Downloadlimit",msg)
        job="tgalbum"+sha256(b"42:leading-oversized").hexdigest()[:32]
        self.assertIn(job,msg)
        self.assertTrue(any(k.endswith("authorization.json") for k in r2.data))
        self.assertFalse(any(k.endswith("manifest.json") for k in r2.data))
        following={**base, "photo":[{"file_id":"small-photo"}]}
        received=receive(following, update_id=101, token="synthetic",
                         client=r2,bucket="test",get=get_mixed,authorized_chat=42)
        self.assertIn("Privat in R2 gespeichert",received)
        manifests=[json.loads(v) for k,v in r2.data.items()
                   if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),1)
        self.assertEqual(len([k for k in r2.data if "/rejected/" in k]),1)
        self.assertEqual(len([k for k in r2.data if "/quarantine/" in k]),0)
        # Do not offer already authorized/recovered albums as new pending.
        answer=handle_private_command("/privat offene",chat=42,authorized_chat=42,
                                      token="synthetic",client=r2,bucket="test",
                                      get=get_mixed)
        self.assertIn(job,answer)
        self.assertIn("0 vorgemerkt, 1 abgewiesen",answer)


    def test_leading_caption_oversize_replays_earlier_quarantined_small_photos(self):
        from datetime import datetime, timezone
        import requests
        class TooLarge:
            status_code = 400
            def json(self):
                return {"ok":False, "error_code":400,
                        "description":"Bad Request: file is too big"}
            def raise_for_status(self):
                raise requests.HTTPError("botSECRET/getFile?file_id=PRIVATE")
        def mixed(url,**kw):
            if (kw.get("params") or {}).get("file_id") == "large":
                return TooLarge()
            return get(url,**kw)
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"early-photos",
              "date":int(datetime.now(timezone.utc).timestamp())}
        receive({**base,"photo":[{"file_id":"early"}]},update_id=110,
                token="synthetic",client=r2,bucket="test",get=mixed,authorized_chat=42)
        self.assertFalse(any(k.endswith("manifest.json") for k in r2.data))
        result=receive({**base,"caption":"/privat",
                        "video":{"file_id":"large","mime_type":"video/mp4"}},
                       update_id=111,token="synthetic",client=r2,bucket="test",
                       get=mixed,authorized_chat=42)
        self.assertIn("Downloadlimit",result)
        self.assertIn("1 vorgemerkte Albumdatei(en) privat gespeichert",result)
        self.assertEqual(len([k for k in r2.data if "/quarantine/" in k]),0)
        self.assertEqual(len([k for k in r2.data if "/rejected/" in k]),1)
        manifests=[json.loads(v) for k,v in r2.data.items()
                   if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),1)
        self.assertEqual(manifests[0]["lane"],"private")

    def test_owner_recovers_legacy_pre_caption_quarantine_without_resending(self):
        from scripts.telegram_private_media import handle_private_command
        from hashlib import sha256
        from datetime import datetime, timezone
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"legacy-pending",
              "date":int(datetime.now(timezone.utc).timestamp())}
        a={**base,"photo":[{"file_id":"first"}]}
        b={**base,"photo":[{"file_id":"second"}]}
        first=receive(a,update_id=200,token="synthetic",
                      client=r2,bucket="test",get=get,authorized_chat=42)
        receive(b,update_id=201,token="synthetic",
                client=r2,bucket="test",get=get,authorized_chat=42)
        job="tgalbum"+sha256(b"42:legacy-pending").hexdigest()[:32]
        self.assertIn(job,first)
        idx="private/v1/telegram-album-index/"+job+".json"
        legacy=json.loads(r2.data[idx])
        legacy.pop("owner_hash")
        r2.data[idx]=json.dumps(legacy).encode()
        self.assertFalse(any(k.endswith("manifest.json") for k in r2.data))
        with self.assertRaises(PermissionError):
            handle_private_command("/privat offene",chat=99,authorized_chat=42,
                                   token="synthetic",client=r2,bucket="test",get=get)
        pending=handle_private_command("/privat offene",chat=42,authorized_chat=42,
                                       token="synthetic",client=r2,bucket="test",get=get)
        self.assertIn(job,pending)
        self.assertIn("2 vorgemerkt",pending)
        with self.assertRaises(ValueError):
            handle_private_command("/privat freigeben tgalbum"+"a"*32,
                                   chat=42,authorized_chat=42,token="synthetic",
                                   client=r2,bucket="test",get=get)
        with self.assertRaises(PermissionError):
            handle_private_command("/privat freigeben "+job,
                                   chat=99,authorized_chat=42,token="synthetic",
                                   client=r2,bucket="test",get=get)
        result=handle_private_command("/privat freigeben "+job,
                                      chat=42,authorized_chat=42,token="synthetic",
                                      client=r2,bucket="test",get=get)
        self.assertIn("2 vorgemerkte Datei(en) in R2 übernommen",result)
        self.assertIn("Keine Veröffentlichung",result)
        manifests=[json.loads(v) for k,v in r2.data.items()
                   if k.endswith("manifest.json")]
        self.assertEqual(len(manifests),1)
        self.assertEqual(len(manifests[0]["assets"]),2)
        self.assertTrue(any(k.endswith("authorization.json") for k in r2.data))
        self.assertFalse(any("/quarantine/" in k for k in r2.data))
        retry=handle_private_command("/privat freigeben "+job,chat=42,
                                     authorized_chat=42,token="synthetic",
                                     client=r2,bucket="test",get=get)
        self.assertIn("Keine vorgemerkten",retry)

    def test_owner_recovery_transient_failure_retains_quarantine_for_retry(self):
        from scripts.telegram_private_media import handle_private_command
        from hashlib import sha256
        from datetime import datetime, timezone
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"retry-pending",
              "date":int(datetime.now(timezone.utc).timestamp()),
              "photo":[{"file_id":"flaky"}]}
        receive(base,update_id=300,token="synthetic",client=r2,
                bucket="test",get=get,authorized_chat=42)
        job="tgalbum"+sha256(b"42:retry-pending").hexdigest()[:32]
        def broken_get(url,**kw):
            raise __import__("requests").ConnectionError("SECRET")
        with self.assertRaisesRegex(RuntimeError,"erneuter Versuch"):
            handle_private_command("/privat freigeben "+job,
                                   chat=42,authorized_chat=42,token="synthetic",
                                   client=r2,bucket="test",get=broken_get)
        self.assertEqual(len([k for k in r2.data if "/quarantine/" in k]),1)
        done=handle_private_command("/privat freigeben "+job,
                                    chat=42,authorized_chat=42,token="synthetic",
                                    client=r2,bucket="test",get=get)
        self.assertIn("1 vorgemerkte Datei(en)",done)
        self.assertFalse(any("/quarantine/" in k for k in r2.data))

    def test_owner_hash_blocks_album_index_cross_chat_recovery(self):
        from scripts.telegram_private_media import handle_private_command
        from datetime import datetime, timezone
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"hash-guard",
              "date":int(datetime.now(timezone.utc).timestamp()),
              "photo":[{"file_id":"flaky"}]}
        result=receive(base,update_id=800,token="synthetic",client=r2,
                       bucket="test",get=get,authorized_chat=42)
        job=result.split(" · ")[1]
        idx="private/v1/telegram-album-index/"+job+".json"
        index=json.loads(r2.data[idx])
        index["owner_hash"]="0"*64
        r2.data[idx]=json.dumps(index).encode()
        with self.assertRaises(PermissionError):
            handle_private_command("/privat freigeben "+job,chat=42,
                                   authorized_chat=42,token="synthetic",
                                   client=r2,bucket="test",get=get)
        listing=handle_private_command("/privat offene",chat=42,
                                       authorized_chat=42,token="synthetic",
                                       client=r2,bucket="test",get=get)
        self.assertNotIn(job,listing)
        self.assertTrue(any("/quarantine/" in k for k in r2.data))

    def test_router_private_owner_text_recovery_does_not_break_other_commands(self):
        import ast
        from pathlib import Path
        tree=ast.parse(Path("telegram_router.py").read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        ns={}
        exec(compile(ast.Module(body=[main],type_ignores=[]),"telegram_router.py","exec"),ns)
        calls=[]
        acked=[]
        sent=[]
        updates=[
            {"update_id":100,"message":{"chat":{"id":42},"text":"/privat offene"}},
            {"update_id":101,"message":{"chat":{"id":42},"text":"/privat freigeben tgalbum"+"a"*32}},
        ]
        ns.update({
            "get_chat_id":lambda:42,
            "_read_last_update_id":lambda:99,
            "get_updates":lambda **kw:updates if kw.get("offset")==100 else [],
            "_ack":lambda uid:acked.append(uid),
            "send_message":lambda msg:sent.append(msg),
            "handle_private_command":lambda txt,**kwargs:calls.append(txt) or "Privat, keine Veröffentlichung",
            "os":__import__("os"),
        })
        ns["main"]()
        self.assertEqual(acked,[100,101])
        self.assertEqual(len(calls),2)
        self.assertTrue(all("keine veröffentlichung" in x.lower() for x in sent))

if __name__=="__main__":unittest.main()
