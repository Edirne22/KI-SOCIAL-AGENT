import json
import pytest
import llm_client


class Response:
    def __init__(self, status, payload=None, headers=None, text=""):
        self.status_code=status
        self._payload=payload or {}
        self.headers=headers or {}
        self.text=text
        self.ok=200 <= status < 300
    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def reset_cooldowns(monkeypatch):
    llm_client._PROVIDER_COOLDOWNS.clear()
    for name in ("AGNES_API_KEY","GEMINI_API_KEY","NVIDIA_API_KEY"):
        monkeypatch.setenv(name,"test-key")


def test_agnes_429_falls_back_to_gemini(monkeypatch):
    calls=[]
    def request(method,url,**kwargs):
        calls.append(url)
        if "agnes-ai.com" in url:
            return Response(429,headers={"Retry-After":"60"},text="rate limit")
        return Response(200,{"candidates":[{"content":{"parts":[{"text":"GEMINI OK"}]}}]})
    monkeypatch.setattr(llm_client.requests,"request",request)
    assert llm_client.generate("final_captions","test") == "GEMINI OK"
    assert llm_client.provider_in_cooldown("agnes")
    assert sum("agnes-ai.com" in url for url in calls) == 1


def test_all_providers_429_fail_closed(monkeypatch):
    calls=[]
    def request(method,url,**kwargs):
        calls.append(url)
        return Response(429,headers={"Retry-After":"60"},text="rate limit")
    monkeypatch.setattr(llm_client.requests,"request",request)
    with pytest.raises(RuntimeError,match="fail-closed"):
        llm_client.generate("racing_semantic_qm","test")
    assert len(calls) == 3
    assert all(llm_client.provider_in_cooldown(p) for p in ("agnes","gemini","nvidia"))


def test_cooldown_respects_retry_after(monkeypatch):
    now=[100.0]
    monkeypatch.setattr(llm_client.time,"monotonic",lambda:now[0])
    monkeypatch.setattr(llm_client.requests,"request",lambda *a,**k:Response(429,headers={"Retry-After":"17"},text="rate limit"))
    with pytest.raises(RuntimeError):
        llm_client._request_json("POST","https://example.invalid",{}, {},10,provider_name="agnes")
    assert llm_client.provider_in_cooldown("agnes")
    now[0]=118.0
    assert not llm_client.provider_in_cooldown("agnes")


def test_http_retry_is_limited_to_one_retry(monkeypatch):
    calls=[]
    responses=[Response(500,text="temporary"),Response(200,{"ok":True})]
    def request(*args,**kwargs):
        calls.append(1)
        return responses.pop(0)
    monkeypatch.setattr(llm_client.requests,"request",request)
    monkeypatch.setattr(llm_client.time,"sleep",lambda *_:None)
    assert llm_client._request_json("POST","https://example.invalid",{}, {},10,provider_name="agnes") == {"ok":True}
    assert len(calls) == 2
