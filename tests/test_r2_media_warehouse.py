import unittest
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from scripts.r2_media_warehouse import lane_for_upload, new_manifest, append_asset, store_original

class FakeR2:
    def __init__(self): self.objects={}
    def get_object(self,*,Bucket,Key):
        if Key not in self.objects:
            err=ValueError("not found")
            err.response={"Error":{"Code":"NoSuchKey"}}
            raise err
        return {"Body":__import__("io").BytesIO(self.objects[Key]),"ETag":'"fake"'}
    def put_object(self,*,Bucket,Key,Body,**kwargs):
        if kwargs.get("IfNoneMatch")=="*" and Key in self.objects:
            raise ValueError("original already exists")
        if kwargs.get("IfMatch") and Key not in self.objects:
            raise ValueError("stale manifest")
        self.objects[Key]=Body
        return {"ETag":'"fake"'}

class WarehouseTests(unittest.TestCase):
    def setUp(self):
        self.date=datetime(2026,10,3,19,0,tzinfo=timezone.utc)
        self.manifest=new_manifest(lane="private",title="Geburtstag",created_at=self.date,job_id="job1234567890")
    def test_private_default_and_children(self):
        self.assertEqual(lane_for_upload(),"private")
        self.assertEqual(lane_for_upload(explicit_social=True,contains_children=True),"private")
        self.assertEqual(lane_for_upload(explicit_social=True),"social")
    def test_chronological_keys_and_hash(self):
        updated,key=append_asset(self.manifest,asset_id="asset12345678",filename="clip.mp4",mime="video/mp4",payload=b"video")
        self.assertEqual(key,"private/v1/2026/10/03/job1234567890/originals/asset12345678/clip.mp4")
        self.assertEqual(updated["assets"][0]["size"],5)
        self.assertEqual(len(updated["assets"][0]["sha256"]),64)
    def test_cross_lane_and_traversal_rejected(self):
        with self.assertRaises(ValueError):
            append_asset(self.manifest,asset_id="asset12345678",filename="../secret",mime="video/mp4",payload=b"x")
        with self.assertRaises(ValueError):
            new_manifest(lane="../social",title="wrong")
    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg unavailable")
    def test_synthetic_photo_video_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo=Path(tmp)/"photo.jpg"
            video=Path(tmp)/"video.mp4"
            subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=blue:s=64x64:d=1","-frames:v","1","-y",str(photo)],check=True)
            subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=red:s=64x64:r=5:d=1","-c:v","mpeg4","-y",str(video)],check=True)
            self.assertTrue(photo.read_bytes().startswith(bytes.fromhex("ffd8")))
            self.assertIn(b"ftyp",video.read_bytes()[:32])
            r2=FakeR2()
            current=self.manifest
            for name,mime,ident,file in (("photo.jpg","image/jpeg","photo1234567890",photo),("video.mp4","video/mp4","video1234567890",video)):
                current=store_original(r2,"bucket",current,asset_id=ident,filename=name,mime=mime,payload=file.read_bytes())
            self.assertEqual(len(current["assets"]),2)
            self.assertEqual(len(r2.objects),3)
            for asset in current["assets"]:
                self.assertEqual(r2.objects[asset["key"]],(photo if asset["mime"]=="image/jpeg" else video).read_bytes())
            self.assertEqual(len(json.loads(r2.objects[current["prefix"]+"manifest.json"])["assets"]),2)

    def test_stale_manifest_cannot_lose_other_upload(self):
        r2=FakeR2()
        first=store_original(r2,"bucket",self.manifest,asset_id="asset12345678",filename="a.jpg",mime="image/jpeg",payload=b"first")
        self.assertEqual(len(first["assets"]),1)
        with self.assertRaises(RuntimeError):
            store_original(r2,"bucket",self.manifest,asset_id="asset87654321",filename="b.jpg",mime="image/jpeg",payload=b"second")
        self.assertEqual(len(json.loads(r2.objects[first["prefix"]+"manifest.json"])["assets"]),1)

    def test_corrupt_readback_never_commits_manifest(self):
        class CorruptR2(FakeR2):
            def get_object(self,*,Bucket,Key):
                result=super().get_object(Bucket=Bucket,Key=Key)
                if "/originals/" in Key:
                    result["Body"]=__import__("io").BytesIO(b"tampered")
                return result
        r2=CorruptR2()
        with self.assertRaisesRegex(RuntimeError,"readback mismatch"):
            store_original(r2,"bucket",self.manifest,asset_id="asset12345678",filename="a.jpg",mime="image/jpeg",payload=b"photo")
        self.assertNotIn(self.manifest["prefix"]+"manifest.json",r2.objects)

    def test_write_original_then_manifest(self):
        r2=FakeR2()
        updated=store_original(r2,"bucket",self.manifest,asset_id="asset12345678",filename="a.jpg",mime="image/jpeg",payload=b"photo")
        self.assertEqual(len(r2.objects),2)
        self.assertIn(updated["prefix"]+"manifest.json",r2.objects)
        with self.assertRaises(ValueError):
            store_original(r2,"bucket",self.manifest,asset_id="asset12345678",filename="a.jpg",mime="image/jpeg",payload=b"photo")

if __name__=="__main__":unittest.main()
