import io
import unittest

from integrations.agent_memory import append_experience, load_context, memory_key


class Storage:
    def __init__(self):
        self.objects = {}

    def get_object(self, *, Key):
        if Key not in self.objects:
            exc = RuntimeError("missing")
            exc.response = {"Error": {"Code": "NoSuchKey"}}
            raise exc
        return {"Body": io.BytesIO(self.objects[Key])}

    def put_object(self, *, Key, Body, ContentType):
        self.objects[Key] = Body


class AgentMemoryTests(unittest.TestCase):
    def test_personal_and_shared_survive_new_calls(self):
        storage = Storage()
        append_experience(storage, "shared", kind="lesson", summary="Use source checks", reviewed=True)
        append_experience(storage, "creative_director", kind="success", summary="Prefer dynamic transitions", reviewed=True)
        context = load_context(storage, "creative_director")
        self.assertEqual(len(context["personal"]), 1)
        self.assertEqual(len(context["shared"]), 1)
        self.assertEqual(load_context(storage, "research")["personal"], [])

    def test_unreviewed_never_saved(self):
        storage = Storage()
        with self.assertRaises(ValueError):
            append_experience(storage, "research", kind="lesson", summary="Unverified", reviewed=False)
        self.assertEqual(storage.objects, {})

    def test_key_cannot_escape_namespace(self):
        with self.assertRaises(ValueError):
            memory_key("../private")


if __name__ == "__main__":
    unittest.main()
