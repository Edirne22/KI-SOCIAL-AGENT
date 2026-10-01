import importlib.util
import json
import pathlib
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("central",ROOT/"scripts/cloud_ai_central.py")
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
TASK={"title":"MCP incident","question":"Which offline test separates the hypotheses?",
      "evidence":"Six raw and six SDK transport attempts timed out; container logs unavailable."}
CFG={"providers":{n:{"api_key_env":n.upper()+"_KEY","base_url":"https://example.test/v1",
    "models":{"default":"mock"}} for n in ["google","nvidia","openrouter","groq"]}}
class FakeR2:
    def __init__(self):self.saved=[]
    def put_object(self,**kwargs):self.saved.append(kwargs)
class Tests(unittest.TestCase):
    def test_task_requires_exact_fields_and_no_secrets(self):
        self.assertEqual(c.validate_task(TASK),TASK)
        with self.assertRaises(ValueError):c.validate_task({**TASK,"token":"value"})
        with self.assertRaises(ValueError):c.validate_task({**TASK,"question":"Authorization: Bearer exposed"})
    def test_independent_role_fallback(self):
        def fake(name,cfg,task,role):
            return {"role":role,"provider":name,
                "status":"ERROR" if name=="nvidia" else "ANSWER"}
        reviews=c.dispatch(TASK,CFG,ask_fn=fake)
        self.assertEqual(len(reviews),3)
        self.assertEqual([x["role"] for x in reviews],list(c.ROLES))
        self.assertEqual([a["provider"] for a in reviews[1]["attempts"]],["nvidia","openrouter"])
        self.assertTrue(all(x["status"]=="ANSWER" for x in reviews))
    def test_no_key_no_network(self):
        with patch.dict("os.environ",{},clear=True):
            result=c.ask("nvidia",CFG["providers"]["nvidia"],TASK,"diagnosis")
        self.assertEqual(result["status"],"NO_KEY")
    def test_packet_requires_approval_and_private_r2_key(self):
        p=c.packet(TASK,[],"1234")
        self.assertEqual(p["status"],"PENDING_REVIEW")
        self.assertTrue(p["requires_human_approval"])
        f=FakeR2()
        key=c.save_r2(p,f,"private-bucket")
        self.assertIn(p["task_id"],key)
        self.assertEqual(f.saved[0]["Bucket"],"private-bucket")
        self.assertEqual(f.saved[0]["ContentType"],"application/json")
        self.assertNotIn("Authorization",str(f.saved))
    def test_deny_invalid_approval_or_run_id(self):
        with self.assertRaises(ValueError):c.packet(TASK,[],"../../etc")
        p=c.packet(TASK,[],"1234")
        p["status"]="APPROVED"
        with self.assertRaises(ValueError):c.save_r2(p,FakeR2(),"private")
if __name__=="__main__":unittest.main()
