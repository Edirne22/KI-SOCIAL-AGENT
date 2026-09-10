import os
import re
import requests

PEXELS_API = "https://api.pexels.com/v1/search"

# Suchbegriffe je nach Thema (einfache Keyword-Erkennung)
KEYWORD_MAP = {
    "motogp": "motogp racing",
    "moto gp": "motogp racing",
    "tuning": "motorcycle tuning",
    "schrauber": "motorcycle mechanic",
    "werkstatt": "motorcycle garage",
    "garage": "motorcycle garage",
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
    "ki": "technology artificial intelligence",
    "technik": "motorcycle technology",
    "sonnenuntergang": "motorcycle sunset",
    "biker": "biker motorcycle",
}

def detect_query(text):
    """Sucht passende Pexels-Suchbegriffe anhand des Beitragstexts."""
    text_lower = text.lower()
    for keyword, query in KEYWORD_MAP.items():
        if keyword in text_lower:
            return query
    # Fallback
    return "motorcycle biker"

def search_pexels(api_key, query):
    """Sucht bei Pexels nach einem passenden Foto."""
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": 5,
        "orientation": "landscape",
        "size": "large"
    }
    r = requests.get(PEXELS_API, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        print(f"Pexels-Fehler: {r.status_code} {r.text}")
        return None
    data = r.json()
    photos = data.get("photos", [])
    if not photos:
        return None
    # Erstes Ergebnis nehmen (Pexels sortiert nach Relevanz)
    return photos[0]["src"]["large2x"]

def download_image(url, filename):
    """Lädt das Bild herunter und speichert es im Repository."""
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        print(f"Download-Fehler: {r.status_code}")
        return False
    with open(filename, "wb") as f:
        f.write(r.content)
    print(f"Bild gespeichert: {filename}")
    return True

def update_published(content, block, filename):
    """Ergänzt die Bild-Zeile im entsprechenden Block."""
    if re.search(r"Bild:\s*\S+", block):
        return content  # Block hat schon ein Bild

    new_block = block.rstrip() + f"\nBild: {filename}\n"
    return content.replace(block, new_block, 1)

def process_block(content, platform_header, api_key):
    """Verarbeitet einen Block (Instagram oder Story), der noch kein Bild hat."""
    pattern = rf"({platform_header}\s*\n(.*?)(?=\n## |\Z))"
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(1)
        body = match.group(2)

        if "[GEPOSTET" in block:
            continue
        if re.search(r"Bild:\s*\S+", body):
            print(f"Block hat schon ein Bild – überspringe.")
            continue

        # Suchbegriff ermitteln
        text_match = re.search(r"Text:\s*(.+?)(?=\nBild:|\Z)", body, re.DOTALL)
        text = text_match.group(1).strip() if text_match else ""
        query = detect_query(text)
        print(f"Suche Pexels-Foto für: '{query}'")

        image_url = search_pexels(api_key, query)
        if not image_url:
            print("Kein Foto gefunden.")
            return content

        # Eindeutiger Dateiname pro Block
        filename = f"auto-image-{abs(hash(block)) % 10000}.jpg"
        if not download_image(image_url, filename):
            return content

        content = update_published(content, block, filename)
        print(f"Bild eingefügt: {filename}")
        return content  # nur ein Block pro Lauf

    return content

if __name__ == "__main__":
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        print("Fehler: PEXELS_API_KEY fehlt.")
        exit(1)

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Zuerst Instagram, dann Story
    new_content = process_block(content, "## Instagram", api_key)
    if new_content == content:
        new_content = process_block(content, "## Story", api_key)

    if new_content != content:
        with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("PUBLISHED.md aktualisiert.")
    else:
        print("Keine Änderungen – kein Block ohne Bild gefunden.")
