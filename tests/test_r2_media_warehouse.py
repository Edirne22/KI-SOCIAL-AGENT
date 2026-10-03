import unittest
from datetime import datetime, timezone
from scripts.r2_media_warehouse import lane_for_upload, new_manifest, append_asset, store_original

class FakeR2:
    def __init__(self): self.objects={}
    def put_object(self,*,Bucket,Key,Body,**kwargs):
        if kwargs.get("IfNoneMatch")=="*" and Key in self.objects:
            raise ValueError("original already exists")
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
    def test_write_original_then_manifest(self):
        r2=FakeR2()
        updated=store_original(r2,"bucket",self.manifest,asset_id="asset12345678",filename="a.jpg",mime="image/jpeg",payload=b"photo")
        self.assertEqual(len(r2.objects),2)
        self.assertIn(updated["prefix"]+"manifest.json",r2.objects)
        with self.assertRaises(ValueError):
            store_original(r2,"bucket",self.manifest,asset_id="asset12345678",filename="a.jpg",mime="image/jpeg",payload=b"photo")

if __name__=="__main__":unittest.main()
