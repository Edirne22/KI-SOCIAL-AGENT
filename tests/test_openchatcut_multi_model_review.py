import importlib.util
import pathlib
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("bridge",ROOT/"scripts"/"openchatcut_multi_model_review.py")
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
class MockResponse:
    status_code=200
    def json(self):return {"choices":[{"message":{"content":'{"hypotheses":[]} Bearer abc'}}]}
class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.cfg={"providers":{"nvidia":{"api_key_env":"NVIDIA_API_KEY","base_url":"https://example.test/v1","models":{"reasoning":"model-r"}},"groq":{"api_key_env":"GROQ_API_KEY","base_url":"https://example.test/v1","models":{"default":"model-g"}}}}
    def test_no_key_no_network(self):
        with patch.dict("os.environ",{},clear=True):
            self.assertEqual(bridge.run("why?",self.cfg,("nvidia",))[0]["state"],"SKIPPED_NO_KEY")
    def test_redacts_and_limits_payload(self):
        called=[]
        def request(url,**kwargs):
            called.append(kwargs)
            return MockResponse()
        with patch.dict("os.environ",{"NVIDIA_API_KEY":"mocksecret"}):
            got=bridge.query("nvidia",self.cfg["providers"]["nvidia"],"why?",transport=request)
        self.assertEqual(got["state"],"REVIEW")
        self.assertNotIn("abc",got["review"])
        self.assertEqual(called[0]["timeout"],45)
        self.assertEqual(called[0]["json"]["max_tokens"],950)
        self.assertNotIn("mocksecret",str(called[0]["json"]))
    def test_order_and_skips_unavailable(self):
        with patch.dict("os.environ",{},clear=True):
            got=bridge.run("why?",self.cfg,("groq","nvidia"))
        self.assertEqual([x["provider"] for x in got],["groq","nvidia"])
        self.assertTrue(all(x["state"]=="SKIPPED_NO_KEY" for x in got))
if __name__=="__main__":unittest.main()
