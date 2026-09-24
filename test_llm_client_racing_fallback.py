"""Regression tests for Racing LLM provider fallback and 429 cooldown."""
import json
import pytest
import llm_client


class Response:
    def __init__(self, status, payload=None, text="", headers=None):
        self.status_code=status
        self._payload=payload or {}
        self.text=text
        self.headers=headers or {}
        self.ok=200 <= status < 300
    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def reset_cooldowns(monkeypatch):
    llm_client._PROVIDER_COOLDOWNS.clear()
    monkeypatch.setenv("AGNES_API_KEY","agnes-test")
    monkeypatch.setenv("GEMINI_API_KEY","gemini-test")
    monkeypatch.setenv("NVIDIA_API_KEY","nvidia-test")


def test_agnes_429_falls_back_to_gemini(monkeypatch):
    calls=[]
    def request(method,url,**kwargs):
        calls.append(url)
        if "agnes-ai.com" in url:
            return Response(429,text="rate limit",headers={"Retry-After":"17"})
        return Response(200,{"candidates":[{"content":{"parts":[{"text":"GEMINI OK"}]}}]})
    monkeypatch.setattr(llm_client.requests,"request",request)
    assert llm_client.generate("final_captions","test") == "GEMINI OK"
    assert llm_client.provider_in_cooldown("agnes")
    assert sum("agnes-ai.com" in u for u in calls) == 1


def test_all_providers_429_fail_closed(monkeypatch):
    calls=[]
    def request(method,url,**kwargs):
        calls.append(url)
        return Response(429,text="rate limit",headers={"Retry-After":"60"})
    monkeypatch.setattr(llm_client.requests,"request",request)
    with pytest.raises(RuntimeError,match="fail-closed"):
        llm_client.generate("racing_semantic_qm","test")
    assert len(calls) == 3
    assert all(llm_client.provider_in_cooldown(p) for p in ("agnes","gemini","nvidia"))


def test_cooldown_respects_retry_after(monkeypatch):
    clock=[100.0]
    monkeypatch.setattr(llm_client.time,"monotonic",lambda: clock[0])
    response=Response(429,headers={"Retry-After":"23"})
    assert llm_client._set_provider_cooldown("agnes",response) == 23.0
    assert llm_client.provider_in_cooldown("agnes")
    clock[0]=123.1
    assert not llm_client.provider_in_cooldown("agnes")


def test_http_retry_is_limited_to_one_retry(monkeypatch):
    calls=[]
    def request(method,url,**kwargs):
        calls.append(url)
        if len(calls)==1:return Response(500,text="temporary")
        return Response(200,{"choices":[{"message":{"content":"OK"}}]})
    monkeypatch.setattr(llm_client.requests,"request",request)
    monkeypatch.setattr(llm_client.time,"sleep",lambda _:None)
    provider={"base_url":"https://example.test/v1","chat_model":"model","timeout_seconds":1}
    assert llm_client._generate_openai_text("test",provider,"key","nvidia") == "OK"
    assert len(calls) == 2


def test_missing_fallback_key_is_skipped(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY")
    calls=[]
    def request(method,url,**kwargs):
        calls.append(url)
        if "agnes-ai.com" in url:return Response(429,text="rate limit")
        return Response(200,{"choices":[{"message":{"content":"NVIDIA OK"}}]})
    monkeypatch.setattr(llm_client.requests,"request",request)
    assert llm_client.generate("final_captions","test") == "NVIDIA OK"
    assert not any("generativelanguage.googleapis.com" in u for u in calls)
