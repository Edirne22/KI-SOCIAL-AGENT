# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

**Stand:** 2026-09-20 (Nachmittag)
**Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
**Ziel:** Autonome Content-Fabrik für Bülent (@edirnelibuelent) – 12–24 Monate zur KI-Agentur.

---

## 🏍️ BÜLENTS CONTENT-VISION (dauerhaft)

### Person & Nische
- Bülent, 50, fährt seit 1992 Motorrad
- Maschine: BMW M1000R, Baujahr 2024
- Region: Schwelm (Ruhrgebiet + Sauerland + Bergisches Land)
- Hausstrecke: Radevormwald → Biggesee → Sägewerk
- Handle: **@edirnelibuelent**

### Ziel
Aus der Fabrik raus. Eigene KI-Agentur. Content, der autonom läuft.
Einnahmen: Sponsoren + Agentur-Kunden. Zeitachse: 12–24 Monate.

### Content-Säulen
1. **Strecken-Doku** – konkrete Strecken, Kurven, Bikertreffs
2. **M1000R-Realität** – ehrliche Berichte (Kosten, Wartung, Erfahrung)
3. **Community** – gemeinsame Touren ab Radevormwald
4. **Biker-Alltag** – Generationen-Content, echte Geschichten

### Format
- Reels: 30–60 Sek, Hook in ersten 3 Sek, immer Untertitel
- Echte Fotos/Videos (kein KI-Editorial für Personenfotos)
- 1 Reel/Tag (Monat 1–6), 2–3/Tag (ab Monat 6)

### Schlachtplan
- **Woche 1:** Setup + 2 Reels
- **Monat 1:** 30 Reels, erste Zahlen
- **Monat 6:** 5.000 Follower, erste Kooperationen (100–500 €/Monat)
- **Monat 12:** 20.000 Follower, 2.500–3.500 €/Monat → Kündigung prüfen
- **Monat 24:** 50.000+ Follower, 10.000 €/Monat → Fabrik gekündigt

### Antrieb
Kinder. Für sie da sein. Ihnen ein besseres Leben ermöglichen.

---

## 📱 WHATSAPP-COMMUNITIES (direkter Zielgruppen-Zugang)

### 1. TÜRKBiR (Türkische Biker-Community)
- **Beigetreten:** 20.09.2026
- **Größe:** 36 Gruppen (bundesweit)
- **Status:** Vorstellung in „Welcome & Tanıtım" erfolgt
- **Relevante Gruppen:** BERGISCHES LAND, Buluşmalar, Tur ve buluşma bilgi, Etkinlikler

### 2. BIKE SOCIETY (Deutsche Biker-Community – 3 Regionen)
- **Status:** Seit mehreren Monaten Mitglied
- **United** → Ruhrgebiet + Ennepe-Ruhr-Kreis (13 Gruppen)
- **Hagen** → Hagen (12 Gruppen)
- **im Bergischen** → Bergisches Land (12 Gruppen)
- **Relevante Gruppen:** Ankündigungen, Laberecke, Fahrten & Treffen, Vorstellungsgruppe, Routen & Tourdaten

### 🎯 Nutzen
- Direkter Zugang zur Zielgruppe
- Content-Ideen aus erster Hand
- Bikertreff-Recherche
- Kooperationen

### 🚦 Nächste Schritte
1. TÜRKBiR: 2–3 Tage beobachten → erste Interaktion
2. BIKE SOCIETY: eigene Inhalte später teilen
3. Screenshots von „Fahrten & Treffen"-Posts → Content-Recherche

### ⚠️ Regel
Nicht mit Werbung starten. Erst Community-Mitglied werden, dann Mehrwert liefern.

---

## 🤖 ROUTER-STACK (Phase 1 – komplett)

| Modul | Primär | Fallback | Status |
|---|---|---|---|
| `llm_router.py` | Groq/Google/OpenRouter/NVIDIA/Cloudflare | – | ✅ live |
| `image_router.py` | Pollinations | Cloudflare → Together → NVIDIA → Agnes | ✅ live |
| `vision_router.py` | Llama 3.2 Vision | Kimi K3 | ⚠️ Upgrade geplant |
| `translation_router.py` | Riva 4B (NVIDIA) | llm_router | ✅ live |
| `speech_router.py` | Nemotron ASR + Magpie TTS | – | 🟢 nach VPS |
| `video_router.py` | Cosmos3 Nano | – | 🟢 nach VPS |

