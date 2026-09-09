import os
import re
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
Wichtig: Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.
Liefere die Idee im Format:
Titel: ...
Plattform: Instagram/TikTok/Facebook/Reel/Story
Thema: ...
Hook: ...
Kurze Beschreibung: ..."""

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + api_key
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]

        # Entferne alle langen alphanumerischen Strings (mögliche Secrets)
        text_clean = re.sub(r'\b[A-Za-z0-9_\-]{20,}\b', '[ENTFERNT]', text)

        # Zusätzlich typische Schlüssel-Muster maskieren
        text_clean = re.sub(r'AIza[0-9A-Za-z_\-]{35}', '[ENTFERNT]', text_clean)
        text_clean = re.sub(r'AKIA[0-9A-Z]{16}', '[ENTFERNT]', text_clean)
        text_clean = re.sub(r'sk-[A-Za-z0-9]{20,}', '[ENTFERNT]', text_clean)

        return text_clean.strip()
    except Exception as e:
        return f"FEHLER bei API-Anfrage: {e}"

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
