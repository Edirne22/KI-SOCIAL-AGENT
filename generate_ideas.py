import os
import requests
from datetime import datetime

def generate_idea():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    prompt = """Erstelle eine neue Content-Idee für einen Social-Media-Agenten.
Themen: Motorrad, Reisen, Lifestyle, Technik, KI, MotoGP.
Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige.
Stil: locker, per Du, wenige Emojis, kurze Captions.
Liefere die Idee im Format:
Titel: ...
Plattform: Instagram/TikTok/Facebook/Reel/Story
Thema: ...
Hook: ...
Kurze Beschreibung: ..."""

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + api_key
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception as e:
        return f"FEHLER bei API-Anfrage: {e}"

def save_idea(idea):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n\n## Idee vom {timestamp}\n{idea}\n"
    try:
        with open("content/GENERATED_IDEAS.md", "a", encoding="utf-8") as f:
            f.write(entry)
        print("Idee gespeichert.")
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")

if __name__ == "__main__":
    idea = generate_idea()
    save_idea(idea)
