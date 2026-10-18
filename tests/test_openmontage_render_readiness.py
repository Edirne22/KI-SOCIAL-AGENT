import unittest
from integrations.openmontage.render_readiness import assess_render_readiness


class RenderReadinessTests(unittest.TestCase):
    def test_empty_storyboard_blocks_render(self):
        self.assertFalse(assess_render_readiness({"request_id": "tg-1", "status": "NEEDS_RESEARCH", "storyboard": []})["ready"])

    def test_unverified_sources_block_render(self):
        plan = {"request_id": "tg-1", "status": "STORYBOARD_DRAFT",
                "storyboard": [{"source_reference": "story_1"}], "verified_sources": []}
        self.assertFalse(assess_render_readiness(plan)["ready"])

    def test_ready_does_not_mean_rendered(self):
        plan = {"request_id": "tg-1", "status": "STORYBOARD_DRAFT",
                "storyboard": [{"source_reference": "story_1"}],
                "verified_sources": [{"url": "https://www.motogp.com/a", "source_status": "official"}]}
        self.assertEqual(assess_render_readiness(plan)["reason"], "READY_FOR_RENDER_PREPARATION")


if __name__ == "__main__":
    unittest.main()
