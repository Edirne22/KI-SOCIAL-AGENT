import os
import base64
import logging
import time
import requests

from generate_agnes_media import agnes_generate_image

logger = logging.getLogger(__name__)

NVIDIA_MODELS = [
    {
        "name": "black-forest-labs/flux.1-schnell",
        "steps": 4,
        "cfg_scale": 0,
        "include_mode": True,
    },
    {
        "name": "black-forest-labs/flux.1-dev",
        "steps": 28,
        "cfg_scale": 3.5,
        "include_mode": True,
    },
    {
        "name": "black-forest-labs/flux.2-klein-4b",
        "steps": 4,
        "cfg_scale": 0,
        "include_mode": False,
    },
]


class ImageRouter:
    """Router for generating images using NVIDIA FLUX models with fallback to Agnes AI."""

    def generate_image(self, prompt: str, **kwargs) -> bytes:
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY environment variable is missing.")

        api_style = os.environ.get("NVIDIA_IMAGE_API_STYLE", "genai").lower()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        backoff_delays = [1, 2, 4]

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
                    "samples": 1,
                    "seed": kwargs.get("seed", 0),
                    "steps": kwargs.get("steps", model_info["steps"]),
                    "cfg_scale": kwargs.get("cfg_scale", model_info["cfg_scale"]),
                }
                if model_info.get("include_mode"):
                    payload["mode"] = "base"

            model_failed = False
            for attempt in range(4):  # initial attempt + up to 3 retries
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=60)
                except Exception as e:
                    logger.error(f"image_router: Network error for model {model_name}: {e}")
                    model_failed = True
                    break

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
                        model_failed = True
                        break

                elif response.status_code == 429:
                    if attempt < 3:
                        delay = backoff_delays[attempt]
                        logger.warning(
                            f"image_router: Rate limit 429 for model {model_name}. Retrying in {delay}s (attempt {attempt + 1}/3)..."
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            f"image_router: Rate limit 429 persisted for model {model_name} after 3 retries."
                        )
                        model_failed = True
                        break

                elif 500 <= response.status_code < 600:
                    logger.error(
                        f"image_router: Server error {response.status_code} for model {model_name}."
                    )
                    model_failed = True
                    break

                else:  # 4xx error (excluding 429) or other statuses
                    logger.error(
                        f"image_router: HTTP error {response.status_code} for model {model_name}: {response.text[:200]}"
                    )
                    model_failed = True
                    break

            if model_failed:
                continue

        logger.warning("image_router: NVIDIA chain exhausted, using Agnes")
        return agnes_generate_image(prompt)
