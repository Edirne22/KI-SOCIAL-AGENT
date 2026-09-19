import os
import base64
import logging
import requests

from generate_agnes_media import agnes_generate_image

logger = logging.getLogger(__name__)

NVIDIA_MODELS = [
    {
        "name": "black-forest-labs/flux.1-schnell",
        "steps": 4,
        "extra": {},
    },
    {
        "name": "black-forest-labs/flux.1-dev",
        "steps": 50,
        "extra": {
            "mode": "",
            "image": "",
            "cfg_scale": 5,
        },
    },
]

API_PROVIDERS = ["cloudflare", "together", "pollinations", "nvidia"]


class ImageRouter:
    """Router for generating images using a multi-provider fallback chain."""

    def _get_chain(self) -> list:
        primary = os.environ.get("IMAGE_PRIMARY", "cloudflare").strip().lower()
        if primary in API_PROVIDERS:
            idx = API_PROVIDERS.index(primary)
            return API_PROVIDERS[idx:] + API_PROVIDERS[:idx] + ["agnes"]
        elif primary == "agnes":
            return ["agnes"] + API_PROVIDERS
        else:
            return API_PROVIDERS + ["agnes"]

    def _generate_cloudflare(self, prompt: str, **kwargs) -> bytes | None:
        account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not account_id or not api_token:
            logger.warning("image_router: Cloudflare credentials missing.")
            return None

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 1024),
            "seed": kwargs.get("seed", 0),
            "steps": kwargs.get("steps", 4),
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                logger.error(f"image_router: Cloudflare error status {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            result = data.get("result")
            b64_str = None
            if isinstance(result, dict):
                b64_str = result.get("image") or result.get("b64_json") or result.get("base64")
            elif isinstance(result, str):
                b64_str = result
            else:
                b64_str = data.get("image")

            if not b64_str:
                logger.error(f"image_router: Cloudflare response missing image data: {data}")
                return None

            return base64.b64decode(b64_str)
        except Exception as e:
            logger.error(f"image_router: Cloudflare exception: {e}")
            return None

    def _generate_together(self, prompt: str, **kwargs) -> bytes | None:
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            logger.warning("image_router: TOGETHER_API_KEY missing.")
            return None

        url = "https://api.together.ai/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell-Free",
            "prompt": prompt,
            "steps": kwargs.get("steps", 4),
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 1024),
            "response_format": "base64",
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                logger.error(f"image_router: Together error status {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            b64_str = None
            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                item = data["data"][0]
                b64_str = item.get("b64_json") or item.get("base64")
            elif isinstance(data, dict):
                b64_str = data.get("b64_json")

            if not b64_str:
                logger.error(f"image_router: Together response missing b64_json: {data}")
                return None

            return base64.b64decode(b64_str)
        except Exception as e:
            logger.error(f"image_router: Together exception: {e}")
            return None

    def _generate_pollinations(self, prompt: str, **kwargs) -> bytes | None:
        api_key = os.environ.get("POLLINATIONS_API_KEY")
        if not api_key:
            logger.warning("image_router: POLLINATIONS_API_KEY missing.")
            return None

        url = "https://gen.pollinations.ai/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "flux",
            "prompt": prompt,
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 1024),
            "response_format": "b64_json",
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                logger.error(f"image_router: Pollinations error status {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            b64_str = None
            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                item = data["data"][0]
                b64_str = item.get("b64_json") or item.get("base64")
            elif isinstance(data, dict):
                b64_str = data.get("b64_json")

            if not b64_str:
                logger.error(f"image_router: Pollinations response missing b64_json: {data}")
                return None

            return base64.b64decode(b64_str)
        except Exception as e:
            logger.error(f"image_router: Pollinations exception: {e}")
            return None

    def _generate_nvidia(self, prompt: str, **kwargs) -> bytes | None:
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            logger.warning("image_router: NVIDIA_API_KEY missing.")
            return None

        api_style = os.environ.get("NVIDIA_IMAGE_API_STYLE", "genai").lower()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        for model_info in NVIDIA_MODELS:
            model_name = model_info["name"]

            if api_style == "openai":
                url = "https://integrate.api.nvidia.com/v1/images/generations"
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    "n": 1,
                    "size": kwargs.get("size", "1024x1024"),
                }
            else:
                url = f"https://ai.api.nvidia.com/v1/genai/{model_name}"
                payload = {
                    "prompt": prompt,
                    "width": 1024,
                    "height": 1024,
                    "seed": kwargs.get("seed", 0),
                    "steps": model_info["steps"],
                }
                payload.update(model_info["extra"])

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=180)
            except Exception as e:
                logger.error(f"image_router: Network/timeout error for model {model_name}: {e}")
                continue

            if response.status_code == 200:
                try:
                    data = response.json()
                    if api_style == "openai":
                        b64_str = data["data"][0]["b64_json"]
                    else:
                        b64_str = data["artifacts"][0]["base64"]
                    img_bytes = base64.b64decode(b64_str)
                    logger.info(f"image_router: generated via {model_name}")
                    return img_bytes
                except (KeyError, IndexError, TypeError, ValueError) as err:
                    logger.error(f"image_router: Failed to parse response from {model_name}: {err}")
                    continue

            elif response.status_code == 429:
                logger.warning(
                    f"image_router: Rate limit 429 for model {model_name}. Moving to next model immediately."
                )
                continue

            elif 500 <= response.status_code < 600:
                logger.error(
                    f"image_router: Server error {response.status_code} for model {model_name}."
                )
                continue

            else:
                logger.error(
                    f"image_router: HTTP error {response.status_code} for model {model_name}: {response.text[:200]}"
                )
                continue

        return None

    def _generate_agnes(self, prompt: str, **kwargs) -> bytes | None:
        try:
            img = agnes_generate_image(prompt)
            if img:
                return img
        except Exception as e:
            logger.error(f"image_router: Agnes exception: {e}")
        return None

    def generate_image(self, prompt: str, **kwargs) -> bytes:
        chain = self._get_chain()
        logger.info(f"image_router: Provider chain is {chain}")

        for provider in chain:
            img_bytes = None
            if provider == "cloudflare":
                img_bytes = self._generate_cloudflare(prompt, **kwargs)
            elif provider == "together":
                img_bytes = self._generate_together(prompt, **kwargs)
            elif provider == "pollinations":
                img_bytes = self._generate_pollinations(prompt, **kwargs)
            elif provider == "nvidia":
                img_bytes = self._generate_nvidia(prompt, **kwargs)
            elif provider == "agnes":
                img_bytes = self._generate_agnes(prompt, **kwargs)

            if img_bytes:
                logger.info(f"image_router: Successfully generated image using provider '{provider}'")
                return img_bytes

        raise RuntimeError("All image generation providers failed in the fallback chain.")
