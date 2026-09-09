import os
import re
import time
import requests
from datetime import datetime

# Liste der Modelle, die nacheinander getestet werden
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

def try_generate(api_key, prompt):
    """Arbeitet die Modellliste in Schleifen ab, bis ein Modell antwortet."""
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

def generate_weekly_plan():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    prompt = """Erstelle einen kompletten Content-Plan für die kommenden 7 Tage (Montag bis Sonntag).
Themen: Motorrad, Reisen, Lifestyle, Technik, KI, MotoGP.
Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige.
Stil: locker, per Du, wenige Emojis, kurze Captions.
Wichtig: Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.

Plane für jeden Tag:
- Wochentag
- Thema
- Plattform (Instagram/TikTok/Facebook/Reel/Story – variiere sinnvoll)
- Hook
- Kurze Beschreibung (1-2 Sätze)
- Hashtags (für Instagram und TikTok, max. 6 pro Plattform)
- Visuelle Idee (kurz)

Formatiere die Antwort exakt so:

--- TAG 1: Montag ---
Thema: ...
Plattform: ...
Hook: ...
Beschreibung: ...
Hashtags Instagram: ...
Hashtags TikTok: ...
Visuelle Idee: ...

--- TAG 2: Dienstag ---
...

--- TAG 3: Mittwoch ---
...

--- TAG 4: Donnerstag ---
...

--- TAG 5: Freitag ---
...

--- TAG 6: Samstag ---
...

--- TAG 7: Sonntag ---
...
"""

    return try_generate(api_key, prompt)

def save_weekly_plan(content):
    os.makedirs("content", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n\n# Wochenplan vom {timestamp}\n{content}\n"
    with open("content/WOCHENPLAN.md", "a", encoding="utf-8") as f:
        f.write(entry)
    print("Wochenplan gespeichert.")

if __name__ == "__main__":
    content = generate_weekly_plan()
    save_weekly_plan(content)
