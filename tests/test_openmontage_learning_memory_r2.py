import io
import unittest

from integrations.openmontage.learning_memory_r2 import load_memory, persist_feedback, MEMORY_KEY


class FakeStorage:
    def __init__(self):
        self.objects = {}

    def get_object(self, *, Key):
        if Key not in self.objects:
            exc = RuntimeError("not found")
            exc.response = {"Error": {"Code": "NoSuchKey"}}
            raise exc
        return {"Body": io.BytesIO(self.objects[Key])}

    def put_object(self, *, Key, Body, ContentType):
        assert ContentType == "application/json"
        self.objects[Key] = Body


class LearningMemoryR2Tests(unittest.TestCase):
    def test_empty_store_then_persist_and_reload(self):
        storage = FakeStorage()
        self.assertEqual(load_memory(storage)["records"], [])
        persist_feedback(storage, video_id="clip-1", decision="approved", style={"transition": "fade"})
        self.assertIn(MEMORY_KEY, storage.objects)
        self.assertEqual(load_memory(storage)["records"][0]["style"]["transition"], "fade")

    def test_unknown_storage_error_not_hidden(self):
        class BrokenStorage:
            def get_object(self, *, Key):
                raise RuntimeError("offline")
        with self.assertRaises(RuntimeError):
            load_memory(BrokenStorage())


if __name__ == "__main__":
    unittest.main()
