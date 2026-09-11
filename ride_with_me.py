import os
import re
import time
import requests
from datetime import datetime

# Liste der Modelle, die nacheinander getestet werden
MODEL_LIST = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
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

def analyze_ride_with_me():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    prompt = """Analysiere öffentlich verfügbare Informationen zu der Motorrad-App "Ride With Me" (von ndhbr).
Offizielle Website: https://ridewithme.app/
Offizieller Google Play Store Eintrag: https://play.google.com/store/apps/details?id=de.ndhbr.RideWithMe

Die App bietet laut Beschreibung unter anderem: Rides, Feed, Chat, Umgebung, GPS-Aufzeichnung, Fahrtenbuch, GPX-Export, Garage, Statistiken, SOS-Funktion.

WICHTIG:
- Nutze nur öffentlich zugängliche Informationen (App-Beschreibung, offizielle Website, öffentliches Feedback).
- Erfinde keine Bewertungen oder Nutzerdaten.
- Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.

Erstelle daraus:

1. Zusammenfassung der App-Funktionen
2. Mögliche Nutzerbedürfnisse (basierend auf typischen Biker-Anforderungen)
3. Mögliche Feature-Ideen / Verbesserungsvorschläge
4. Social-Media-Ideen passend zu diesen Themen (für Instagram, Facebook, TikTok)
   - Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige
   - Stil: locker, per Du, wenige Emojis, kurze Captions

Formatiere die Antwort exakt so:

## App-Zusammenfassung
...

## Mögliche Nutzerbedürfnisse
...

## Feature-Ideen
...

## Social-Media-Ideen
...
"""

    return try_generate(api_key, prompt)

def save_ride_with_me_analysis(content):
    os.makedirs("ride-with-me", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n\n# Ride With Me Analyse vom {timestamp}\n{content}\n"

    # In Feature-Ideen Datei speichern (enthält auch Social-Media-Ideen)
    with open("ride-with-me/FEATURE_IDEAS.md", "a", encoding="utf-8") as f:
        f.write(entry)

    # Zusätzlich eine kurze Zusammenfassung in USER_FEEDBACK.md
    feedback_summary = "\n\n## Automatische Analyse\n" + content + "\n"
    with open("ride-with-me/USER_FEEDBACK.md", "a", encoding="utf-8") as f:
        f.write(feedback_summary)

    print("Ride With Me Analyse gespeichert.")

if __name__ == "__main__":
    content = analyze_ride_with_me()
    save_ride_with_me_analysis(content)
