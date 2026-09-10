import os
import re
import base64
import requests

GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models"
PEXELS_API = "https://api.pexels.com/v1/search"

# Bildmodelle von Gemini (in dieser Reihenfolge testen)
IMAGE_MODELS = [
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
    "gemini-3-pro-image",
    "nano-banana-pro-preview",
]

# Renn-Prompts: Keyword → Prompt für Gemini
RACING_PROMPTS = {
    "toprak": "Cinematic action photo of a modern MotoGP racing motorcycle in sharp cornering lean, Yamaha blue and black racing livery, number 07 visible, Misano race track at golden hour, Turkish flag waving in background, professional motorsport photography, ultra realistic",
    "razgatlioglu": "Cinematic action photo of a modern MotoGP racing motorcycle leaning into a corner, Yamaha racing colors, number 07, professional motorsport photography, ultra realistic",
    "deniz": "Professional photo of a Moto2 racing motorcycle on track, dynamic cornering, dark blue and white racing livery, motorsport photography, ultra realistic",
    "öncü": "Professional photo of a racing motorcycle on track, action shot, blue and white racing colors, ultra realistic motorsport photography",
    "oncu": "Professional photo of a racing motorcycle on track, action shot, blue and white racing colors, ultra realistic motorsport photography",
    "bahattin": "Professional photo of a Superbike racing motorcycle on track, dynamic action, superbike racing livery, ultra realistic",
    "sofuoglu": "Professional photo of a racing motorcycle on track, dynamic action, ultra realistic motorsport photography",
    "kenan": "Cinematic portrait of a racing world champion standing beside a racing motorcycle, sunset lighting, professional motorsport photo",
    "zayn": "A young talented go-kart driver racing on a karting track, small kart, Turkish flag on the suit, professional karting photography, ultra realistic",
    "motogp": "Start grid of a MotoGP race, multiple modern prototype racing motorcycles lined up, packed grandstands, dramatic lighting, professional sports photography, ultra realistic",
    "moto gp": "Start grid of a MotoGP race, multiple modern prototype racing motorcycles lined up, packed grandstands, dramatic lighting, professional sports photography, ultra realistic",
    "sprint": "MotoGP sprint race action, motorcycle riders battling for position, dynamic speed blur, professional motorsport photography",
    "podium": "Podium celebration at a MotoGP race, champagne spray, three riders on the podium, Turkish flag, dramatic lighting, professional sports photography",
    "rennen": "Professional motorsport action shot, racing motorcycle on track, dynamic cornering, cinematic lighting",
    "race day": "Professional motorsport action shot, racing motorcycle on track, dynamic cornering, cinematic lighting",
    "startaufstellung": "MotoGP starting grid with multiple racing motorcycles, race track view, professional sports photography",
    "rennfahrer": "Professional photo of a motorcycle racer in action on track, ultra realistic motorsport photography",
    "_default": "Professional motorsport photography of a modern racing motorcycle on a scenic race track, dynamic action shot, cinematic lighting, ultra realistic",
}

# Pexels-Suchbegriffe für Nicht-Renn-Content
PEXELS_KEYWORDS = {
    "reise": "motorcycle travel road",
    "roadtrip": "motorcycle road trip",
    "route": "winding mountain road",
    "kurve": "winding road motorcycle",
    "alpen": "alps motorcycle",
    "türkei": "turkey coast road",
    "istanbul": "istanbul sunset",
    "pack": "motorcycle luggage",
    "ölwechsel": "motorcycle engine oil",
    "tüv": "motorcycle inspection",
    "sicherheit": "motorcycle safety helmet",
    "helm": "motorcycle helmet",
    "technik": "motorcycle technology",
    "sonnenuntergang": "motorcycle sunset",
    "biker": "biker motorcycle",
    "community": "motorcycle group riders",
    "tuning": "motorcycle tuning",
    "schrauber": "motorcycle mechanic",
    "werkstatt": "motorcycle garage",
    "garage": "motorcycle garage",
}

# ------------------------------------------

def is_racing_content(text):
    """Erkennt, ob es ein Renn-Thema ist."""
    text_lower = text.lower()
    for kw in RACING_PROMPTS:
        if kw != "_default" and kw in text_lower:
            return True
    return False

