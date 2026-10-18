import unittest
from openmontage_storyboard import build_storyboard


class UniversalStoryboardTests(unittest.TestCase):
    def setUp(self):
        self.research = {"stories": [{
            "title": "Neue Motorradtechnik",
            "summary": "Schaltassistent und Blipper werden technisch erklärt.",
            "original_url": "https://example.org/verified",
            "series": "Technik",
        }]}

    def test_35_second_technical_explainer(self):
        plan = build_storyboard(self.research, target_duration=35,
                                film_type="product_explainer", language="de")
        self.assertAlmostEqual(plan["actual_duration_seconds"], 35, places=2)
        self.assertIn("Schaltassistent", plan["scenes"][0]["speaker_text"])
        self.assertNotIn("Meldung 1", plan["scenes"][0]["speaker_text"])

    def test_40_second_technology_news(self):
        plan = build_storyboard(self.research, target_duration=40,
                                film_type="technology_news")
        self.assertAlmostEqual(plan["actual_duration_seconds"], 40, places=2)

    def test_invalid_duration_fails(self):
        with self.assertRaises(ValueError):
            build_storyboard(self.research, target_duration=301)


if __name__ == "__main__":
    unittest.main()
