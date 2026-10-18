import io
import unittest

from integrations.agent_memory_preflight import prepare_agent_context, require_agent_memory


class Storage:
    def get_object(self, *, Key):
        exc = RuntimeError("not found")
        exc.response = {"Error": {"Code": "NoSuchKey"}}
        raise exc


class MemoryPreflightTests(unittest.TestCase):
    def test_every_role_can_load_own_and_shared_memory(self):
        for agent_id in ("01_content_creator", "05_research_synthesist",
                         "14_memory_curator", "21_instandhaltungsagent", "creative_director"):
            prepared = prepare_agent_context(Storage(), agent_id=agent_id, job={"job_id": "test"})
            self.assertTrue(require_agent_memory(prepared)["memory_loaded"])

    def test_no_unloaded_job_passes(self):
        with self.assertRaises(RuntimeError):
            require_agent_memory({"job_id": "test"})

    def test_missing_job_id_rejected(self):
        with self.assertRaises(ValueError):
            prepare_agent_context(Storage(), agent_id="creative_director", job={})


if __name__ == "__main__":
    unittest.main()
