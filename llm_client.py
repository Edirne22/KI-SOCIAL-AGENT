"""Einheitlicher Client für konfigurierbare Text-, Bild- und Video-Aufgaben."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Sequence

import requests

from router import get_api_key, get_provider_config, get_provider_for_task, get_task_config

SECRET_PATTERNS = (
    (re.compile(r"AIza[0-9A-Za-z_-]{35}"), "[ENTFERNT]"),
    (re.compile(r"AQ\.[A-Za-z0-9_-]{40,}"), "[ENTFERNT]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "[ENTFERNT]"),
    (re.compile(r"\b[A-Za-z0-9_-]{50,}\b"), "[ENTFERNT]"),
)


def redact_secrets(value: str) -> str:
    """Entfernt bekannte Schlüssel- und Tokenmuster aus Ausgaben."""
    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def load_agent(agent_file: str) -> str:
    """Lädt eine Agenten-Anweisung aus dem lokalen Verzeichnis ``agents/``.

    Es sind nur Dateinamen innerhalb von ``agents/`` erlaubt. Dadurch können
    Prompt-Aufrufe keine beliebigen Dateien aus dem Runner lesen.
    """
    requested_name = agent_file.strip()
    if requested_name.endswith(".md"):
        requested_name = requested_name[:-3]

    if not requested_name or "/" in requested_name or "\\" in requested_name or requested_name in {".", ".."}:
        raise ValueError("Agenten-Datei muss als einfacher Name ohne Pfad angegeben werden.")

    agents_dir = Path(__file__).resolve().parent / "agents"
    agent_path = (agents_dir / f"{requested_name}.md").resolve()
    if agent_path.parent != agents_dir.resolve():
        raise ValueError("Ungültiger Agenten-Dateiname.")

    try:
        return agent_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Agenten-Datei nicht gefunden: {agent_path.name}") from error


def get_agent_context(agent_names: Sequence[str]) -> str:
    """Kombiniert die Anweisungen der angeforderten Agenten für einen Prompt."""
    contexts: list[str] = []
    for agent_name in agent_names:
        normalized_name = agent_name[:-3] if agent_name.endswith(".md") else agent_name
        content = load_agent(normalized_name)
        contexts.append(f"--- Agent: {normalized_name} ---\n{content}")

    return "\n\n".join(contexts)


def _request_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    response = requests.request(method, url, headers=headers, json=payload, timeout=timeout)
    if not response.ok:
        detail = redact_secrets(response.text[:500])
        raise RuntimeError(f"Provider-Anfrage fehlgeschlagen (HTTP {response.status_code}): {detail}")
    return response.json()


def _generate_gemini(prompt: str, provider: dict[str, Any], api_key: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key,
    }
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    errors: list[str] = []

    for model in provider["text_models"]:
        url = f"{provider['base_url']}/models/{model}:generateContent"
        try:
            data = _request_json("POST", url, headers, payload, provider["timeout_seconds"])
            return redact_secrets(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
        except (KeyError, IndexError, TypeError) as error:
            errors.append(f"{model}: unvollständige Antwort ({error})")
        except RuntimeError as error:
            errors.append(f"{model}: {error}")

    raise RuntimeError("Kein Gemini-Modell konnte die Aufgabe ausführen. " + " | ".join(errors))


def _generate_agnes_text(prompt: str, provider: dict[str, Any], api_key: str) -> str:
    data = _request_json(
        "POST",
        f"{provider['base_url']}/chat/completions",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {
            "model": provider["chat_model"],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        provider["timeout_seconds"],
    )
    return redact_secrets(data["choices"][0]["message"]["content"]).strip()


def _generate_agnes_image(prompt: str, provider: dict[str, Any], api_key: str) -> dict[str, Any]:
    return _request_json(
        "POST",
        f"{provider['base_url']}/images/generations",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {"model": provider["image_model"], "prompt": prompt, "size": "1024x1024", "n": 1},
        provider["timeout_seconds"],
    )


def _start_agnes_video(prompt: str, provider: dict[str, Any], api_key: str) -> dict[str, Any]:
    return _request_json(
        "POST",
        f"{provider['base_url']}/videos",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {"model": provider["video_model"], "prompt": prompt, "duration": 5, "size": "720x1280"},
        provider["timeout_seconds"],
    )


def generate(task_name: str, prompt: str) -> str | dict[str, Any]:
    """Führt eine Aufgabe mit dem zugeordneten Provider aus.

    Kritische externe Aktionen werden hier nicht ausgelöst. Bild- und Video-Aufgaben
    erzeugen nur Medien; Veröffentlichung bleibt Aufgabe der bestehenden Freigabe-Workflows.
    """
    task = get_task_config(task_name)
    provider_name = get_provider_for_task(task_name)
    provider = get_provider_config(provider_name)
    api_key = get_api_key(provider_name)

    if provider_name == "gemini":
        if task["response_type"] != "text":
            raise ValueError(f"Gemini unterstützt im Router keine Aufgabe vom Typ {task['response_type']}.")
        return _generate_gemini(prompt, provider, api_key)

    if provider_name == "agnes":
        if task["response_type"] == "text":
            return _generate_agnes_text(prompt, provider, api_key)
        if task["response_type"] == "image":
            return _generate_agnes_image(prompt, provider, api_key)
        if task["response_type"] == "video":
            return _start_agnes_video(prompt, provider, api_key)

    raise ValueError(f"Keine Client-Implementierung für Provider '{provider_name}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Testet eine Model-Router-Aufgabe.")
    parser.add_argument("--task", default="content_ideas", help="Name der Router-Aufgabe")
    parser.add_argument("--prompt", default="Nenne eine kurze Motorrad-Content-Idee.")
    args = parser.parse_args()

    result = generate(args.task, args.prompt)
    if isinstance(result, str):
        print(result)
    else:
        print(redact_secrets(str(result)))
