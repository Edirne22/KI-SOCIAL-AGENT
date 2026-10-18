"""Create a bucket-scoped private R2 client from existing GitHub secrets."""
from __future__ import annotations

import os


class PrivateStorageUnavailable(RuntimeError):
    pass


class BucketStorage:
    def __init__(self, client, bucket: str):
        self.client = client
        self.bucket = bucket

    def put_object(self, *, Key, Body, ContentType):
        return self.client.put_object(Bucket=self.bucket, Key=Key, Body=Body,
                                      ContentType=ContentType)

    def get_object(self, *, Key):
        return self.client.get_object(Bucket=self.bucket, Key=Key)


def from_environment(*, env=None, boto3_module=None):
    env = os.environ if env is None else env
    keys = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
    if any(not env.get(key) for key in keys):
        raise PrivateStorageUnavailable("Private R2 request storage not configured")
    if boto3_module is None:
        try:
            import boto3 as boto3_module
        except ImportError as exc:
            raise PrivateStorageUnavailable("boto3 dependency unavailable") from exc
    client = boto3_module.client(
        "s3",
        endpoint_url=f"https://{env['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    return BucketStorage(client, env["R2_BUCKET_NAME"])