### Bild-Router Details
- **Env-Schalter:** `IMAGE_PRIMARY` = `pollinations` (Standard) | `cloudflare` | `together` | `nvidia` | `agnes`
- Cloudflare-Payload: nur `{"prompt": ...}`
- Together: Read-only Mode, nicht nutzbar
- Pollinations: läuft ohne Key zuverlässig
- NVIDIA FLUX: **auf Eis** (Timeout/422)
- Agnes: letzter Fallback, funktioniert

### Vision-Router Details
- `general` → `meta/llama-3.2-11b-vision-instruct` (Fallback: Kimi K3)
  - ⚠️ **Upgrade geplant:** `meta/muse-glimmer-30b` (stärker für Screenshots)
- `ocr` → `nvidia/nemotron-ocr-v2` (liefert `text` + `tables`)
- `omni` → `nvidia/nemotron-3-nano-omni`

### Translation-Router Details
- Primär: `nvidia/riva-translate-4b-instruct-v2`
- Fallback: `llm_router.quick_chat`
- **Wichtig:** Sprach-Namen ausgeschrieben („German", „Turkish")
- Sprachen: DE, TR, EN, FR, ES, IT, NL, PL, RU, AR

---

## 🔑 API-KEYS & SECRETS

| Secret | Status |
|---|---|
| `NVIDIA_API_KEY` | `KI-SOCIAL-AGENT-v2` |
| `CLOUDFLARE_ACCOUNT_ID` | aktiv |
| `CLOUDFLARE_API_TOKEN` | aktiv |
| `TOGETHER_API_KEY` | gesetzt, aber nicht nutzbar |
| `POLLINATIONS_API_KEY` | aktiv |
| `GROQ_API_KEY` | aktiv |
| `OPENROUTER_API_KEY` | aktiv |
| `GEMINI_API_KEY` | aktiv |
| `AGNES_API_KEY` | aktiv |
| `PEXELS_API_KEY` | aktiv |
| `TELEGRAM_BOT_TOKEN` | aktiv |
| `TELEGRAM_CHAT_ID` | aktiv |

### Provider-Status
- ✅ **Pollinations** – läuft, kein Key-Limit
- ✅ **Cloudflare Workers AI** – 10k Neuronen/Tag
- ❌ **Together AI** – nicht nutzbar
- ❌ **NVIDIA FLUX** – auf Eis
- ✅ **NVIDIA Riva 4B** – läuft
- ✅ **NVIDIA Llama Vision** – läuft (Upgrade geplant)
- ✅ **Agnes** – Bild-Fallback
- ✅ **Kimi K3** – Reasoning/Coding
- ⚠️ **DeepSeek v4-flash** – EOL 22.09.2026

### 🔒 Sicherheitsregel
Keine Keys in Chats posten. Bei versehentlichem Posten: sofort rotieren.

---

## 🧪 TEST-WORKFLOWS (alle grün)

| Workflow | Zweck | Letztes Ergebnis |
|---|---|---|
| `test-image-router.yml` | Bild-Generierung | `BYTES: 386374` in 9 Sek |
| `test-vision-router.yml` | Vision-Analyse | `RESULT: {...}` |
| `test-translation-router.yml` | DE↔TR | `Merhaba, nasılsın?` |

---

## 🤖 TELEGRAM VISION-BOT (Bild-Analyse)

**Status:** ✅ live seit 20.09.2026
**Dateien:** `telegram_router.py`, `memory/VISION_LOG.jsonl`

### Funktionen
| Kommando | Wirkung |
|---|---|
| Bild + `/vision` | Bild analysieren |
| Bild + `/ocr` | Text/Tabellen extrahieren |
| Bild + `/omni` | Multimodale Analyse |
| Bild ohne Caption | Standard = general |
| `/help` / `/hilfe` | Kommando-Übersicht |
| `/vision` ohne Bild | Hinweis |

### NEU seit 20.09.: Vision-Log-Speicherung
- Jede Analyse wird in `memory/VISION_LOG.jsonl` geschrieben
- Format: `{timestamp, source, mode, model, result, tables_present, error}`
- Auch Fehlerfälle werden geloggt
- **Zweck:** Basis für automatische Auswertung

