# test_vision_router.py
import base64
import json
from unittest.mock import Mock

import pytest
import requests

import vision_router
from vision_router import FALLBACK_MODEL, NVIDIA_MODELS, VisionRouter

IMAGE = b"\xff\xd8\xfftest-image"


def response(content="Ein Motorrad.", status=200):
    result = Mock(status_code=status)
    result.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return result


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")


@pytest.fixture(autouse=True)
def http(monkeypatch):
    post = Mock(return_value=response())
    monkeypatch.setattr(vision_router.requests, "post", post)
    return post


@pytest.mark.parametrize("mode", ["general", "omni"])
def test_description(mode, http):
    assert VisionRouter().analyze(IMAGE, mode) == {
        "description": "Ein Motorrad.",
        "model_used": NVIDIA_MODELS[mode],
    }
    http.assert_called_once()

    args, kwargs = http.call_args
    assert args == (vision_router.NVIDIA_URL,)
    assert kwargs["timeout"] == 180
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == NVIDIA_MODELS[mode]

    content = kwargs["json"]["messages"][0]["content"]
    assert content[0]["text"] == vision_router.PROMPTS[mode]
    assert content[1]["image_url"]["url"] == (
        "data:image/jpeg;base64," + base64.b64encode(IMAGE).decode()
    )


@pytest.mark.parametrize("status", [400, 401, 500, 503])
def test_general_fallback(status, http):
    http.side_effect = [
        response(status=status),
        response("Fallback."),
    ]

    assert VisionRouter().analyze(IMAGE) == {
        "description": "Fallback.",
        "model_used": FALLBACK_MODEL,
    }
    assert http.call_count == 2
    assert [
        call.kwargs["json"]["model"]
        for call in http.call_args_list
    ] == [NVIDIA_MODELS["general"], FALLBACK_MODEL]


def test_ocr_tables(http):
    extracted = {
        "text": "Kosten",
        "tables": [
            {
                "headers": ["Teil", "EUR"],
                "rows": [["Reifen", "200"]],
            }
        ],
    }
    http.return_value = response(json.dumps(extracted))

    assert VisionRouter().analyze(IMAGE, "ocr") == {
        **extracted,
        "model_used": NVIDIA_MODELS["ocr"],
    }
    http.assert_called_once()
    assert http.call_args.kwargs["json"]["model"] == NVIDIA_MODELS["ocr"]


def test_missing_api_key(monkeypatch, http):
    monkeypatch.delenv("NVIDIA_API_KEY")

    with pytest.raises(RuntimeError, match="NVIDIA_API_KEY"):
        VisionRouter().analyze(IMAGE)

    http.assert_not_called()


def test_invalid_mode(http):
    with pytest.raises(ValueError, match="mode"):
        VisionRouter().analyze(IMAGE, "invalid")

    http.assert_not_called()


@pytest.mark.parametrize("kind", ["path", "base64", "data_url"])
def test_image_inputs(kind, tmp_path, http):
    encoded = base64.b64encode(IMAGE).decode()

    if kind == "path":
        path = tmp_path / "image.jpg"
        path.write_bytes(IMAGE)
        image = str(path)
    elif kind == "data_url":
        image = "data:image/jpeg;base64," + encoded
    else:
        image = encoded

    assert "description" in VisionRouter().analyze(image)
    content = http.call_args.kwargs["json"]["messages"][0]["content"]
    assert content[1]["image_url"]["url"] == (
        "data:image/jpeg;base64," + encoded
    )


def test_429_switches_immediately_to_fallback(http):
    http.side_effect = [
        response(status=429),
        response("Fallback."),
    ]

    assert VisionRouter().analyze(IMAGE) == {
        "description": "Fallback.",
        "model_used": FALLBACK_MODEL,
    }
    assert http.call_count == 2
    assert [
        call.kwargs["json"]["model"]
        for call in http.call_args_list
    ] == [NVIDIA_MODELS["general"], FALLBACK_MODEL]


def test_429_on_both_models_has_no_retries(http):
    http.return_value = response(status_code=429) if False else response(
        status=429
    )

    result = VisionRouter().analyze(IMAGE)

    assert "429" in result["error"]
    assert http.call_count == 2
    assert [
        call.kwargs["json"]["model"]
        for call in http.call_args_list
    ] == [NVIDIA_MODELS["general"], FALLBACK_MODEL]


@pytest.mark.parametrize("mode", ["ocr", "omni"])
@pytest.mark.parametrize("status", [400, 429, 500])
def test_no_fallback(mode, status, http):
    http.return_value = response(status=status)

    assert str(status) in VisionRouter().analyze(IMAGE, mode)["error"]
    http.assert_called_once()


def test_timeout_fallback(http):
    http.side_effect = [
        requests.Timeout("Timed out"),
        response(),
    ]

    assert VisionRouter().analyze(IMAGE)["model_used"] == FALLBACK_MODEL
    assert http.call_count == 2


@pytest.mark.parametrize(
    "content",
    [
        "bad json",
        "[]",
        '{"text": "x"}',
        '{"text": "x", "tables": [{"headers": [], "rows": ["bad"]}]}',
    ],
)
def test_malformed_ocr(content, http):
    http.return_value = response(content)

    assert "error" in VisionRouter().analyze(IMAGE, "ocr")
    http.assert_called_once()


def test_invalid_image(http):
    assert "error" in VisionRouter().analyze("missing-image.jpg")
    http.assert_not_called()
