"""Konfigurationsbasierter Model Router für den KI Social Media Agent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "model_router.json"


def load_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Lädt und prüft die Router-Konfiguration."""
    with config_path.open(encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config.get("providers"), dict) or not isinstance(config.get("tasks"), dict):
        raise ValueError("Router-Konfiguration benötigt 'providers' und 'tasks'.")
    return config


def get_task_config(task_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    try:
        return config["tasks"][task_name]
    except KeyError as error:
        available = ", ".join(sorted(config["tasks"]))
        raise KeyError(f"Unbekannte Aufgabe '{task_name}'. Verfügbar: {available}") from error


def get_provider_for_task(task_name: str, config: dict[str, Any] | None = None) -> str:
    """Gibt den aktivierten Provider für eine Aufgabe zurück."""
    config = config or load_config()
    provider_name = get_task_config(task_name, config)["provider"]
    provider = get_provider_config(provider_name, config)
    if not provider.get("enabled", False):
        raise RuntimeError(f"Provider '{provider_name}' ist für '{task_name}' deaktiviert.")
    return provider_name


def get_provider_config(provider_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Gibt die öffentliche Provider-Konfiguration ohne Geheimnisse zurück."""
    config = config or load_config()
    try:
        return config["providers"][provider_name]
    except KeyError as error:
        available = ", ".join(sorted(config["providers"]))
        raise KeyError(f"Unbekannter Provider '{provider_name}'. Verfügbar: {available}") from error


def get_api_key(provider_name: str, config: dict[str, Any] | None = None) -> str:
    """Liest den API-Key ausschließlich aus der angegebenen Umgebungsvariable."""
    provider = get_provider_config(provider_name, config)
    env_name = provider.get("api_key_env")
    if not env_name:
        raise ValueError(f"Provider '{provider_name}' hat keine api_key_env-Konfiguration.")

    api_key = os.environ.get(env_name)
    if not api_key:
        raise RuntimeError(f"Benötigtes Secret '{env_name}' ist nicht gesetzt.")
    return api_key


def list_task_routes(config: dict[str, Any] | None = None) -> list[tuple[str, str, str]]:
    """Gibt Aufgaben mit Provider und Antworttyp für die Anzeige zurück."""
    config = config or load_config()
    return [
        (task_name, task_config["provider"], task_config["response_type"])
        for task_name, task_config in sorted(config["tasks"].items())
    ]


if __name__ == "__main__":
    router_config = load_config()
    print("Model Router – konfigurierte Routen")
    for task, provider, response_type in list_task_routes(router_config):
        enabled = router_config["providers"][provider].get("enabled", False)
        state = "aktiv" if enabled else "deaktiviert"
        print(f"- {task}: {provider} ({response_type}, {state})")
