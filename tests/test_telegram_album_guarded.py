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
        if kw.get("IfNoneMatch")=="*" and Key in self.data:raise ValueError("duplicate")
        self.data[Key]=Body

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
        self.assertFalse(r2.data)
    def test_out_of_order_album_item_requires_explicit_replay(self):
        r2=R2()
        base={"chat":{"id":42},"media_group_id":"abc123","date":1791059000}
        first={**base,"photo":[{"file_id":"b"}]}
        captioned={**base,"caption":"/privat","photo":[{"file_id":"a"}]}
        self.assertIn("zurückgehalten",receive(first,update_id=201,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42))
        receive(captioned,update_id=200,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
        receive(first,update_id=201,token="synthetic",client=r2,bucket="test",get=get,authorized_chat=42)
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
if __name__=="__main__":unittest.main()