### Workflow
```
Screenshot → Telegram (/vision) → Vision-Router → Analyse
                                       ↓
                                VISION_LOG.jsonl
                                       ↓
                          (später: Vision-Summary-Agent)
```

### Nächster Schritt (Auftrag vorbereitet)
- **Vision-Summary-Agent** liest `VISION_LOG.jsonl`, schreibt `VISION_SUMMARY.md`
- **Erster Lauf:** 18.10.2026 (Guard-Clause im Workflow)
- **Danach:** alle 3 Tage um 08:00 UTC

---

## 🎯 PATTERN LIBRARY (Instagram-Content-Bausteine)

**Datei:** `config/PATTERN_LIBRARY.md`
**Angelegt:** 20.09.2026

| # | Pattern | Quelle | Anwendung |
|---|---|---|---|
| 1 | Zahl + Nutzen im Hook | @aiwithshivang | Listen-Reels |
| 2 | Kommentar-Trigger | @aiwithshivang | Reichweite |
| 3 | Selfie mit VIP | Bülent (MotoGP) | Social Proof |
| 4 | Vorher/Nachher | vorgemerkt | Transformation |
| 5 | POV | vorgemerkt | Fahrt-Content |
| 6 | Storytelling mit Ende offen | vorgemerkt | Serie |

**Ziel:** 15–20 Patterns bis Ende Oktober 2026.

---

## 📺 MOTOGP CONTENT PIPELINE (V8.5.5)

### Workflows
| Workflow | Trigger | Zweck |
|---|---|---|
| `motogp-content-agency.yml` | schedule + workflow_dispatch | 5 Tagesvorschläge generieren |
| `motogp-telegram-approval.yml` | **nur workflow_dispatch** | Empfängt MotoGP-Kommandos |
| `telegram-receive.yml` | schedule (~alle 5 Min) | Zentraler Router für Telegram-Updates |
| `motogp-pipeline-diagnose.yml` | workflow_dispatch | Diagnose |
| `motogp-roster-update.yml` | schedule | Fahrer-Roster aktualisieren |

### Wichtige Erkenntnisse (20.09.2026)
- **MotoGP Telegram Approval läuft NICHT automatisch** (kein `schedule`)
  - Der zentrale Router `telegram-receive.yml` übernimmt das Polling
  - Bei Bedarf manuell starten
- **5 → 3 Stories möglich** wenn FRESHNESS DIAG alte/fehlende Stories filtert
  - NULL-TOLERANZ: nur frische Stories werden verwendet
  - Top-20-Fallback füllt Lücken bei manuellem Start
- **FRESHNESS DIAG** filtert nach: fresh / old / missing_date / promo_irrelevant
- **SERIES LOCK** in V8.5.5: immutable series + source-fact whitelist

### Erwartete Telegram-Nachricht
- 🏍️ 5 Tagesvorschläge (MotoGP, Moto2, Moto3, Turkish, Community)
- 🔎 Fakten-QM: NULL-TOLERANZ
- ✍️ Human Writing Protocol + Bülents Bike Life Voice
- Freigabe via `motogp 1–5` / `motogp alle` / `motogp nein`

---

## 🎬 CONTENT-MATERIAL (Bülent)

### 5 Foto-/Video-Ordner auf Laptop

| Ordner | Inhalt | Potenzial |
|---|---|---|
| **MotoGP Assen 2026** | Toprak (Video + Selfies), Jack Miller, Morbidelli, Rins, Ai Ogura, Strecke, Stände | 🔥 **höchstes** |
| **Radevormwald** | Fotos | mittel |
| **BiggeGrill / Biggesee** | Fotos | mittel |
| **Hagen Biker Treff** | Fotos (auch Bike Society Hagen) | mittel |
| **M1000R Übungsplatz** | Kreise, Achten, Hinterreifen, Helm, Straße | hoch |

### Bonus-Material
- BMW-App-Screenshot: Route + Schräglagen (47° rechts / 44° links)
- Calimoto (falls aufgezeichnet)

### 🏆 Top-Material: MotoGP Assen 2026
- 🎥 **Toprak-Video:** bedankt sich auf Türkisch, winkt in Kamera
- 📸 Selfies mit Toprak, Jack Miller, Morbidelli, Rins
- 📸 Ai Ogura (von weitem)
- 📸 Strecke + Stände

