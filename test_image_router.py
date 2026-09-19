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


def test_cloudflare_called_first_when_primary_cloudflare(monkeypatch):
    monkeypatch.setenv("IMAGE_PRIMARY", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "cf-acc-123")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-tok-456")

    fake_bytes = b"fake_cloudflare_bytes"
    b64_data = base64.b64encode(fake_bytes).decode("utf-8")
    resp_200 = create_mock_response(200, json_data={"result": {"image": b64_data}})

    with patch("requests.post", return_value=resp_200) as mock_post, \
         patch("image_router.agnes_generate_image") as mock_agnes:
        router = ImageRouter()
        res = router.generate_image("a racing motorcycle")

        assert res == fake_bytes
        assert mock_post.call_count == 1
        url = mock_post.call_args[0][0]
        assert "api.cloudflare.com" in url
        assert "cf-acc-123" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["prompt"] == "a racing motorcycle"
        assert payload["width"] == 1024
        assert payload["height"] == 1024
        mock_agnes.assert_not_called()


def test_together_called_first_when_primary_together(monkeypatch):
    monkeypatch.setenv("IMAGE_PRIMARY", "together")
    monkeypatch.setenv("TOGETHER_API_KEY", "together-key-123")

    fake_bytes = b"fake_together_bytes"
    b64_data = base64.b64encode(fake_bytes).decode("utf-8")
    resp_200 = create_mock_response(200, json_data={"data": [{"b64_json": b64_data}]})

    with patch("requests.post", return_value=resp_200) as mock_post, \
         patch("image_router.agnes_generate_image") as mock_agnes:
        router = ImageRouter()
        res = router.generate_image("a racing motorcycle")

        assert res == fake_bytes
        assert mock_post.call_count == 1
        url = mock_post.call_args[0][0]
        assert "api.together.ai" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "black-forest-labs/FLUX.1-schnell-Free"
        assert payload["prompt"] == "a racing motorcycle"
        mock_agnes.assert_not_called()


def test_pollinations_called_first_when_primary_pollinations(monkeypatch):
    monkeypatch.setenv("IMAGE_PRIMARY", "pollinations")
    monkeypatch.setenv("POLLINATIONS_API_KEY", "sk_pollinations_key")

    fake_bytes = b"fake_pollinations_bytes"
    b64_data = base64.b64encode(fake_bytes).decode("utf-8")
    resp_200 = create_mock_response(200, json_data={"data": [{"b64_json": b64_data}]})

    with patch("requests.post", return_value=resp_200) as mock_post, \
         patch("image_router.agnes_generate_image") as mock_agnes:
        router = ImageRouter()
        res = router.generate_image("a racing motorcycle")

        assert res == fake_bytes
        assert mock_post.call_count == 1
        url = mock_post.call_args[0][0]
        assert "gen.pollinations.ai" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "flux"
        assert payload["prompt"] == "a racing motorcycle"
        mock_agnes.assert_not_called()


def test_chain_fallback_on_failure(monkeypatch):
    monkeypatch.setenv("IMAGE_PRIMARY", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "cf-acc")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-tok")
    monkeypatch.setenv("TOGETHER_API_KEY", "tog-key")

    cf_fail_resp = create_mock_response(500, text="Cloudflare server error")

    together_bytes = b"together_fallback_bytes"
    tog_b64 = base64.b64encode(together_bytes).decode("utf-8")
    tog_success_resp = create_mock_response(200, json_data={"data": [{"b64_json": tog_b64}]})

    side_effects = [cf_fail_resp, tog_success_resp]

    with patch("requests.post", side_effect=side_effects) as mock_post:
        router = ImageRouter()
        res = router.generate_image("fallback test prompt")

        assert res == together_bytes
        assert mock_post.call_count == 2
        # First call was cloudflare, second was together
        assert "api.cloudflare.com" in mock_post.call_args_list[0][0][0]
        assert "api.together.ai" in mock_post.call_args_list[1][0][0]


def test_all_providers_fail_raises_runtime_error(monkeypatch):
    monkeypatch.setenv("IMAGE_PRIMARY", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "cf-acc")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-tok")
    monkeypatch.setenv("TOGETHER_API_KEY", "tog-key")
    monkeypatch.setenv("POLLINATIONS_API_KEY", "pol-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")

    fail_resp = create_mock_response(500, text="Server Error")

    with patch("requests.post", return_value=fail_resp) as mock_post, \
         patch("image_router.agnes_generate_image", return_value=None) as mock_agnes:
        router = ImageRouter()
        with pytest.raises(RuntimeError, match="All image generation providers failed"):
            router.generate_image("should fail")

        mock_agnes.assert_called_once_with("should fail")


def test_fallback_to_agnes_when_all_apis_fail(monkeypatch):
    monkeypatch.setenv("IMAGE_PRIMARY", "cloudflare")

    agnes_bytes = b"fake_agnes_image_bytes"
    response_500 = create_mock_response(500, text="Server error")

    with patch("requests.post", return_value=response_500) as mock_post, \
         patch("image_router.agnes_generate_image", return_value=agnes_bytes) as mock_agnes:
        router = ImageRouter()
        res = router.generate_image("a fast motorcycle")

        assert res == agnes_bytes
        mock_agnes.assert_called_once_with("a fast motorcycle")
