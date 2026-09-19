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

            else:  # 4xx error (excluding 429) or other statuses
                logger.error(
                    f"image_router: HTTP error {response.status_code} for model {model_name}: {response.text[:200]}"
                )
                continue

        logger.warning("image_router: NVIDIA chain exhausted, using Agnes")
        return agnes_generate_image(prompt)
