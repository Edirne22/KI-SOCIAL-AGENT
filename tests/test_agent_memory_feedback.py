import io
import unittest

from integrations.agent_memory_feedback import record_reviewed_outcome, review_history


class Storage:
    def __init__(self):
        self.data = {}

    def get_object(self, *, Key):
        if Key not in self.data:
            exc = RuntimeError("missing")
            exc.response = {"Error": {"Code": "NoSuchKey"}}
            raise exc
        return {"Body": io.BytesIO(self.data[Key])}

    def put_object(self, *, Key, Body, ContentType):
        self.data[Key] = Body


class FeedbackTests(unittest.TestCase):
    def test_reviewed_feedback_survives_new_read_and_is_shared(self):
        store = Storage()
        result = record_reviewed_outcome(store, agent_id="05_research_synthesist",
                                         job_id="job-42", outcome="lesson",
                                         lesson="Verify primary sources", reviewed=True,
                                         share=True)
        self.assertTrue(result["shared"])
        context = review_history(store, agent_id="05_research_synthesist")
        self.assertIn("job-42", context["personal"][0]["summary"])
        self.assertEqual(len(context["shared"]), 1)

    def test_unreviewed_cannot_write(self):
        store = Storage()
        with self.assertRaises(PermissionError):
            record_reviewed_outcome(store, agent_id="creative_director", job_id="1",
                                    outcome="success", lesson="Great cut", reviewed=False)
        self.assertFalse(store.data)


if __name__ == "__main__":
    unittest.main()
