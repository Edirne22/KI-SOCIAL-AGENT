import unittest
from integrations.openmontage.research_memory_playbook import LESSONS, ensure_research_playbook
from unittest.mock import patch

class MemoryPlaybookTests(unittest.TestCase):
    def test_roles_and_methodology(self):
        self.assertEqual(set(LESSONS), {"05_research_synthesist", "creative_director", "07_video_optimization"})
        self.assertTrue(any("Fundstelle" in x for x in LESSONS["05_research_synthesist"]))
    def test_seed_is_idempotent(self):
        stored = {}
        def load(storage, role, limit=100):
            return {"personal": [{"summary": x, "reviewed": True} for x in stored.get(role, [])], "shared": []}
        def append(storage, role, *, kind, summary, reviewed):
            self.assertTrue(reviewed)
            stored.setdefault(role, []).append(summary)
        with patch("integrations.openmontage.research_memory_playbook.load_context", side_effect=load), patch("integrations.openmontage.research_memory_playbook.append_experience", side_effect=append):
            first = ensure_research_playbook(object())
            second = ensure_research_playbook(object())
        self.assertTrue(all(n > 0 for n in first.values()))
        self.assertTrue(all(n == 0 for n in second.values()))
