import os
import time
import base64
import requests

from asset_paths import get_test_path

def test_file(name):
    path = get_test_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

AGNES_BASE = "https://apihub.agnes-ai.com/v1"

def get_headers():
    key = os.environ.get("AGNES_API_KEY")
    if not key:
        raise RuntimeError("AGNES_API_KEY fehlt.")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

def test_text():
    """Test: Textgenerierung via Chat-Completions."""
    print("\n=== TEST 1: TEXT ===")
    url = f"{AGNES_BASE}/chat/completions"
    payload = {
        "model": "agnes-2.5-flash",
        "messages": [
            {"role": "user", "content": "Schreibe einen kurzen Instagram-Hook über eine Motorrad-Tour durch die Türkei. Max 15 Wörter, deutsch."}
        ]
    }
    r = requests.post(url, headers=get_headers(), json=payload, timeout=60)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("Antwort:", data["choices"][0]["message"]["content"])
        return True
    print("Fehler:", r.text[:500])
    return False

def test_image():
    """Test: Bildgenerierung."""
    print("\n=== TEST 2: BILD ===")
    url = f"{AGNES_BASE}/images/generations"
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": "Modern MotoGP racing motorcycle in sharp cornering lean, Yamaha blue and black racing livery, aerodynamic winglets, sunset, professional motorsport photography, ultra realistic",
        "size": "1024x1024",
        "n": 1
    }
    r = requests.post(url, headers=get_headers(), json=payload, timeout=120)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        # OpenAI-Format: data[0].url oder data[0].b64_json
        if "data" in data and data["data"]:
            item = data["data"][0]
            if "url" in item:
                print("Bild-URL:", item["url"])
                # Herunterladen und speichern
                img = requests.get(item["url"], timeout=60)
                with open(test_file("test-image.jpg"), "wb") as f:
                    f.write(img.content)
                print("Gespeichert: assets/test/test-image.jpg")
            elif "b64_json" in item:
                with open("test-agnes-image.jpg", "wb") as f:
                    f.write(base64.b64decode(item["b64_json"]))
                print("Gespeichert: assets/test/test-image.jpg (base64)")
        return True
    print("Fehler:", r.text[:500])
    return False

def test_video():
    """Test: Videogenerierung (asynchron)."""
    print("\n=== TEST 3: VIDEO ===")
    url = f"{AGNES_BASE}/videos"
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": "Cinematic shot of a motorcycle riding on a winding mountain road at sunset, ultra realistic",
        "duration": 5,
        "size": "720x1280"
    }
    r = requests.post(url, headers=get_headers(), json=payload, timeout=60)
    print(f"Status: {r.status_code}")
    if r.status_code not in (200, 201, 202):
        print("Fehler beim Start:", r.text[:500])
        return False

    data = r.json()
    print("Antwort:", str(data)[:300])

    task_id = data.get("id") or data.get("task_id") or (data.get("data") or {}).get("id")
    if not task_id:
        print("Keine Task-ID gefunden.")
        return False

    print(f"Task-ID: {task_id}. Warte auf Fertigstellung...")

    # Polling bis zu 5 Minuten
    status_url = f"{AGNES_BASE}/videos/{task_id}"
    for i in range(60):
        time.sleep(5)
        s = requests.get(status_url, headers=get_headers(), timeout=30)
        if s.status_code != 200:
            print(f"Status-Abfrage: {s.status_code}")
            continue
        st = s.json()
        status = st.get("status", "?")
        print(f"  Versuch {i+1}: {status}")
        if status in ("completed", "succeeded", "success"):
            # Video-URL suchen
            video_url = st.get("url") or (st.get("data") or {}).get("url") or (st.get("output") or {}).get("url")
            if video_url:
                print(f"Video-URL: {video_url}")
                vid = requests.get(video_url, timeout=120)
                with open(test_file("test-video-portrait.mp4"), "wb") as f:
                    f.write(vid.content)
                print("Gespeichert: assets/test/test-video-portrait.mp4")
            else:
                print("Status fertig, aber keine URL gefunden:", str(st)[:300])
            return True
        if status in ("failed", "error"):
            print("Fehlgeschlagen:", str(st)[:300])
            return False

    print("Timeout beim Video.")
    return False

if __name__ == "__main__":
    print("Agnes AI Test startet...")
    results = {
        "text": test_text(),
        "image": test_image(),
        "video": test_video()
    }
    print("\n=== ERGEBNIS ===")
    for k, v in results.items():
        print(f"{k}: {'✅' if v else '❌'}")