def get_racing_prompt(text):
    """Ermittelt den besten Prompt für ein Renn-Thema."""
    text_lower = text.lower()
    for kw, prompt in RACING_PROMPTS.items():
        if kw == "_default":
            continue
        if kw in text_lower:
            return prompt
    return RACING_PROMPTS["_default"]

def get_pexels_query(text):
    """Ermittelt Suchbegriff für Pexels bei Alltags-Content."""
    text_lower = text.lower()
    for keyword, query in PEXELS_KEYWORDS.items():
        if keyword in text_lower:
            return query
    return "motorcycle biker"

def generate_gemini_image(api_key, prompt):
    """Generiert ein Bild über Gemini. Gibt Bild-Bytes zurück oder None."""
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }

    # Jetzt mit ?key= in der URL UND ohne X-goog-api-key Header (Bild-API mag das anders)
    for model in IMAGE_MODELS:
        url = f"{GEMINI_API}/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            r = requests.post(url, json=data, timeout=180)
            print(f"{model}: Status {r.status_code}")
            if r.status_code == 200:
                result = r.json()
                parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        print(f"Gemini-Bild erstellt mit {model}")
                        return base64.b64decode(part["inlineData"]["data"])
                print(f"{model}: Kein Bild in Antwort. Parts: {[list(p.keys()) for p in parts]}")
            else:
                # Erste 300 Zeichen der Antwort ausgeben zur Diagnose
                print(f"{model} Fehler-Antwort: {r.text[:300]}")
        except Exception as e:
            print(f"{model}: Exception – {e}")

    return None

def search_pexels(api_key, query):
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": 5, "orientation": "landscape", "size": "large"}
    r = requests.get(PEXELS_API, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        print(f"Pexels-Fehler: {r.status_code}")
        return None
    photos = r.json().get("photos", [])
    if not photos:
        return None
    return photos[0]["src"]["large2x"]

def download_url(url, filename):
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        return False
    with open(filename, "wb") as f:
        f.write(r.content)
    return True

def save_bytes(data, filename):
    try:
        with open(filename, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Speichern fehlgeschlagen: {e}")
        return False

def update_published(content, block, filename):
    new_block = block.rstrip() + f"\nBild: {filename}\n"
    return content.replace(block, new_block, 1)

def process_block(content, platform_header, gemini_key, pexels_key):
    pattern = rf"({platform_header}\s*\n(.*?)(?=\n## |\Z))"
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(1)
        body = match.group(2)

        if "[GEPOSTET" in block:
            continue
        if re.search(r"Bild:\s*\S+", body):
            print("Block hat schon ein Bild – überspringe.")
            continue

        text_match = re.search(r"Text:\s*(.+?)(?=\nBild:|\Z)", body, re.DOTALL)
        text = text_match.group(1).strip() if text_match else ""

        filename = f"auto-image-{abs(hash(block)) % 10000}.jpg"

        # 1. Renn-Content → Gemini
        if is_racing_content(text):
            prompt = get_racing_prompt(text)
            print(f"Renn-Content erkannt. Gemini-Prompt: {prompt[:80]}...")
            image_bytes = generate_gemini_image(gemini_key, prompt)
            if image_bytes and save_bytes(image_bytes, filename):
                content = update_published(content, block, filename)
                print(f"Gemini-Bild eingefügt: {filename}")
                return content
            print("Gemini fehlgeschlagen – Fallback auf Pexels.")

        # 2. Alltags-Content oder Fallback → Pexels
        query = get_pexels_query(text)
        print(f"Pexels-Suche: '{query}'")
        image_url = search_pexels(pexels_key, query)
        if image_url and download_url(image_url, filename):
            content = update_published(content, block, filename)
            print(f"Pexels-Bild eingefügt: {filename}")
            return content

        print("Kein Bild gefunden.")
        return content

    return content

if __name__ == "__main__":
    gemini_key = os.environ.get("GEMINI_API_KEY")
    pexels_key = os.environ.get("PEXELS_API_KEY")

    if not gemini_key or not pexels_key:
        print("Fehler: Secrets fehlen.")
        exit(1)

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    new_content = process_block(content, "## Instagram", gemini_key, pexels_key)
    if new_content == content:
        new_content = process_block(content, "## Story", gemini_key, pexels_key)

    if new_content != content:
        with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("PUBLISHED.md aktualisiert.")
    else:
        print("Keine Änderungen – kein Block ohne Bild gefunden.")