**Virales Potenzial:** 3 Zielgruppen gleichzeitig

### 🎯 Reel-Plan
| # | Reel | Status |
|---|---|---|
| 1 | MotoGP Assen – „Toprak bedankt sich" | 🔴 Storyboard fertig |
| 2 | Bikertreff-Runde (Radevormwald + Biggesee) | 🔴 Storyboard fertig |
| 3 | Hagen Biker Treff / Bike Society Hagen | ⏸️ wartet |
| 4 | M1000R-Realität | ⏸️ wartet |
| 5 | BiggeGrill | ⏸️ wartet |

### 🛠️ Video-Tool-Entscheidung
- **CapCut:** ❌ zu groß für Laptop
- **HeyGen:** ✅ kostenlos (3 Videos/Monat, 1 Min, Wasserzeichen)
- **OpenReel:** ✅ Browser (kein Install)
- **Empfehlung:**
  - MotoGP-Reel: manuell (OpenReel)
  - Andere: HeyGen für Rohschnitt

---

## 🖥️ APPROVAL-DASHBOARD (geplant)

**Aktuell:** Freigabe über Telegram.

### Stufe 2 – KURZFRISTIG (1–2 Wochen)
- GitHub Pages, statische HTML
- Datenquelle: `docs/approval/queue.json`
- Freigabe: Button → `workflow_dispatch` → Publisher
- Kosten: 0 €
- URL: `edirne22.github.io/KI-SOCIAL-AGENT/`

### Stufe 3 – NACH VPS
- Streamlit oder Next.js
- Kalender, Analytics, Content-Bibliothek

---

## 📦 CLAWHUB-SKILLS (Social-Media-Automatisierung)

**Empfohlen:**
- **Phy Social Post** → Insta + FB + TikTok
- **Multi-Platform Scheduler**
- **Outfeed** → Bulk-Publishing

**Mit Vorsicht:**
- **Postmoore** → Security-Risiken

---

## 🔴 OFFENE PRIORITÄTEN

### Kurzfristig (diese Woche)
- 🎬 MotoGP-Reel bauen + posten
- 🎬 Bikertreff-Reel (Radevormwald + Biggesee)
- 📸 Instagram durchforsten → Patterns sammeln
- 📱 TÜRKBiR beobachten → erste Interaktion
- 📄 `config/MEDIA_TOOLS.md` anlegen
- 🧠 **Vision-Summary-Agent** (Auftrag vorbereitet, PR offen)
- 🎯 **Vision-Modell-Upgrade** auf `meta/muse-glimmer-30b` (Auftrag vorbereitet)

### Mittelfristig (2 Wochen)
- 🖥️ Approval-Dashboard Stufe 2
- 📦 TikTok-Integration
- 🧠 Vision in Pipeline einbinden
- 🧠 Memory-Embedding → `nvidia/nemotron-3-embed-1b`
- 🛡️ Safety-Check → `nvidia/nemotron-3-content-safety`
- ⚙️ Router-Erweiterung
- 🐛 Debug-Branch-Schutz

### Nach VPS
- 🟢 VPS einrichten
- 🟢 SearXNG, OmniRoute
- 🟢 `speech_router.py`, `video_router.py`
- 🟢 Remotion + Video-Pipeline autonom

### Strategisch
- 🟣 V8.6 Promotion Debug → main
- 🟣 Debug-Workflow-Split auflösen
- 🟣 OpenRouter 10 $ aufladen
- 🟣 Autonome Content-Fabrik

---

## 🔧 TOOL-WORKFLOW (Jules + Codex)

### Jules (Google)
- 15 Sessions/Tag (rollierend 24h), max 3 parallel
- Automatische PRs, GitHub-Integration
- **Neuer Auftrag = neuer Chat**
- **Fix an gemergtem PR = neuer Chat**

### Codex (ChatGPT Plus)
- Nutzungslimit, Reset ~18:41 Uhr
- Kann GitHub-PRs direkt anlegen (GitHub-Verbindung)
- Selbst-enthaltende Aufträge (kein Chat-Gedächtnis)

### Aufteilung
- **Jules:** Größere Tasks
- **Codex:** Fixes, kleine PRs, parallel zu Jules
- **Beide:** Nie dieselbe Datei gleichzeitig bearbeiten

