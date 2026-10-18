import json
import tempfile
import unittest
from pathlib import Path

from content_factory_core import JobStatus, ProductionJob
from content_factory_handoff import ToolTask, run_authorized_agent_machine, HandoffError
from content_factory_media_production import MediaProductionError
from integrations.openmontage.factory_bridge import OpenMontageFactoryAdapter
from media_storage import LocalScratchStorage


class OpenMontageBridgeTests(unittest.TestCase):
    def setUp(self):
        self.job = ProductionJob("om-bridge")
        for state in (JobStatus.INGESTING, JobStatus.RESEARCHING, JobStatus.WRITING, JobStatus.STORYBOARDING):
            self.job.transition(state)
        self.payload = {
            "job_id": self.job.job_id, "revision": self.job.revision,
            "research": {"stories": []}, "storyboard": {"scenes": []},
            "media_manifest": {"manifest": []},
        }

    def test_real_file_handoff(self):
        calls = []
        def producer(**kwargs):
            calls.append(kwargs)
            movie = kwargs["output_dir"] / "creative-demo.mp4"
            movie.write_bytes(b"verified-fixture-mp4")
            return {"status": "COMPLETED", "video_file": str(movie)}
        with tempfile.TemporaryDirectory() as tmp:
            storage = LocalScratchStorage(Path(tmp) / "media")
            adapter = OpenMontageFactoryAdapter(storage, producer)
            task = ToolTask(self.job.job_id, self.job.revision, "render", [], {"openmontage_payload": json.dumps(self.payload)})
            from content_factory_handoff import run_machine
            result = run_machine(self.job, adapter, task)
            self.assertEqual(1, len(calls))
            self.assertEqual("openmontage", result.machine)
            self.assertEqual(b"verified-fixture-mp4", storage.resolve_local(result.outputs[0]).read_bytes())
            self.assertEqual(result.outputs[0], self.job.media[0])

    def test_rejects_foreign_job_and_stale_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = OpenMontageFactoryAdapter(LocalScratchStorage(Path(tmp)), lambda **kw: self.fail("producer invoked"))
            for field, bad in (("job_id", "foreign"), ("revision", self.job.revision + 1)):
                payload = dict(self.payload, **{field: bad})
                task = ToolTask(self.job.job_id, self.job.revision, "render", [], {"openmontage_payload": json.dumps(payload)})
                with self.assertRaises(MediaProductionError):
                    adapter.run(task)

    def test_rejects_missing_video_and_unverified_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = OpenMontageFactoryAdapter(LocalScratchStorage(Path(tmp)), lambda **kw: {"status": "COMPLETED", "video_file": str(kw["output_dir"] / "creative-demo.mp4")})
            task = ToolTask(self.job.job_id, self.job.revision, "render", [], {"openmontage_payload": json.dumps(self.payload)})
            with self.assertRaises(MediaProductionError):
                adapter.run(task)

    def test_rejects_missing_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = OpenMontageFactoryAdapter(LocalScratchStorage(Path(tmp)), lambda **kw: self.fail("producer invoked"))
            with self.assertRaises(MediaProductionError):
                adapter.run(ToolTask(self.job.job_id, self.job.revision, "render", [], {}))


if __name__ == "__main__":
    unittest.main()
