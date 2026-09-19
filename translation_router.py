import logging
import os
import time

import requests

import llm_router

logger = logging.getLogger(__name__)

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "nvidia/riva-translate-4b-instruct-v2"
SUPPORTED_LANGUAGES = ("de", "tr", "en", "fr", "es", "it", "nl", "pl", "ru", "ar")


class TranslationRouter:
    """Translate text using NVIDIA with the existing LLM router as fallback."""

    def translate(self, text: str, source: str, target: str) -> str:
        if source not in SUPPORTED_LANGUAGES or target not in SUPPORTED_LANGUAGES:
            raise ValueError("Unsupported source or target language.")
        if source == target:
            raise ValueError("Source and target languages must differ.")

        api_key = os.environ.get("NVIDIA_API_KEY")
        if api_key:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": NVIDIA_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a translation engine."},
                    {
                        "role": "user",
                        "content": (
                            f"Translate from {source} to {target}. "
                            f"Output only the translation.\n\n{text}"
                        ),
                    },
                ],
                "temperature": 0,
                "top_p": 1,
            }
            for attempt in range(2):
                try:
                    response = requests.post(
                        NVIDIA_URL, headers=headers, json=payload, timeout=60
                    )
                except requests.RequestException:
                    logger.warning("translation_router: NVIDIA request failed.")
                    break

                if response.status_code == 429 and attempt == 0:
                    logger.warning(
                        "translation_router: NVIDIA HTTP 429; retrying once in 3s."
                    )
                    time.sleep(3)
                    continue
                if response.status_code != 200:
                    logger.warning(
                        "translation_router: NVIDIA HTTP %s; using fallback.",
                        response.status_code,
                    )
                    break

                try:
                    content = response.json()["choices"][0]["message"]["content"]
                    if not isinstance(content, str) or not content.strip():
                        raise ValueError("Empty or invalid translation.")
                except (KeyError, IndexError, TypeError, ValueError):
                    logger.warning("translation_router: Invalid NVIDIA response.")
                    break
                logger.info("translation_router: Translated via NVIDIA.")
                return content
        else:
            logger.info("translation_router: NVIDIA_API_KEY missing.")

        logger.info("translation_router: Using llm_router fallback.")
        return llm_router.quick_chat(
            f"Translate from {source} to {target}. Return ONLY the translation.\n"
            f"Text: {text}"
        )
