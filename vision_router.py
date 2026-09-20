# vision_router.py
import base64
import binascii
import json
import logging
import os
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODELS = {
    "general": "meta/muse-glimmer-30b",
    "ocr": "nvidia/nemotron-ocr-v2",
    "omni": "nvidia/nemotron-3-nano-omni",
}
FALLBACK_MODEL = "moonshotai/kimi-k3"
PROMPTS = {
    "general": (
        "Analysiere diesen Screenshot auf Deutsch und antworte "
        "ausschließlich auf Deutsch.\n"
        "Beschreibe:\n\n"
        "1. Was ist zu sehen? (Szene, Objekte, Personen)\n"
        "2. Welcher Text ist im Bild sichtbar? (zitiere ihn wörtlich)\n"
        "3. Welche Plattform/welcher Account? (falls erkennbar)\n"
        "4. Zahlen/Daten, falls sichtbar (Likes, Kommentare, Datum)\n"
        "Erfinde keine Details. Wenn etwas nicht erkennbar ist, "
        "schreibe 'nicht erkennbar'."
    ),
    "ocr": (
        "Extract all text and table structures from this image. "
        'Return strict JSON: {"text": "...", '
        '"tables": [{"headers": [...], "rows": [[...]]}]}'
    ),
    "omni": (
        "Describe this content in detail in German. Include what "
        "you see (image/video frames), any spoken text, "
        "and any written text."
    ),
}


class VisionRouter:
    """Analyze images using NVIDIA models with a general-mode fallback."""

    def analyze(self, image, mode: str = "general") -> dict:
        if mode not in NVIDIA_MODELS:
            raise ValueError("mode must be 'general', 'ocr', or 'omni'.")

        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError(
                "NVIDIA_API_KEY environment variable is missing."
            )

        try:
            image_url = self._image_url(image)
        except (OSError, TypeError, ValueError) as err:
            logger.error("vision_router: Invalid image: %s", err)
            return {"error": str(err)}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        models = [NVIDIA_MODELS[mode]]
        if mode == "general":
            models.append(FALLBACK_MODEL)

        reason = "No model returned a valid response."
        for model_name in models:
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPTS[mode]},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                        ],
                    }
                ],
                "stream": False,
            }

            try:
                response = requests.post(
                    NVIDIA_URL,
                    headers=headers,
                    json=payload,
                    timeout=240 if mode == "general" else 180,
                )

                if response.status_code == 429:
                    logger.warning(
                        "vision_router: Rate limit for %s; no retry.",
                        model_name,
                    )

                if response.status_code != 200:
                    raise ValueError(f"HTTP {response.status_code}")

                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Missing or empty response content.")

                if mode == "ocr":
                    result = self._parse_ocr(content)
                else:
                    result = {"description": content}

                result["model_used"] = model_name
                logger.info("vision_router: analyzed via %s", model_name)
                return result
            except (
                requests.RequestException,
                KeyError,
                IndexError,
                TypeError,
                ValueError,
            ) as err:
                reason = f"{model_name}: {err}"
                logger.error("vision_router: Failed for %s", reason)
                if mode == "general" and model_name != FALLBACK_MODEL:
                    logger.warning(
                        "vision_router: Falling back to %s",
                        FALLBACK_MODEL,
                    )

        return {"error": reason}

    @staticmethod
    def _image_url(image):
        if isinstance(image, bytes):
            raw = image
        elif isinstance(image, str):
            try:
                is_file = Path(image).is_file()
            except (OSError, ValueError):
                is_file = False

            if is_file:
                raw = Path(image).read_bytes()
            else:
                encoded = image
                if image.startswith("data:"):
                    prefix, separator, encoded = image.partition(",")
                    if not separator or not prefix.endswith(";base64"):
                        raise ValueError("Invalid base64 image data URL.")

                try:
                    raw = base64.b64decode(
                        "".join(encoded.split()),
                        validate=True,
                    )
                except (binascii.Error, ValueError) as err:
                    raise ValueError(
                        "Image must be an existing file or valid base64."
                    ) from err
        else:
            raise TypeError(
                "Image must be a file path, bytes, or base64 str."
            )

        if not raw:
            raise ValueError("Image is empty.")

        if raw.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        elif raw.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"
        elif raw.startswith((b"GIF87a", b"GIF89a")):
            mime = "image/gif"
        elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
            mime = "image/webp"
        else:
            raise ValueError(
                "Unsupported image format; use JPEG/PNG/GIF/WebP."
            )

        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    @staticmethod
    def _parse_ocr(content):
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("OCR response must be a JSON object.")

        text = result.get("text")
        tables = result.get("tables")
        if not isinstance(text, str) or not isinstance(tables, list):
            raise ValueError("OCR response requires text and tables fields.")

        for table in tables:
            if (
                not isinstance(table, dict)
                or not isinstance(table.get("headers"), list)
                or not isinstance(table.get("rows"), list)
                or not all(isinstance(row, list) for row in table["rows"])
            ):
                raise ValueError("Invalid OCR table headers or rows.")

        return {"text": text, "tables": tables}
