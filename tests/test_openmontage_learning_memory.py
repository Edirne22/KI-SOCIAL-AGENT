import unittest
from integrations.openmontage.learning_memory import record_feedback, suggested_style, serialize_memory


class LearningMemoryTests(unittest.TestCase):
    def test_approved_styles_can_be_suggested(self):
        memory = record_feedback({}, video_id="clip-1", decision="approved", style={"transition": "fade"})
        self.assertEqual(suggested_style(memory)["transition"], "fade")
        self.assertIn(b"approved", serialize_memory(memory))

    def test_rejected_styles_not_preferred(self):
        memory = record_feedback({}, video_id="clip-1", decision="rejected", style={"transition": "wipeleft"})
        self.assertEqual(suggested_style(memory), {})

    def test_invalid_decision_rejected(self):
        with self.assertRaises(ValueError):
            record_feedback({}, video_id="clip-1", decision="publish")

    def test_feedback_updates_existing_video(self):
        memory = record_feedback({}, video_id="clip-1", decision="rejected")
        memory = record_feedback(memory, video_id="clip-1", decision="approved")
        self.assertEqual(len(memory["records"]), 1)


if __name__ == "__main__":
    unittest.main()
