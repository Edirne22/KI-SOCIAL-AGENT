import hashlib
import tempfile
import unittest
from pathlib import Path

from content_factory_core import MediaRef
from media_storage import R2Storage


class FakeS3:
    def __init__(self):
        self.objects = {}
    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        self.objects[(bucket, key)] = Path(filename).read_bytes()
    def download_file(self, bucket, key, filename):
        Path(filename).write_bytes(self.objects[(bucket, key)])


class R2StorageTests(unittest.TestCase):
    def make(self, root, client):
        return R2Storage(account_id="acct", access_key_id="key", secret_access_key="secret",
                         bucket="factory", cache_root=root, client=client)

    def test_roundtrip_preserves_hash_size_and_private_uri(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"hello video.mp4"; src.write_bytes(b"factory-media")
            s3=FakeS3(); store=self.make(root/"cache",s3)
            ref=store.put_file(src,provenance="test:upload",mime_type="video/mp4")
            self.assertTrue(ref.uri.startswith("r2://factory/media/"))
            self.assertNotIn("https://",ref.uri)
            out=store.resolve_local(ref)
            self.assertEqual(src.read_bytes(),out.read_bytes())
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),ref.sha256)

    def test_foreign_bucket_uri_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store=self.make(Path(td)/"cache",FakeS3())
            ref=MediaRef("m","r2://other/media/m/x.mp4","0"*64,1,"video/mp4","test")
            with self.assertRaises(ValueError): store.resolve_local(ref)

    def test_cross_media_id_key_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store=self.make(Path(td)/"cache",FakeS3())
            ref=MediaRef("good","r2://factory/media/evil/x.mp4","0"*64,1,"video/mp4","test")
            with self.assertRaises(ValueError): store.resolve_local(ref)

    def test_tampered_object_is_deleted_and_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"x.mp4"; src.write_bytes(b"original")
            s3=FakeS3(); store=self.make(root/"cache",s3); ref=store.put_file(src,provenance="test")
            key=ref.uri[len("r2://factory/"):]
            s3.objects[("factory",key)]=b"tampered"
            with self.assertRaises(ValueError): store.resolve_local(ref)
            self.assertFalse(any((root/"cache").rglob("x.mp4")))

    def test_missing_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            import os
            names=("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME")
            old={n:os.environ.pop(n,None) for n in names}
            try:
                with self.assertRaises(ValueError): R2Storage.from_env(cache_root=Path(td))
            finally:
                for n,v in old.items():
                    if v is not None: os.environ[n]=v


if __name__=="__main__":
    unittest.main()
