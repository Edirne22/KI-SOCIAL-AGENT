import os
import re
import time
import requests
from datetime import datetime

MODEL_LIST = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-pro-latest"
]

def read_ride_with_me():
    """Liest öffentliche Ride With Me Analysen, falls vorhanden."""
    knowledge = ""
    for path in ["ride-with-me/FEATURE_IDEAS.md", "ride-with-me/USER_FEEDBACK.md"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Nur den letzten Teil verwenden, um den Prompt nicht zu überladen
            knowledge += f"\n\n--- Inhalt aus {path} ---\n{content[-3000:]}"
        except FileNotFoundError:
            pass
    return knowledge

def try_generate(api_key, prompt):
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    max_rounds = 5
    pause_between_models = 10
    pause_between_rounds = 90

    for round_number in range(1, max_rounds + 1):
        print(f"Starte Durchlauf {round_number} von {max_rounds}")
        for model in MODEL_LIST:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                response = requests.post(url, headers=headers, json=data, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    text_clean = re.sub(r'AIza[0-9A-Za-z_\-]{35}', '[ENTFERNT]', text)
                    text_clean = re.sub(r'sk-[A-Za-z0-9]{20,}', '[ENTFERNT]', text_clean)
                    print(f"Erfolg mit Modell: {model}")
                    return text_clean.strip()
                else:
                    print(f"Modell {model}: Status {response.status_code} – probiere nächstes...")
                    time.sleep(pause_between_models)
            except Exception as e:
                print(f"Modell {model}: Fehler – {e}")
                time.sleep(pause_between_models)

        if round_number < max_rounds:
            print(f"Durchlauf {round_number} beendet – warte {pause_between_rounds} Sekunden...")
            time.sleep(pause_between_rounds)

    return "FEHLER: Kein Modell verfügbar nach mehreren Durchläufen. Bitte später erneut versuchen."

def generate_content_plan():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    ride_with_me_knowledge = read_ride_with_me()
    if ride_with_me_knowledge:
        knowledge_part = f"Berücksichtige bei der Ideenfindung auch folgende Informationen aus der Ride With Me Analyse:\n{ride_with_me_knowledge}\n"
    else:
        knowledge_part = ""

    prompt = f"""Erstelle 3 komplette Content-Ideen für einen Social-Media-Agenten.
Themen: Motorrad, Reisen, Lifestyle, Technik, KI, MotoGP.
Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige.
Stil: locker, per Du, wenige Emojis, kurze Captions.
Wichtig: Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.

{knowledge_part}

Erstelle zu jeder Idee:
- Titel
- Plattform (Instagram/TikTok/Facebook/Reel/Story)
- Thema
- Hook
- Instagram-Caption (kurz, mit Hashtags)
- Facebook-Post (etwas ausführlicher, aber auf den Punkt)
- TikTok-Skript (Hook + 3-4 Szenen + Call-to-Action)
- Visuelle Idee (Bildkomposition / Videoidee)
- Hashtag-Vorschläge (für Instagram und TikTok, max. 8 pro Plattform)
- Trend-Bezug (kurzer Hinweis, warum das Thema gerade relevant ist – nutze dein aktuelles Wissen über Trends im Motorrad-, Reise-, Tech- und KI-Bereich)

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

Visuelle Idee:
...

Hashtags Instagram:
#...

Hashtags TikTok:
#...

Trend-Bezug:
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

Visuelle Idee:
...

Hashtags Instagram:
#...

Hashtags TikTok:
#...

Trend-Bezug:
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

Visuelle Idee:
...

Hashtags Instagram:
#...

Hashtags TikTok:
#...

Trend-Bezug:
...
"""

    return try_generate(api_key, prompt)

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
