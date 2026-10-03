import unittest
from unittest.mock import patch
from scripts.telegram_private_media import identify,download,receive
class FakeR2:
    def __init__(self):self.objects={}
    def get_object(self,*,Bucket,Key):
        if Key not in self.objects:
            err=ValueError("missing")
            err.response={"Error":{"Code":"NoSuchKey"}}
            raise err
        import io
        return {"Body":io.BytesIO(self.objects[Key]),"ETag":'"fake"'}
    def put_object(self,*,Bucket,Key,Body,**kwargs):
        if kwargs.get("IfNoneMatch")=="*" and Key in self.objects:
            raise ValueError("duplicate")
        self.objects[Key]=Body
        return {"ETag":'"fake"'}

class Response:
    def __init__(self,data=None,payload=b"synthetic"):
        self.data=data
        self.payload=payload
    def raise_for_status(self):pass
    def json(self):return self.data
    def iter_content(self,chunk_size):yield self.payload

def fake_get(url,**kwargs):
    if url.endswith("/getFile"):
        return Response({"ok":True,"result":{"file_path":"photos/synthetic.jpg","file_size":9}})
    return Response(payload=b"synthetic")

class PrivateMediaTests(unittest.TestCase):
    def test_explicit_only(self):
        self.assertIsNone(identify({"photo":[{"file_id":"abc"}]}))
        self.assertEqual(identify({"caption":"/privat","photo":[{"file_id":"abc"}]})[1],"image/jpeg")
        self.assertEqual(identify({"caption":"/privat","video":{"file_id":"v","mime_type":"video/mp4"}})[1],"video/mp4")
    def test_synthetic_photo_and_video_private(self):
        for i,message in enumerate((
            {"caption":"/privat","photo":[{"file_id":"synthetic-photo"}]},
            {"caption":"/privat","video":{"file_id":"synthetic-video","mime_type":"video/mp4"}}
        )):
            r2=FakeR2()
            reply=receive(message,update_id=100+i,token="fake",client=r2,bucket="bucket",get=fake_get)
            self.assertIn("Privat in R2",reply)
            self.assertEqual(len(r2.objects),2)
            self.assertTrue(all(key.startswith("private/v1/") for key in r2.objects))
    def test_oversized_rejected(self):
        def oversized(url,**kwargs):
            return Response({"ok":True,"result":{"file_path":"a.jpg","file_size":20*1024*1024}})
        with self.assertRaises(ValueError):
            download("file","fake",get=oversized)

if __name__=="__main__":unittest.main()
