import tempfile
import unittest
from pathlib import Path
from scripts.openmontage_control import handle, load_jobs_ledger, save_job_entry

VIDEO = "12345678-1234-1234-1234-123456789abc"
JOB = "job_12345678"


class EditorialApprovalSafetyTests(unittest.TestCase):
    def test_unknown_video_cannot_be_approved_or_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "jobs.json"
            for command in ("freigeben", "ablehnen"):
                result = handle(f"/montage {command} {VIDEO}", 10, "1", "1", jobs_state=path)
                self.assertIn("unbekannt", result)
                self.assertEqual(load_jobs_ledger(path), {})

    def test_only_ready_job_can_be_approved(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "jobs.json"
            save_job_entry(JOB, {"video_id": VIDEO, "status": "RENDERING"}, path)
            result = handle(f"/montage freigeben {VIDEO}", 10, "1", "1", jobs_state=path)
            self.assertIn("Keine Freigabe", result)
            self.assertEqual(load_jobs_ledger(path)[JOB]["status"], "RENDERING")
            save_job_entry(JOB, {"video_id": VIDEO, "status": "READY_FOR_APPROVAL"}, path)
            result = handle(f"/montage freigeben {VIDEO}", 10, "1", "1", jobs_state=path)
            self.assertIn("FREIGEGEBEN", result)
            self.assertEqual(load_jobs_ledger(path)[JOB]["status"], "APPROVED")

    def test_foreign_chat_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):
                handle(f"/montage freigeben {VIDEO}", 10, "2", "1", jobs_state=Path(d)/"jobs.json")


if __name__ == "__main__":
    unittest.main()
