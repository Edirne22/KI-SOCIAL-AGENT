import io
import unittest
from integrations.openmontage.r2_client import from_environment, PrivateStorageUnavailable
from integrations.openmontage.private_request_store import get_request, put_request


class FakeBoto:
    def __init__(self):
        self.objects = {}
    def client(self, service, **kwargs):
        assert service == "s3"
        return self
    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = Body
    def get_object(self, *, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}


class R2ClientTests(unittest.TestCase):
    def test_missing_secrets_fail_closed(self):
        with self.assertRaises(PrivateStorageUnavailable):
            from_environment(env={}, boto3_module=FakeBoto())

    def test_bucket_scoped_roundtrip(self):
        env = {"R2_ACCOUNT_ID": "account", "R2_ACCESS_KEY_ID": "key",
               "R2_SECRET_ACCESS_KEY": "secret", "R2_BUCKET_NAME": "private"}
        storage = from_environment(env=env, boto3_module=FakeBoto())
        put_request(storage, request_id="tg-123", prompt="MotoGP", owner_chat="owner")
        self.assertEqual(get_request(storage, request_id="tg-123")["prompt"], "MotoGP")


if __name__ == "__main__":
    unittest.main()
