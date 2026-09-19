## 🏍️ BÜLENTS CONTENT-VISION (dauerhaft)

### Person & Nische
- Bülent, 50, fährt seit 1992 Motorrad
- Maschine: BMW M1000R, Baujahr 2024
- Region: Ruhrgebiet + Sauerland
- Hausstrecke: Radevormwald → Biggesee → Sägewerk
- Handle: @edirnelibuelent

### Ziel
Aus der Fabrik raus. Eigene KI-Agentur. Content, der autonom läuft.
Einnahmen: Sponsoren + Agentur-Kunden.
Zeitachse: 12–24 Monate.

### Content-Säulen
1. **Strecken-Doku** – konkrete Strecken, Kurven, Tracks (Ruhrgebiet)
2. **M1000R-Realität** – ehrliche Berichte (Kosten, Wartung, Erfahrung)
3. **Community** – gemeinsame Touren ab Radevormwald
4. **Biker-Alltag** – Generationen-Content, echte Geschichten

### Format
- Reels: 30–60 Sek, Hook in ersten 3 Sek, immer Untertitel
- Echte Fotos/Videos (kein KI-Editorial für Personenfotos)
- 1 Reel/Tag (Monat 1–6), 2–3/Tag (ab Monat 6)

### Schlachtplan
- **Woche 1:** Setup (Handle, Bio, Profilbild) + 2 Reels
- **Monat 1:** 30 Reels, erste Zahlen
- **Monat 6:** 5.000 Follower, erste Kooperationen (100–500 €/Monat)
- **Monat 12:** 20.000 Follower, 2.500–3.500 €/Monat → Kündigung prüfen
- **Monat 24:** 50.000+ Follower, 10.000 €/Monat → Fabrik gekündigt

### Nächster konkreter Schritt
1. Instagram-Handle prüfen + Bio schreiben
2. Profilbild: Bülent + M1000R
3. Erste Fahrt mit Handy-Video (Radevormwald → Biggesee)
4. Ersten Reel bauen (CapCut, kostenlos)
5. Ersten Reel posten

### KI-Agenten unterstützen später
- MotoGP-Agent → Text für Posts
- NVIDIA Image-Router → Grafiken/Infografiken
- NVIDIA Speech-to-Text → Untertitel automatisch
- NVIDIA TTS → Voiceover
- Remotion + VPS → Video-Pipeline autonom
- OmniRoute → alles gebündelt

### Antrieb
Kinder. Für sie da sein. Ihnen ein besseres Leben ermöglichen.


---

## 🤖 NVIDIA NIM – Merkliste (Einbau-Plan)

### Technische Details
| Aspekt | Wert |
|---|---|
| Text-API | `https://integrate.api.nvidia.com/v1` (OpenAI-kompatibel) |
| Bild-API | `https://ai.api.nvidia.com/v1/genai/<model>` (eigenes Format) |
| Rate-Limit | 40 Requests/Minute |
| Kosten | Kostenlos zum Prototyping |
| Token-Billing | Keins |
| API-Key | `NVIDIA_API_KEY` (Ablauf 18.03.2027) |

### 🔴 Priorität 1 – Sofort einbauen

**Text/Reasoning:**
- `moonshotai/kimi-k3` → in `config/llm_providers.json` nvidia.models (reasoning, coding, long_context)
- Grund: 1M Kontext, Top-Reasoning, Coding, multimodal. Ersetzt `deepseek-v4-flash` (EOL).

**Bildgenerierung → neuer `image_router.py`:**
- Primär: `black-forest-labs/flux.1-schnell` (227K Calls/30d)
- Fallback: `black-forest-labs/flux.1-dev` (303K Calls/30d)
- Schnellste Alternative: `black-forest-labs/flux.2-klein-4b` (338K Calls/30d)
- Letzter Fallback: Agnes (bestehend)

### 🟡 Priorität 2 – Nach image_router.py

**Vision → neuer `vision_router.py`:**
- `meta/llama-3.2-11b-vision-instruct` → Instagram-Bilder analysieren
- `nvidia/nemotron-ocr-v2` → Text aus Bildern (Finanzagent-Tabellen)
- `nvidia/nemotron-3-nano-omni` → Multimodal (Bild+Video+Speech+Text)

**Übersetzung → neuer `translation_router.py`:**
- Riva Translate 1.6b → DE ↔ TR (36 Sprachen)

**Speech → neuer `speech_router.py` (nach VPS):**
- Nemotron ASR Streaming → Untertitel für Reels
- Magpie TTS Multilingual → Voiceover (12 Sprachen)

### 🟢 Priorität 3 – Nach VPS

**Video → neuer `video_router.py`:**
- `nvidia/cosmos3-nano` → Video-Generierung
- `nvidia/cosmos-transfer2.5-2b` → Video-zu-Video
- `nvidia/cosmos3-nano-reasoner` → Video/Bild-Verständnis
- `nvidia/video-super-resolution` → Videos hochskalieren
- `nvidia/relighting` → Beleuchtung anpassen

**Embedding:**
- `nvidia/nemotron-3-embed-1b` → Memory-Suche, RAG (34 Sprachen)

**Safety:**
- `nvidia/nemotron-3-content-safety` → Post-Qualität prüfen

**Router-Erweiterung (mehr Optionen):**
- `nvidia/nemotron-3-ultra-550b` → 1M Kontext, agentic
- `nvidia/nemotron-3-super-120b` → Effizienter MoE
- `nvidia/nemotron-3.5-lightning-30b` → Schnelle Agenten
- `meta/llama-3.3-70b-instruct` → Standard-LLM
- `google/gemma-4-31b-it` → Reasoning/Coding
- `minimaxai/minimax-m3` → Multimodal MoE (ist drin)
- `glm-5.2` → Agentic + Coding

### ❌ Nicht relevant
- ARC / Evo 2 (Biologie)
- Drug Discovery
- Route Optimization (cuOpt)

### 🎯 Geplante Router-Module
| Modul | Primär | Fallback | Status |
|---|---|---|---|
| `llm_router.py` | Groq/OpenRouter/Google/NVIDIA/Cloudflare | – | ✅ fertig |
| `image_router.py` | FLUX.1-schnell | FLUX.1-dev → Agnes | 🔴 offen |
| `vision_router.py` | Llama Vision | Kimi K3 → Nemotron OCR | 🟡 offen |
| `translation_router.py` | Riva Translate | – | 🟡 offen |
| `speech_router.py` | Nemotron ASR + Magpie TTS | – | 🟢 nach VPS |
| `video_router.py` | Cosmos3 Nano | – | 🟢 nach VPS |
