import os
import re
import time
import base64
from pathlib import Path
import requests

from asset_paths import get_carousel_dir, get_image_path, get_video_path, slugify

AGNES_BASE = "https://apihub.agnes-ai.com/v1"
PEXELS_API = "https://api.pexels.com/v1/search"

# === Einstellungen ===
# Wenn True: Pexels wird als automatischer Fallback genutzt
# Wenn False: Bei Agnes-Ausfall wird KEIN Bild gesetzt (Bülent entscheidet manuell)
PEXELS_FALLBACK = False

# Wenn True: Videos werden nur erzeugt, wenn im Block "Video: auto" steht
VIDEO_ON_REQUEST_ONLY = True

# ------------------------------------------

NEGATIVE_PROMPT = (
    " IMPORTANT: Modern MotoGP prototype racing motorcycle with full fairing, "
    "sportbike design, aerodynamic winglets, racing slicks. "
    "NO Harley Davidson, NO cruiser, NO chopper, NO touring bike, NO American flag, "
    "NO cowboy style, NO vintage motorcycle, NO chrome. "
    "European racing style, ultra realistic professional motorsport photography."
)

RACING_KEYWORDS = [
    "toprak", "razgatlioglu", "deniz", "öncü", "oncu", "bahattin",
    "sofuoglu", "kenan", "zayn", "motogp", "moto gp", "sprint",
    "podium", "rennen", "race day", "startaufstellung", "rennfahrer",
]

RACING_PROMPTS = {
    "toprak": "Cinematic action photo of a modern MotoGP racing motorcycle in sharp cornering lean, Yamaha blue and black racing livery with number 07, aerodynamic winglets, race track at golden hour, packed grandstands, professional motorsport photography, ultra realistic",
    "razgatlioglu": "Cinematic action photo of a modern MotoGP racing motorcycle in sharp cornering lean, Yamaha racing colors with number 07, aerodynamic winglets, professional motorsport photography, ultra realistic",
    "deniz": "Professional photo of a modern Moto2 racing motorcycle on track, dynamic cornering, dark blue and white racing livery, aerodynamic fairing, motorsport photography, ultra realistic",
    "öncü": "Professional photo of a modern racing motorcycle on track, action shot, blue and white racing livery, aerodynamic fairing, ultra realistic motorsport photography",
    "oncu": "Professional photo of a modern racing motorcycle on track, action shot, blue and white racing livery, aerodynamic fairing, ultra realistic motorsport photography",
    "bahattin": "Professional photo of a modern Superbike racing motorcycle on track, dynamic action, sportbike with full fairing, racing slicks, ultra realistic",
    "sofuoglu": "Professional photo of a modern racing motorcycle on track, dynamic action, sportbike with full fairing, ultra realistic motorsport photography",
    "kenan": "Cinematic portrait of a racing world champion standing beside a modern racing motorcycle, sunset lighting, professional motorsport photo",
    "zayn": "A young talented go-kart driver racing on a karting track, small racing kart, professional karting photography, ultra realistic",
    "motogp": "Start grid of a MotoGP race, multiple modern prototype racing motorcycles lined up, full fairing sportbikes with aerodynamic winglets, packed grandstands, dramatic lighting, professional sports photography, ultra realistic",
    "moto gp": "Start grid of a MotoGP race, multiple modern prototype racing motorcycles lined up, full fairing sportbikes with aerodynamic winglets, packed grandstands, dramatic lighting, professional sports photography, ultra realistic",
    "sprint": "MotoGP sprint race action, motorcycle riders battling for position, modern prototype racing bikes, dynamic speed blur, professional motorsport photography",
    "podium": "Podium celebration at a MotoGP race, champagne spray, three riders on the podium, modern racing suits, dramatic lighting, professional sports photography",
    "rennen": "Professional motorsport action shot, modern racing motorcycle on track, dynamic cornering, full fairing sportbike, cinematic lighting",
    "race day": "Professional motorsport action shot, modern racing motorcycle on track, dynamic cornering, full fairing sportbike, cinematic lighting",
    "startaufstellung": "MotoGP starting grid with multiple modern racing motorcycles, full fairing sportbikes with winglets, race track view, professional sports photography",
    "rennfahrer": "Professional photo of a motorcycle racer in action on track, modern full fairing racing bike, ultra realistic motorsport photography",
    "_default": "Professional motorsport photography of a modern racing motorcycle with full fairing on a scenic race track, dynamic action shot, cinematic lighting, ultra realistic",
}

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

def get_agnes_headers():
    key = os.environ.get("AGNES_API_KEY")
    if not key:
        raise RuntimeError("AGNES_API_KEY fehlt.")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def is_racing_content(text):
    text_lower = text.lower()
    for kw in ["harley", "cruiser", "chopper"]:
        if kw in text_lower:
            return False
    for kw in RACING_KEYWORDS:
        if kw in text_lower:
            return True
    return False

