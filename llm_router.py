"""Zentraler Multi-Modell-Router. Wechselt bei 429 automatisch den Anbieter."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

# Absoluter Pfad, unabhängig vom Aufruf-Verzeichnis
CONFIG_PATH = Path(__file__).resolve().parent / "config" / "llm_providers.json"

# Maximale Tokens pro Antwort (Kosten- und Missbrauchsschutz)
MAX_TOKENS = 2000


class LLMRouter:
    def __init__(self, config_path: Path = CONFIG_PATH):
        if not config_path.exists():
            raise FileNotFoundError(f"Router-Config fehlt: {config_path}")
        self.config = json.loads(config_path.read_text(encoding="utf-8"))
        self._validate_config()
        self._cooldowns: dict[str, float] = {}

    def _validate_config(self):
        """Prüft, ob die Config die notwendigen Felder enthält."""
        required = ["providers", "fallback_order", "task_routing"]
        for key in required:
            if key not in self.config:
                raise ValueError(f"Router-Config unvollständig: '{key}' fehlt")
        if not isinstance(self.config["providers"], dict):
            raise ValueError("Router-Config: 'providers' muss ein Objekt sein")
        for name, cfg in self.config["providers"].items():
            for field in ("base_url", "api_key_env", "models"):
                if field not in cfg:
                    raise ValueError(f"Provider '{name}' fehlt Feld: {field}")

    def _is_available(self, provider: str) -> bool:
        return time.time() >= self._cooldowns.get(provider, 0)

    def _set_cooldown(self, provider: str, seconds: int = 60):
        self._cooldowns[provider] = time.time() + seconds

    def _build_url(self, provider: str, cfg: dict) -> str:
        url = cfg["base_url"]
        if "{account_id}" in url:
            account_id = os.environ.get(cfg.get("account_id_env", ""), "")
            if not account_id:
                print(f"[router] {provider}: Account-ID fehlt, übersprungen.")
                return ""
            url = url.replace("{account_id}", account_id)
        return url.rstrip("/") + "/chat/completions"

    def _build_headers(self, cfg: dict) -> dict | None:
        key = os.environ.get(cfg["api_key_env"], "")
        if not key:
            return None
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _call_provider(
        self,
        provider: str,
        cfg: dict,
        messages: list[dict],
        task_type: str,
        model_override: str | None = None,
    ) -> str | None:
        models = cfg.get("models", {})
        model = model_override or models.get(task_type) or models.get("default")
        if not model:
            return None

        url = self._build_url(provider, cfg)
        if not url:
            return None

        headers = self._build_headers(cfg)
        if not headers:
            print(f"[router] {provider}: API-Key fehlt, übersprungen.")
            return None

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": MAX_TOKENS,
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as e:
            print(f"[router] {provider} Netzwerkfehler: {e}")
            return None

        if r.status_code == 429:
            # Retry-After-Header beachten, falls vorhanden
            try:
                retry_after = int(r.headers.get("Retry-After", 60))
            except (ValueError, TypeError):
                retry_after = 60
            print(f"[router] {provider} 429; Cooldown {retry_after}s.")
            self._set_cooldown(provider, retry_after)
            return None

        if r.status_code >= 500:
            print(f"[router] {provider} HTTP {r.status_code}; Cooldown 30s.")
            self._set_cooldown(provider, 30)
            return None

        if r.status_code != 200:
            print(f"[router] {provider} HTTP {r.status_code}: {r.text[:200]}")
            return None

        try:
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"[router] {provider} Antwort-Parsing fehlgeschlagen: {e}")
            return None

    def chat(
        self,
        messages: list[dict],
        task_type: str = "default",
        model_override: str | None = None,
    ) -> str:
        order = self.config["task_routing"].get(task_type, self.config["fallback_order"])

        for provider in order:
            if not self._is_available(provider):
                continue
            cfg = self.config["providers"].get(provider)
            if not cfg:
                continue
            print(f"[router] Versuch: {provider}")
            result = self._call_provider(provider, cfg, messages, task_type, model_override)
            if result:
                print(f"[router] Erfolg via {provider}")
                return result

        raise RuntimeError(
            "Alle verfügbaren KI-Anbieter fehlgeschlagen (Rate-Limits oder Keys fehlen)."
        )


_router: LLMRouter | None = None


def get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


def quick_chat(prompt: str, task_type: str = "default") -> str:
    return get_router().chat(
        messages=[{"role": "user", "content": prompt}],
        task_type=task_type,
    )
