import io
import tempfile
import unittest
from pathlib import Path

from scripts.openmontage_control import handle, save_job_entry
from integrations.openmontage.learning_memory_r2 import load_memory

VIDEO = "12345678-1234-1234-1234-123456789abc"


class Storage:
    def __init__(self):
        self.data = {}

    def get_object(self, *, Key):
        if Key not in self.data:
            exc = RuntimeError("not found")
            exc.response = {"Error": {"Code": "NoSuchKey"}}
            raise exc
        return {"Body": io.BytesIO(self.data[Key])}

    def put_object(self, *, Key, Body, ContentType):
        self.data[Key] = Body


class TelegramLearningTests(unittest.TestCase):
    def test_valid_approval_learns(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "jobs.json"
            save_job_entry("job_12345678", {"video_id": VIDEO, "status": "READY_FOR_APPROVAL",
                                           "style": {"transition": "fade"}}, path)
            storage = Storage()
            reply = handle(f"/montage freigeben {VIDEO}", 1, "1", "1", jobs_state=path,
                           feedback_storage=storage)
            self.assertIn("FREIGEGEBEN", reply)
            self.assertEqual(load_memory(storage)["records"][0]["decision"], "approved")

    def test_unknown_video_never_learns(self):
        with tempfile.TemporaryDirectory() as d:
            storage = Storage()
            reply = handle(f"/montage ablehnen {VIDEO}", 1, "1", "1",
                           jobs_state=Path(d) / "jobs.json", feedback_storage=storage)
            self.assertIn("unbekannt", reply)
            self.assertEqual(load_memory(storage)["records"], [])


if __name__ == "__main__":
    unittest.main()