def get_racing_prompt(text):
    text_lower = text.lower()
    base = RACING_PROMPTS["_default"]
    for kw, prompt in RACING_PROMPTS.items():
        if kw == "_default":
            continue
        if kw in text_lower:
            base = prompt
            break
    return base + NEGATIVE_PROMPT

def get_pexels_query(text):
    text_lower = text.lower()
    for keyword, query in PEXELS_KEYWORDS.items():
        if keyword in text_lower:
            return query
    return "motorcycle biker"

def agnes_generate_image(prompt):
    """Erzeugt ein Bild via Agnes AI. Gibt Bytes zurück oder None."""
    url = f"{AGNES_BASE}/images/generations"
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1
    }
    try:
        r = requests.post(url, headers=get_agnes_headers(), json=payload, timeout=120)
        print(f"Agnes Bild: Status {r.status_code}")
        if r.status_code != 200:
            print(f"Fehler: {r.text[:300]}")
            return None
        data = r.json()
        item = data.get("data", [{}])[0]
        if "url" in item:
            img = requests.get(item["url"], timeout=60)
            return img.content
        if "b64_json" in item:
            return base64.b64decode(item["b64_json"])
    except Exception as e:
        print(f"Agnes Bild Exception: {e}")
    return None

def agnes_generate_video(prompt, max_wait=300):
    """Erzeugt ein Video via Agnes AI. Gibt Bytes zurück oder None."""
    url = f"{AGNES_BASE}/videos"
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": prompt,
        "duration": 5,
        "size": "720x1280"
    }
    try:
        r = requests.post(url, headers=get_agnes_headers(), json=payload, timeout=60)
        print(f"Agnes Video-Start: Status {r.status_code}")
        if r.status_code not in (200, 201, 202):
            print(f"Fehler: {r.text[:300]}")
            return None

        data = r.json()
        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            print("Keine Task-ID.")
            return None

        status_url = f"{AGNES_BASE}/videos/{task_id}"
        for _ in range(max_wait // 5):
            time.sleep(5)
            s = requests.get(status_url, headers=get_agnes_headers(), timeout=30)
            if s.status_code != 200:
                continue
            st = s.json()
            status = st.get("status")
            if status in ("completed", "succeeded", "success"):
                video_url = st.get("url") or (st.get("data") or {}).get("url")
                if video_url:
                    vid = requests.get(video_url, timeout=120)
                    return vid.content
                return None
            if status in ("failed", "error"):
                return None
        print("Video-Timeout.")
    except Exception as e:
        print(f"Agnes Video Exception: {e}")
    return None

def pexels_search(query):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    r = requests.get(PEXELS_API, headers={"Authorization": key},
                     params={"query": query, "per_page": 5, "orientation": "landscape", "size": "large"},
                     timeout=30)
    if r.status_code != 200:
        return None
    photos = r.json().get("photos", [])
    if not photos:
        return None
    return photos[0]["src"]["large2x"]

def download_bytes(url):
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        return None
    return r.content

def save_bytes(data, filename):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(data)
    return True

def insert_image_reference(block, filename):
    """Fügt die Bildzeile vor einer vorhandenen Video-Zeile ein."""
    if re.search(r"(?m)^Video:\s*", block):
        return re.sub(r"(?m)^(Video:\s*)", f"Bild: {filename}\n\\1", block, count=1)
    return block.rstrip() + f"\nBild: {filename}\n"


def replace_auto_video_reference(block, filename):
    """Ersetzt ausschließlich die Anforderung Video: auto durch den Dateinamen."""
    return re.sub(
        r"(?im)^Video:\s*auto\s*$",
        f"Video: {filename}",
        block,
        count=1,
    )


def wants_video(body):
    return bool(re.search(r"Video:\s*auto", body, re.IGNORECASE))



def process_carousel_block(content):
    """Erzeugt für Karussell-Entwürfe mit Bilder: auto drei zusammenpassende Bilder."""
    pattern = r"(## Instagram Karussell\s*\n(.*?)(?=\n## |\Z))"
    for match in re.finditer(pattern, content, re.DOTALL):
        block, body = match.group(1), match.group(2)
        if "[GEPOSTET" in block or not re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", body):
            if "[GEPOSTET" not in block:
                print("Instagram-Karussell-Entwurf übersprungen (nicht freigegeben).")
            continue
        if not re.search(r"(?mi)^Bilder:\s*auto\s*$", body):
            continue

        text_match = re.search(r"(?ms)^Text:\s*(.*?)(?=^Bilder:|\Z)", body)
        topic = text_match.group(1).strip() if text_match else "Motorrad und Reise"
        carousel_dir = get_carousel_dir(slugify(topic))
        variants = (
            ("Hauptmotiv", "dynamic main subject, clear story, cinematic motorcycle photography"),
            ("Detail", "close-up detail of motorcycle, equipment or road texture, cinematic photography"),
            ("Emotion", "authentic rider or community lifestyle moment, warm and realistic photography"),
        )
        filenames = []
        for number, (label, direction) in enumerate(variants, start=1):
            filename = carousel_dir / f"slide-{number}.jpg"
            prompt = (
                f"Vertical 4:5 social media carousel image. Theme: {topic[:220]}. "
                f"Slide {number}: {label}. {direction}. No text or watermark."
            )
            print(f"Agnes Karussell-Bild {number}/3: {prompt[:100]}...")
            image_bytes = agnes_generate_image(prompt)
            if not image_bytes:
                print("Karussell-Generierung fehlgeschlagen – Bilder: auto bleibt unverändert.")
                return content
            save_bytes(image_bytes, filename)
            filenames.append(filename.as_posix())

        references = "Bilder:\n" + "\n".join(f"- {filename}" for filename in filenames)
        updated = re.sub(r"(?mi)^Bilder:\s*auto\s*$", references, block, count=1)
        print("Agnes-Karussell vollständig gespeichert: " + ", ".join(filenames))
        return content.replace(block, updated, 1)
    return content


def process_block(content, platform_header, want_video_check=True):
    pattern = rf"({platform_header}\s*\n(.*?)(?=\n## |\Z))"
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(1)
        body = match.group(2)

        if "[GEPOSTET" in block or "Karussell" in block.splitlines()[0]:
            continue

        has_image = bool(re.search(r"Bild:\s*\S+", body))
        has_video = bool(re.search(r"Video:\s*\S+", body))
        video_requested = wants_video(body)
        if (has_image or has_video) and not video_requested:
            continue

        text_match = re.search(r"Text:\s*(.+?)(?=\nBild:|\nVideo:|\Z)", body, re.DOTALL)
        text = text_match.group(1).strip() if text_match else ""
        image_filename = get_image_path(slugify(text), 1)
        video_filename = get_video_path(slugify(text))
        updated_block = block

        # === 1) BILD via Agnes (nur wenn im Block noch keines vorhanden ist) ===
        if not has_image and not has_video:
            if is_racing_content(text):
                prompt = get_racing_prompt(text)
            else:
                prompt = f"Realistic motorcycle photograph related to: {text[:200]}. Professional photography, ultra realistic, cinematic lighting."

            print(f"Agnes Bild-Prompt: {prompt[:100]}...")
            img_bytes = agnes_generate_image(prompt)

            if img_bytes:
                save_bytes(img_bytes, image_filename)
                updated_block = insert_image_reference(updated_block, image_filename.as_posix())
                print(f"Agnes-Bild gespeichert: {image_filename}")
            else:
                print("Agnes-Bild fehlgeschlagen.")
                if PEXELS_FALLBACK:
                    query = get_pexels_query(text)
                    url = pexels_search(query)
                    if url:
                        data = download_bytes(url)
                        if data:
                            save_bytes(data, image_filename)
                            updated_block = insert_image_reference(updated_block, image_filename)
                            print(f"Pexels-Fallback gespeichert: {image_filename}")
                else:
                    print("→ KEIN Fallback aktiv. Bitte manuell ein Bild einfügen.")

        # === 2) VIDEO (nur bei exakt Video: auto) ===
        if video_requested:
            video_prompt = (
                f"Cinematic vertical 9:16 shot: {text[:200]}. "
                "5 seconds, ultra realistic, composed for Instagram Stories and Reels."
            )
            print(f"Agnes Video-Prompt: {video_prompt[:100]}...")
            vid_bytes = agnes_generate_video(video_prompt)
            if vid_bytes:
                save_bytes(vid_bytes, video_filename)
                updated_block = replace_auto_video_reference(updated_block, video_filename.as_posix())
                print(f"Agnes-Video gespeichert: {video_filename}")
            else:
                print("Agnes-Video fehlgeschlagen – Video: auto bleibt für einen späteren Versuch stehen.")

        if updated_block != block:
            return content.replace(block, updated_block, 1)
        return content

    return content

if __name__ == "__main__":
    if not os.environ.get("AGNES_API_KEY"):
        print("Fehler: AGNES_API_KEY fehlt.")
        exit(1)

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Karussell zuerst, dann Reel-, Instagram- und Story-Logik.
    new_content = process_carousel_block(content)
    if new_content == content:
        new_content = process_block(content, "## Instagram Reel")
    if new_content == content:
        new_content = process_block(content, "## Instagram")
    if new_content == content:
        new_content = process_block(content, "## Story")

    if new_content != content:
        with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("PUBLISHED.md aktualisiert.")
    else:
        print("Keine offenen Blöcke ohne Bild gefunden.")
