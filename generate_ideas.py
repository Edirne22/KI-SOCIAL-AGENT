import os
import re
import requests
from datetime import datetime

def generate_ideas():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    prompt = """Erstelle 3 verschiedene Content-Ideen für einen Social-Media-Agenten.
Themen: Motorrad, Reisen, Lifestyle, Technik, KI, MotoGP.
Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige.
Stil: locker, per Du, wenige Emojis, kurze Captions.
Wichtig: Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.

Formatiere die Antwort exakt so:

--- IDEE 1 ---
Titel: ...
Plattform: Instagram/TikTok/Facebook/Reel/Story
Thema: ...
Hook: ...
Beschreibung: ...

--- IDEE 2 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...
Beschreibung: ...

--- IDEE 3 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...
Beschreibung: ...
"""

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        # Entferne lange Strings, die wie Secrets aussehen könnten
        text_clean = re.sub(r'\b[A-Za-z0-9_\-]{20,}\b', '[ENTFERNT]', text)
        return text_clean.strip()
    except Exception as e:
        return f"FEHLER bei API-Anfrage: {e}"

def save_ideas(ideas):
    os.makedirs("content", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n\n## Ideen vom {timestamp}\n{ideas}\n"
    with open("content/GENERATED_IDEAS.md", "a", encoding="utf-8") as f:
        f.write(entry)
    print("Ideen gespeichert.")

if __name__ == "__main__":
    ideas = generate_ideas()
    save_ideas(ideas)
