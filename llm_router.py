"""Zentraler Multi-Modell-Router. Wechselt bei 429 automatisch den Anbieter."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable

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
            "max_tokens": min(MAX_TOKENS, 256) if provider == "claude_openrouter" else MAX_TOKENS,
        }
        if task_type == "weekly_plan" and provider == "groq" and model == "openai/gpt-oss-120b":
            # Reserve the existing bounded output for the plan, not visible reasoning.
            payload.update(reasoning_effort="low", include_reasoning=False)

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as e:
            print(f"[router] {provider} Netzwerkfehler: {type(e).__name__}")
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
            print(f"[router] {provider} HTTP {r.status_code}")
            return None

        try:
            data = r.json()
            if task_type == "daily_ideas" and data["choices"][0].get("finish_reason") == "length":
                print("[router] Daily-Ideas-Antwort abgeschnitten; naechsten Anbieter versuchen.")
                return None
            if task_type == "weekly_plan":
                if not isinstance(data["choices"][0], dict):
                    print("[router] Wochenplan-Antwortschema ungültig.")
                    return None
                finish = data["choices"][0].get("finish_reason")
                print(f"[router] Wochenplan via {provider}, Modell {model}, Abschluss {finish}.")
                if finish == "length":
                    print("[router] Wochenplan am Tokenlimit abgebrochen; Antwort verworfen.")
                    return None
            text = data["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                print(f"[router] {provider} Antwort enthaelt keinen verwendbaren Text.")
                return None
            return text.strip()
        except (KeyError, IndexError, TypeError, ValueError) as e:
            print(f"[router] {provider} Antwort-Parsing fehlgeschlagen: {type(e).__name__}")
            return None

    def chat(
        self,
        messages: list[dict],
        task_type: str = "default",
        model_override: str | None = None,
        response_validator: Callable[[str], None] | None = None,
    ) -> str:
        # Claude-only is a verified model-family lock, never a generic provider fallback.
        if task_type == "claude_only":
            allowed = "anthropic/claude-sonnet-4.5"
            if model_override is not None and model_override != allowed:
                raise ValueError("claude_only forbids a non-approved model override")
            exact = self.config["task_routing"].get("claude_only")
            if exact != ["claude_openrouter"]:
                raise RuntimeError("Claude-only routing contract invalid")
            cfg = self.config["providers"].get("claude_openrouter", {})
            if cfg.get("models", {}).get("claude_only") != allowed:
                raise RuntimeError("Claude-only model contract invalid")
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
                if response_validator is not None:
                    try:
                        response_validator(result)
                    except (ValueError, RuntimeError):
                        # Never log model output or context; try each provider only once.
                        print(f"[router] {provider}: Antwortvalidierung fehlgeschlagen; nächster Anbieter.")
                        continue
                print(f"[router] Erfolg via {provider}")
                return result

        raise RuntimeError(
            "Alle konfigurierten KI-Anbieter fehlgeschlagen; keine verwendbare Textantwort."
        )


_router: LLMRouter | None = None


def get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


def quick_chat(prompt: str, task_type: str = "default", *,
               response_validator: Callable[[str], None] | None = None) -> str:
    return get_router().chat(
        messages=[{"role": "user", "content": prompt}],
        task_type=task_type,
        response_validator=response_validator,
    )
