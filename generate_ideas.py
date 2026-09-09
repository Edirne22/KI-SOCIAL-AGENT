import os
import re
import requests
from datetime import datetime

# Liste möglicher Modelle – wird der Reihe nach getestet, bis eines klappt
MODEL_LIST = [
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-pro-latest",
    "gemini-1.5-flash",
]

def try_generate_with_models(api_key, prompt):
    """Probiert verschiedene Modelle nacheinander, bis eines antwortet."""
    for model in MODEL_LIST:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": api_key
        }
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                text_clean = re.sub(r'\b[A-Za-z0-9_\-]{20,}\b', '[ENTFERNT]', text)
                return text_clean.strip()
            else:
                print(f"Modell {model}: Status {response.status_code} – versuche nächstes...")
        except Exception as e:
            print(f"Modell {model}: Fehler – {e}")
    return "FEHLER: Kein verfügbares Modell gefunden. Bitte später erneut versuchen."

def generate_content_plan():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    prompt = """Erstelle 3 komplette Content-Ideen für einen Social-Media-Agenten.
Themen: Motorrad, Reisen, Lifestyle, Technik, KI, MotoGP.
Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige.
Stil: locker, per Du, wenige Emojis, kurze Captions.
Wichtig: Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.

Erstelle zu jeder Idee:
- Titel
- Plattform (Instagram/TikTok/Facebook/Reel/Story)
- Thema
- Hook
- Instagram-Caption (kurz, mit Hashtags)
- Facebook-Post (etwas ausführlicher, aber auf den Punkt)
- TikTok-Skript (Hook + 3-4 Szenen + Call-to-Action)

Formatiere die Antwort exakt so:

--- BEITRAG 1 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...

Instagram-Caption:
...

Facebook-Post:
...

TikTok-Skript:
...

--- BEITRAG 2 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...

Instagram-Caption:
...

Facebook-Post:
...

TikTok-Skript:
...

--- BEITRAG 3 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...

Instagram-Caption:
...

Facebook-Post:
...

TikTok-Skript:
...
"""

    return try_generate_with_models(api_key, prompt)

def save_content_plan(content):
    os.makedirs("content", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n\n## Automatisch generierte Beiträge vom {timestamp}\n{content}\n"
    with open("content/CONTENT_PLAN.md", "a", encoding="utf-8") as f:
        f.write(entry)
    print("Content-Plan gespeichert.")

if __name__ == "__main__":
    content = generate_content_plan()
    save_content_plan(content)
