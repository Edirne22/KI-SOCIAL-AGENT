from unittest.mock import Mock, call

import pytest
import requests

import translation_router
from translation_router import TranslationRouter


def response(status=200, content="Merhaba"):
    result = Mock(status_code=status)
    result.json.return_value = {"choices": [{"message": {"content": content}}]}
    return result


@pytest.fixture
def dependencies(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    post = Mock(return_value=response())
    fallback = Mock(return_value="Fallback translation")
    sleep = Mock()
    monkeypatch.setattr(translation_router.requests, "post", post)
    monkeypatch.setattr(translation_router.llm_router, "quick_chat", fallback)
    monkeypatch.setattr(translation_router.time, "sleep", sleep)
    return post, fallback, sleep


@pytest.mark.parametrize(
    "text,source,target,translated",
    [("Hallo", "de", "tr", "Merhaba"), ("Merhaba", "tr", "de", "Hallo")],
)
def test_primary(text, source, target, translated, dependencies):
    post, fallback, sleep = dependencies
    post.return_value = response(content=translated)
    assert TranslationRouter().translate(text, source, target) == translated
    post.assert_called_once_with(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
        json={
            "model": "nvidia/riva-translate-4b-instruct-v2",
            "messages": [
                {"role": "system", "content": "You are a translation engine."},
                {"role": "user", "content": (
                    f"Translate from {source} to {target}. "
                    f"Output only the translation.\n\n{text}"
                )},
            ],
            "temperature": 0,
            "top_p": 1,
        },
        timeout=60,
    )
    fallback.assert_not_called()
    sleep.assert_not_called()


@pytest.mark.parametrize("status", [400, 401, 403, 500, 503])
def test_http_error_fallback(status, dependencies):
    post, fallback, sleep = dependencies
    post.return_value = response(status=status)
    assert TranslationRouter().translate("Hallo", "de", "tr") == "Fallback translation"
    post.assert_called_once()
    fallback.assert_called_once_with(
        "Translate from de to tr. Return ONLY the translation.\nText: Hallo"
    )
    sleep.assert_not_called()


def test_missing_key(monkeypatch, dependencies):
    post, fallback, sleep = dependencies
    monkeypatch.delenv("NVIDIA_API_KEY")
    assert TranslationRouter().translate("Hallo", "de", "tr") == "Fallback translation"
    post.assert_not_called()
    fallback.assert_called_once()
    sleep.assert_not_called()


@pytest.mark.parametrize("source,target", [("de", "de"), ("xx", "tr"), ("de", "xx")])
def test_invalid_languages(source, target, dependencies):
    post, fallback, sleep = dependencies
    with pytest.raises(ValueError):
        TranslationRouter().translate("Hallo", source, target)
    post.assert_not_called()
    fallback.assert_not_called()
    sleep.assert_not_called()


@pytest.mark.parametrize("error", [requests.Timeout, requests.ConnectionError])
def test_network_error_fallback(error, dependencies):
    post, fallback, sleep = dependencies
    post.side_effect = error("unavailable")
    assert TranslationRouter().translate("Hallo", "de", "tr") == "Fallback translation"
    post.assert_called_once()
    fallback.assert_called_once()
    sleep.assert_not_called()


@pytest.mark.parametrize("second_status", [200, 429, 500])
def test_429_retries_once_after_sleep(second_status, dependencies):
    post, fallback, sleep = dependencies
    events = Mock()
    events.attach_mock(post, "post")
    events.attach_mock(sleep, "sleep")
    events.attach_mock(fallback, "fallback")
    post.side_effect = [response(status=429), response(status=second_status)]
    result = TranslationRouter().translate("Hallo", "de", "tr")
    assert post.call_count == 2
    assert post.call_args_list[0] == post.call_args_list[1]
    sleep.assert_called_once_with(3)
    assert [entry[0] for entry in events.mock_calls[:3]] == ["post", "sleep", "post"]
    if second_status == 200:
        assert result == "Merhaba"
        fallback.assert_not_called()
    else:
        assert result == "Fallback translation"
        fallback.assert_called_once()


@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": [{"message": {"content": ""}}]},
                                  {"choices": [{"message": {"content": None}}]}])
def test_malformed_response_fallback(body, dependencies):
    post, fallback, sleep = dependencies
    post.return_value.json.return_value = body
    assert TranslationRouter().translate("Hallo", "de", "tr") == "Fallback translation"
    post.assert_called_once()
    fallback.assert_called_once()
    sleep.assert_not_called()


def test_invalid_json_fallback(dependencies):
    post, fallback, sleep = dependencies
    post.return_value.json.side_effect = ValueError("invalid JSON")
    assert TranslationRouter().translate("Hallo", "de", "tr") == "Fallback translation"
    fallback.assert_called_once()
    sleep.assert_not_called()


def test_fallback_failure_propagates(monkeypatch, dependencies):
    post, fallback, sleep = dependencies
    monkeypatch.delenv("NVIDIA_API_KEY")
    fallback.side_effect = RuntimeError("All providers failed")
    with pytest.raises(RuntimeError, match="All providers failed"):
        TranslationRouter().translate("Hallo", "de", "tr")
    fallback.assert_called_once()
    post.assert_not_called()
