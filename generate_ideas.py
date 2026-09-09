import os
import re
import requests
from datetime import datetime

def get_available_models(api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    headers = {"X-goog-api-key": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        models = [m["name"] for m in data.get("models", [])]
        return models
    except Exception as e:
        return [f"FEHLER beim Abrufen der Modellliste: {e}"]

def generate_idea():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    prompt = """Erstelle eine neue Content-Idee für einen Social-Media-Agenten.
Themen: Motorrad, Reisen, Lifestyle, Technik, KI, MotoGP.
Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige.
Stil: locker, per Du, wenige Emojis, kurze Captions.
Wichtig: Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.
Liefere die Idee im Format:
Titel: ...
Plattform: Instagram/TikTok/Facebook/Reel/Story
Thema: ...
Hook: ...
Kurze Beschreibung: ..."""

    # Aktuell testen wir gemini-3.5-flash in v1beta – aber es könnte andere Modelle geben.
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        text_clean = re.sub(r'\b[A-Za-z0-9_\-]{20,}\b', '[ENTFERNT]', text)
        return text_clean.strip()
    except Exception as e:
        # Wenn ein Fehler auftritt, rufen wir die Modellliste ab, um zu sehen, welche verfügbar sind.
        models = get_available_models(api_key)
        model_list = "\n".join(models)
        return f"FEHLER bei API-Anfrage: {e}\n\nVerfügbare Modelle:\n{model_list}"

def save_idea(idea):
    os.makedirs("content", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n\n## Idee vom {timestamp}\n{idea}\n"
    with open("content/GENERATED_IDEAS.md", "a", encoding="utf-8") as f:
        f.write(entry)
    print("Idee gespeichert.")

if __name__ == "__main__":
    idea = generate_idea()
    save_idea(idea)
