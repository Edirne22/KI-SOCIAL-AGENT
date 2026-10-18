import unittest

from openmontage_storyboard import build_storyboard


STORIES = {"stories": [{"title": "Verified test", "summary": "Sample",
                        "original_url": "https://example.com/source", "source_status": "official"}]}


class StoryboardMemoryTests(unittest.TestCase):
    def test_reviewed_preference_changes_transition(self):
        memory = {"creative_director": {"personal": [
            {"kind": "preference", "reviewed": True, "summary": "transition:wipeleft"}], "shared": []}}
        storyboard = build_storyboard(STORIES, agent_memory=memory)
        self.assertEqual(storyboard["scenes"][0]["transition"], "wipeleft")

    def test_unreviewed_preference_ignored(self):
        memory = {"creative_director": {"personal": [
            {"kind": "preference", "reviewed": False, "summary": "transition:wipeleft"}], "shared": []}}
        storyboard = build_storyboard(STORIES, agent_memory=memory)
        self.assertEqual(storyboard["scenes"][0]["transition"], "fade")


if __name__ == "__main__":
    unittest.main()
