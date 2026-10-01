"""Offline production-router regression for verified Claude via OpenRouter."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import llm_router
import router

ROOT=Path(__file__).resolve().parents[1]
class Response:
    status_code=200
    headers={}
    def json(self):return {"choices":[{"message":{"content":"CLAUDE_ROUTED_OK"}}]}
class ClaudeRouteTests(unittest.TestCase):
    def test_canonical_old_router_is_enabled_using_existing_openrouter_key(self):
        cfg=router.load_config()
        self.assertEqual(router.get_provider_for_task("claude_document",cfg),"claude")
        self.assertEqual(cfg["providers"]["claude"]["api_key_env"],"OPENROUTER_API_KEY")
        self.assertEqual(cfg["providers"]["claude"]["model"],"anthropic/claude-sonnet-4.5")
        self.assertFalse(cfg["providers"]["claude_direct"]["enabled"])
    def test_runtime_exact_model_and_no_non_claude_fallback(self):
        config=ROOT/"config"/"llm_providers.json"
        worker=llm_router.LLMRouter(config)
        history=[]
        def post(url,headers,json,timeout):
            history.append((url,json["model"],headers["Authorization"]))
            return Response()
        with patch.dict("os.environ",{"OPENROUTER_API_KEY":"test-only-not-real"}):
            with patch.object(llm_router.requests,"post",post):
                result=worker.chat([{"role":"user","content":"test"}],task_type="claude_only")
        self.assertEqual(result,"CLAUDE_ROUTED_OK")
        self.assertEqual(len(history),1)
        self.assertEqual(history[0][0],"https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(history[0][1],"anthropic/claude-sonnet-4.5")
    def test_non_claude_override_is_rejected_without_network(self):
        worker=llm_router.LLMRouter(ROOT/"config"/"llm_providers.json")
        with self.assertRaisesRegex(ValueError,"forbids"):
            worker.chat([{"role":"user","content":"test"}],task_type="claude_only",model_override="google/gemini-3.6-flash")
    def test_claude_failure_cannot_fall_back_to_gemini(self):
        worker=llm_router.LLMRouter(ROOT/"config"/"llm_providers.json")
        class Rejected:
            status_code=402
            text="Payment Required"
            headers={}
        calls=[]
        def post(url,headers,json,timeout):
            calls.append(json["model"])
            return Rejected()
        with patch.dict("os.environ",{"OPENROUTER_API_KEY":"test-only-not-real"}):
            with patch.object(llm_router.requests,"post",post):
                with self.assertRaisesRegex(RuntimeError,"fehlgeschlagen"):
                    worker.chat([{"role":"user","content":"test"}],task_type="claude_only")
        self.assertEqual(calls,["anthropic/claude-sonnet-4.5"])
if __name__=="__main__":unittest.main()
