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
    def test_free_review_scope_has_no_paid_provider_fallback(self):
        self.assertEqual(set(c.FREE_ROLES),{"research","challenge"})
        self.assertTrue(all(names==("openrouter",) for names in c.FREE_ROLES.values()))
        used=[]
        def fake(name,cfg,task,role):
            used.append((name,cfg["models"]["default"]))
            return {"role":role,"provider":name,"status":"ANSWER"}
        cfg={"providers":{"openrouter":{"models":{"default":"openrouter/free"}}}}
        result=c.dispatch(TASK,cfg,ask_fn=fake,roles=c.FREE_ROLES)
        self.assertEqual(len(result),2)
        self.assertEqual(used,[("openrouter","openrouter/free")]*2)
    def test_pinned_free_team_contains_only_documented_free_endpoints(self):
        cfg=json.loads((ROOT/"config/llm_providers.json").read_text())
        scoped=c.free_team_config(cfg)
        self.assertEqual(set(scoped["providers"]),{"openrouter","nvidia_nemotron","nvidia_kimi"})
        self.assertEqual(scoped["providers"]["openrouter"]["models"]["reasoning"],"openrouter/free")
        for label,model in c.FREE_TEAM_MODELS.items():
            self.assertEqual(scoped["providers"][label]["models"]["reasoning"],model)
            self.assertEqual(scoped["providers"][label]["api_key_env"],"NVIDIA_API_KEY")
        self.assertNotIn("claude_openrouter",scoped["providers"])
    def test_free_team_three_real_roles_with_bounded_fallback(self):
        cfg=c.free_team_config(json.loads((ROOT/"config/llm_providers.json").read_text()))
        attempts=[]
        def fake(name,route,task,role):
            attempts.append((name,route["models"]["reasoning"],role))
            return {"role":role,"provider":name,
                    "status":"ERROR" if name=="nvidia_kimi" else "ANSWER"}
        result=c.dispatch(TASK,cfg,ask_fn=fake,roles=c.FREE_TEAM_ROLES)
        self.assertEqual([x["role"] for x in result],["research","diagnosis","challenge"])
        self.assertTrue(all(x["status"]=="ANSWER" for x in result))
        self.assertEqual([x[0] for x in attempts],
            ["nvidia_nemotron","nvidia_kimi","openrouter","openrouter"])
        self.assertTrue(all(model in set(c.FREE_TEAM_MODELS.values())|{"openrouter/free"}
                            for _,model,_ in attempts))
    def test_free_team_refuses_provider_endpoint_mutation(self):
        cfg=json.loads((ROOT/"config/llm_providers.json").read_text())
        cfg["providers"]["nvidia"]["base_url"]="https://fake.example/v1"
        with self.assertRaisesRegex(ValueError,"FREE_TEAM_ROUTE_CONFIG_MISMATCH"):
            c.free_team_config(cfg)
        workflow=(ROOT/".github/workflows/ai-central-free-team-once.yml").read_text()
        self.assertIn("AI_NVIDIA_DEVELOPER_FREE_VERIFIED",workflow)
        self.assertIn("--free-team",workflow)
        self.assertNotIn("ANTHROPIC_API_KEY",workflow)

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
