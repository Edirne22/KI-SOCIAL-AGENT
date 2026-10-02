"""Negative/positive isolated private R2 IfMatch smoke with no credentials."""
import os
import unittest
from uuid import uuid4
from unittest.mock import patch

from scripts.block8_private_r2_cas_smoke import PREFIX,exercise_conditional_cas,run
from tests.test_content_factory_r2_job_repository import FakeS3


class OfflineS3(FakeS3):
    def delete_object(self,*,Bucket,Key):
        with self.lock:
            self.objects.pop((Bucket,Key),None)


class CasSmokeTest(unittest.TestCase):
    def test_offline_race_and_cleanup(self):
        client=OfflineS3();key=PREFIX+str(uuid4())+".json"
        self.assertIn(exercise_conditional_cas(client,"test-private-bucket",key),(2,3))
        self.assertNotIn(("test-private-bucket",key),client.objects)

    def test_cannot_use_canonical_or_media_prefixes(self):
        c=OfflineS3()
        for path in ("ai-central/v1/factory-jobs/"+str(uuid4())+".json",
                     "media/"+str(uuid4())+"/video.mp4"):
            with self.assertRaises(ValueError):
                exercise_conditional_cas(c,"private",path)
        self.assertFalse(c.objects)

    def test_unapproved_smoke_cannot_access_any_r2_credentials(self):
        with patch.dict(os.environ,{"BLOCK8_PRIVATE_R2_CAS_SMOKE_APPROVED":""}):
            with self.assertRaisesRegex(RuntimeError,"BLOCK8_REAL_R2_SMOKE_NOT_APPROVED"):
                run()


if __name__=="__main__":
    unittest.main()