---

## ⚠️ WICHTIGE REGELN

### Verbotene Clubs (nie erwähnen, nie taggen)
- ❌ Osmanen Germania (verboten 2018)
- ❌ Turkos MC (aufgelöst 2018)
- ❌ Black Jackets (kriminell)

### Content-Regeln
- ✅ Immer Türkisch + Deutsch (Zielgruppe)
- ✅ Nur öffentliche Infos
- ✅ Respektvoll & positiv
- ✅ Keine politischen Aussagen
- ✅ Handles nur, wenn öffentlich sichtbar
- ❌ Keine KI-Deepfakes von echten Personen
- ❌ Kein Re-Upload ohne Freigabe

### Branches
- `main` = produktiv
- `debug/motogp-pipeline-output` = nur Bülent + Codex

---

## 📊 AUTONOMIE-STAND

| Stufe | Status |
|---|---|
| 1. Planung | ✅ |
| 2. Recherche | ✅ |
| 3. Media (Bild/Vision/Translation) | ✅ Phase 1 |
| 4. Compose | ⏳ teilweise |
| 5. Approval (Telegram) | ✅ |
| 6. Publishing (Insta + FB) | ✅ |
| 7. Publishing (TikTok) | ❌ geplant |
| 8. Media (Audio/Video) | 🟢 nach VPS |
| 9. Durchgehende Autonomie-Kette | 🔴 in Arbeit |

**Aktuell: ~50 % autonom.**

---

## 📎 QUELLEN & LINKS

- **Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
- **PRs:** https://github.com/Edirne22/KI-SOCIAL-AGENT/pulls
- **Actions:** https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- **NVIDIA Build:** https://build.nvidia.com/models
- **ClawHub:** https://clawhub.ai
- **Handbuch:** `docs/HANDBUCH.md`
- **Bikertreffs:** `config/Bikertreffs.md`
- **Pattern Library:** `config/PATTERN_LIBRARY.md`
- **Jules Docs:** https://jules.google/docs/usage-limits/

---

## 🎯 FÜR NEUE CHATS

**Startprompt für neuen Chat:**
> „Lies `docs/PROJEKT_UEBERGABE.md` im Repo Edirne22/KI-SOCIAL-AGENT (raw: https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/docs/PROJEKT_UEBERGABE.md). Arbeite auf diesem Stand weiter."

**Damit ist der Assistent in 10 Sekunden auf Stand.**

---

## 🧠 ARBEITS-PRINZIPIEN (verbindlich für alle Chats)

### 1. Proaktiv mitdenken
Wenn dem Assistenten auffällt, dass etwas **suboptimal** ist
(schwaches Modell, unnötiger Aufwand, falsche Architektur), soll er
das **sofort ansprechen** – nicht erst auf Nachfrage.

**Konkret:**
- Bei Vergleichen prüfen: Gibt es ein besseres Modell/Tool?
- Bei Fehlern: Ursache benennen, nicht nur fixen
- Bei Entscheidungen: Vor- und Nachteile nennen
- Bei wiederkehrenden Mustern: Vorschlag zur Automatisierung machen

### 2. Nach jedem Meilenstein: Snapshot
Wenn ein größeres Feature fertig ist (Router, Agent, Pipeline):
- Eintrag in `docs/PROJEKT_UEBERGABE.md` ergänzen
- Was wurde gebaut, was läuft, was ist offen
- Verhindert Wissensverlust zwischen Chats

### 3. Bei neuen Chats: Übergabe lesen
Der Assistent MUSS zu Beginn eines neuen Chats die
`PROJEKT_UEBERGABE.md` lesen (Raw-Link) und auf diesem Stand
weiterarbeiten.

### 4. Modelle/Tools immer hinterfragen
Wenn ein Modell oder Tool nicht das gewünschte Ergebnis liefert:
- Prüfen, ob es eine stärkere, kostenlose Alternative gibt
- Wenn ja: sofort vorschlagen (nicht auf Nachfrage warten)
- Mit konkretem Wechsel-Vorschlag + Auswirkung

### 5. Ehrliche Einschätzung > höfliche Zustimmung
Bei Schwächen, Risiken oder Fehlern: klar ansprechen.
Nicht schönreden. Lieber unbequem ehrlich als bequem falsch.
