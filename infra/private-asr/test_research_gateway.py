import os,sys,unittest
from unittest.mock import patch
sys.path.insert(0,os.path.dirname(__file__))
import research_gateway as rg

class Response:
    status_code=200
    def json(self):
        return {"candidates":[{"groundingMetadata":{"groundingChunks":[
            {"web":{"title":"Current source","uri":"https://example.com/current"}}
        ]}}]}

class ResearchGatewayTests(unittest.TestCase):
    def test_openrouter_uses_current_server_web_tool(self):
        class ORResponse:
            status_code=200
            def json(self):
                return {"choices":[{"message":{"content":"Current fact [source](https://example.com/live)"}}]}
        env={"OPENROUTER_API_KEY":"test-or","GEMINI_API_KEY":"","SEARXNG_URL":""}
        with patch.dict(os.environ,env,clear=False),patch.object(rg.requests,"post",return_value=ORResponse()) as post:
            out=rg.research("current public fact")
        self.assertTrue(out["live_search"]);self.assertEqual(out["provider"],"OpenRouter-Web")
        payload=post.call_args.kwargs["json"]
        self.assertEqual(payload["tools"][0]["type"],"openrouter:web_search")
        self.assertNotIn("plugins",payload)

    def test_generic_gemini_grounding_returns_bounded_source(self):
        with patch.dict(os.environ,{"GEMINI_API_KEY":"test-key","SEARXNG_URL":""},clear=False),patch.object(rg.requests,"post",return_value=Response()) as post:
            out=rg.research("weather today in Schwelm")
        self.assertTrue(out["live_search"]);self.assertEqual(out["provider"],"Gemini-Grounded")
        self.assertEqual(out["results"][0]["url"],"https://example.com/current")
        payload=post.call_args.kwargs["json"];prompt=payload["contents"][0]["parts"][0]["text"]
        self.assertIn("weather today in Schwelm",prompt);self.assertNotIn("BESTES_ANGEBOT",prompt)

    def test_no_provider_fails_closed(self):
        with patch.dict(os.environ,{"GEMINI_API_KEY":"","SEARXNG_URL":""},clear=False):
            out=rg.research("current news")
        self.assertFalse(out["live_search"]);self.assertEqual(out["results"],[])

    def test_query_is_bounded(self):
        with self.assertRaises(ValueError): rg.research("x"*501)

if __name__=="__main__": unittest.main()


def test_openrouter_402_falls_back_to_groq_browser_search():
    import os
    from unittest.mock import patch
    old={k:os.environ.get(k) for k in ("OPENROUTER_API_KEY","GROQ_API_KEY","GEMINI_API_KEY","SEARXNG_URL")}
    os.environ["OPENROUTER_API_KEY"]="test-openrouter"
    os.environ["GROQ_API_KEY"]="test-groq"
    os.environ["GEMINI_API_KEY"]=""
    os.environ["SEARXNG_URL"]=""
    class R:
        def __init__(self,code,data): self.status_code=code; self._data=data
        def json(self): return self._data
    calls=[]
    def post(url,**kwargs):
        calls.append((url,kwargs.get("json") or {}))
        if "openrouter.ai" in url: return R(402,{})
        return R(200,{"choices":[{"message":{"content":"Current fact https://example.com/live"}}]})
    try:
        with patch("research_gateway.requests.post",side_effect=post):
            result=research_gateway.research("current public fact")
        assert result["live_search"] is True
        assert result["provider"]=="Groq-BrowserSearch"
        assert result["results"][0]["url"]=="https://example.com/live"
        groq_payload=calls[1][1]
        assert groq_payload["model"]=="openai/gpt-oss-20b"
        assert groq_payload["tools"]==[{"type":"browser_search"}]
        assert groq_payload["tool_choice"]=="required"
    finally:
        for k,v in old.items():
            if v is None: os.environ.pop(k,None)
            else: os.environ[k]=v


def test_direct_groq_research_never_calls_openrouter():
    import os
    from unittest.mock import patch
    old={k:os.environ.get(k) for k in ("OPENROUTER_API_KEY","GROQ_API_KEY","GEMINI_API_KEY","SEARXNG_URL")}
    os.environ["OPENROUTER_API_KEY"]="must-not-be-used"
    os.environ["GROQ_API_KEY"]="test-groq"
    os.environ["GEMINI_API_KEY"]=""
    os.environ["SEARXNG_URL"]=""
    class R:
        status_code=200
        def json(self): return {"choices":[{"message":{"content":"Live fact https://example.com/live"}}]}
    seen=[]
    def post(url,**kwargs):
        seen.append(url)
        assert "openrouter.ai" not in url
        return R()
    try:
        with patch("research_gateway.requests.post",side_effect=post):
            result=research_gateway.research("current public fact")
        assert result["live_search"] is True
        assert result["provider"]=="Groq-BrowserSearch"
        assert seen==[research_gateway.GROQ_URL]
    finally:
        for k,v in old.items():
            if v is None: os.environ.pop(k,None)
            else: os.environ[k]=v
