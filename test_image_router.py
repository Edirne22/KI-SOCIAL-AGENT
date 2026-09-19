import base64
import os
import pytest
from unittest.mock import patch, MagicMock

from image_router import ImageRouter


def create_mock_response(status_code, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


def test_missing_nvidia_api_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    router = ImageRouter()
    with pytest.raises(RuntimeError, match="NVIDIA_API_KEY"):
        router.generate_image("a test prompt")


def test_schnell_payload_and_200(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_IMAGE_API_STYLE", "genai")

    fake_bytes = b"fake_image_bytes_schnell"
    b64_data = base64.b64encode(fake_bytes).decode("utf-8")

    response_200 = create_mock_response(
        200, json_data={"artifacts": [{"base64": b64_data}]}
    )

    with patch("requests.post", return_value=response_200) as mock_post, \
         patch("image_router.agnes_generate_image") as mock_agnes:
        router = ImageRouter()
        result = router.generate_image("a fast motorcycle")

        assert result == fake_bytes
        assert mock_post.call_count == 1
        assert "flux.1-schnell" in mock_post.call_args[0][0]
        assert mock_post.call_args[1]["timeout"] == 180

        payload = mock_post.call_args[1]["json"]
        assert payload["prompt"] == "a fast motorcycle"
        assert payload["width"] == 1024
        assert payload["height"] == 1024
        assert payload["seed"] == 0
        assert payload["steps"] == 4
        assert "mode" not in payload
        assert "image" not in payload
        assert "cfg_scale" not in payload
        mock_agnes.assert_not_called()


def test_fallback_to_dev_on_429(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_IMAGE_API_STYLE", "genai")

    fake_bytes = b"fake_image_bytes_dev"
    b64_data = base64.b64encode(fake_bytes).decode("utf-8")

    response_429 = create_mock_response(429, text="Rate limit exceeded")
    response_200 = create_mock_response(
        200, json_data={"artifacts": [{"base64": b64_data}]}
    )

    # 1 attempt for schnell returns 429 -> immediate fallback to dev
    side_effects = [response_429, response_200]

    with patch("requests.post", side_effect=side_effects) as mock_post, \
         patch("time.sleep") as mock_sleep, \
         patch("image_router.agnes_generate_image") as mock_agnes:
        router = ImageRouter()
        result = router.generate_image("a fast motorcycle")

        assert result == fake_bytes
        assert mock_post.call_count == 2
        mock_sleep.assert_not_called()  # No retries/sleep

        assert "flux.1-dev" in mock_post.call_args[0][0]
        dev_payload = mock_post.call_args[1]["json"]
        assert dev_payload["prompt"] == "a fast motorcycle"
        assert dev_payload["width"] == 1024
        assert dev_payload["height"] == 1024
        assert dev_payload["seed"] == 0
        assert dev_payload["steps"] == 50
        assert dev_payload["mode"] == ""
        assert dev_payload["image"] == ""
        assert dev_payload["cfg_scale"] == 5
        mock_agnes.assert_not_called()


def test_fallback_to_agnes_when_both_fail(monkeypatch, caplog):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_IMAGE_API_STYLE", "genai")

    agnes_bytes = b"fake_agnes_image_bytes"
    response_500 = create_mock_response(500, text="Server error")

    with patch("requests.post", return_value=response_500) as mock_post, \
         patch("image_router.agnes_generate_image", return_value=agnes_bytes) as mock_agnes:
        router = ImageRouter()
        result = router.generate_image("a fast motorcycle")

        assert result == agnes_bytes
        assert mock_post.call_count == 2  # 1 try for schnell, 1 try for dev
        mock_agnes.assert_called_once_with("a fast motorcycle")
        assert "image_router: NVIDIA chain exhausted, using Agnes" in caplog.text


def test_both_api_styles_produce_bytes(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")

    genai_bytes = b"genai_bytes"
    genai_b64 = base64.b64encode(genai_bytes).decode("utf-8")
    genai_resp = create_mock_response(
        200, json_data={"artifacts": [{"base64": genai_b64}]}
    )

    openai_bytes = b"openai_bytes"
    openai_b64 = base64.b64encode(openai_bytes).decode("utf-8")
    openai_resp = create_mock_response(
        200, json_data={"data": [{"b64_json": openai_b64}]}
    )

    # Test genai style
    monkeypatch.setenv("NVIDIA_IMAGE_API_STYLE", "genai")
    with patch("requests.post", return_value=genai_resp) as mock_post_genai:
        router = ImageRouter()
        res_genai = router.generate_image("prompt1")
        assert res_genai == genai_bytes
        assert "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell" in mock_post_genai.call_args[0][0]

    # Test openai style
    monkeypatch.setenv("NVIDIA_IMAGE_API_STYLE", "openai")
    with patch("requests.post", return_value=openai_resp) as mock_post_openai:
        router = ImageRouter()
        res_openai = router.generate_image("prompt2")
        assert res_openai == openai_bytes
        assert mock_post_openai.call_args[0][0] == "https://integrate.api.nvidia.com/v1/images/generations"
        json_body = mock_post_openai.call_args[1]["json"]
        assert json_body["model"] == "black-forest-labs/flux.1-schnell"
