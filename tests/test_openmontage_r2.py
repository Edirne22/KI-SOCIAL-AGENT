"""Offline R2 preview tests: no credentials, network calls, or actual uploads."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from media_storage import R2Storage
from scripts.openmontage_r2 import upload_private_preview


class PrivatePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "preview.mp4"
        self.file.write_bytes(b"fake-mp4-for-mocked-storage")
        self.client = Mock()
        self.client.generate_presigned_url.return_value = (
            "https://example.r2.cloudflarestorage.com/private?X-Amz-Signature=redacted"
        )
        self.storage = R2Storage(
            account_id="example", access_key_id="fake", secret_access_key="fake",
            bucket="private-bucket", cache_root=Path(self.temp.name) / "cache",
            client=self.client,
        )

    def test_private_upload_and_short_lived_link(self):
        result = upload_private_preview(self.file, storage=self.storage)
        self.assertEqual(result["expires_seconds"], 900)
        self.assertTrue(result["r2_uri"].startswith("r2://private-bucket/media/"))
        args, kwargs = self.client.upload_file.call_args
        self.assertEqual(args[1], "private-bucket")
        self.assertEqual(kwargs["ExtraArgs"]["ContentType"], "video/mp4")
        self.assertNotIn("ACL", kwargs["ExtraArgs"])
        signed = self.client.generate_presigned_url.call_args
        self.assertEqual(signed.args[0], "get_object")
        self.assertEqual(signed.kwargs["ExpiresIn"], 900)
        self.assertEqual(signed.kwargs["HttpMethod"], "GET")
        self.assertEqual(signed.kwargs["Params"]["Key"], args[2])

    def test_expiry_rejected_before_upload(self):
        for invalid in (0, 59, 3601, True, "900"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    upload_private_preview(self.file, storage=self.storage, expires_seconds=invalid)
        self.client.upload_file.assert_not_called()

    def test_invalid_file_rejected_before_upload(self):
        for filename, data in (("bad.jpg", b"x"), ("empty.mp4", b"")):
            with self.subTest(filename=filename):
                path = Path(self.temp.name) / filename
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    upload_private_preview(path, storage=self.storage)
        self.client.upload_file.assert_not_called()

    def test_insecure_url_rejected(self):
        self.client.generate_presigned_url.return_value = "http://insecure.example/test"
        with self.assertRaises(RuntimeError):
            upload_private_preview(self.file, storage=self.storage)


if __name__ == "__main__":
    unittest.main()
