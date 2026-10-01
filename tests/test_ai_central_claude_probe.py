import unittest
from unittest.mock import patch
from scripts.ai_central_claude_probe import probe,MODEL
class Resp:
  status_code=200
  def json(self):return {"model":MODEL,"choices":[{"message":{"content":"CLAUDE_OK"}}]}
class TestProbe(unittest.TestCase):
  def test_no_key_does_not_call_endpoint(self):
    with patch.dict("os.environ",{},clear=True):
      self.assertEqual(probe(lambda *args,**kwargs: self.fail("network"))["state"],"NO_KEY")
  def test_exact_claude_response_and_minimal_tokens(self):
    with patch.dict("os.environ",{"OPENROUTER_API_KEY":"fake"}):
      def fake(url,**kwargs):
        self.assertEqual(kwargs["json"]["model"],MODEL)
        self.assertLessEqual(kwargs["json"]["max_tokens"],24)
        return Resp()
      self.assertEqual(probe(fake)["state"],"INFERENCE_OK")
  def test_non_claude_response_rejected(self):
    with patch.dict("os.environ",{"OPENROUTER_API_KEY":"fake"}):
      class Other(Resp):
        def json(self):return {"model":"google/gemini-3-flash","choices":[{"message":{"content":"CLAUDE_OK"}}]}
      self.assertEqual(probe(lambda *args,**kwargs:Other())["state"],"UNVERIFIED_RESPONSE")
if __name__=="__main__":unittest.main()
