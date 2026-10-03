"""Synthetic tests only: no real Telegram or private media."""
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

if __name__=="__main__":unittest.main()
