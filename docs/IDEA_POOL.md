# 💡 IDEA POOL – KI-SOCIAL-AGENT

**Zweck:** Sammlung von Ideen, Aufgaben und Features. Kein Zwang – Auswahl nach Lust, Zeit und Priorität.

**Regel:** Der Pool darf wachsen. Er ist ein Werkzeugkasten, keine Bürde.

**Letzte Aktualisierung:** 2026-09-29

---

## 🔴 HEUTE / DIESE WOCHE – AKTIV

### Racing-Pipeline (Stand 24.09.2026)

**Offene Bugs:**
- [ ] **Community-Fallback feuert zu aggressiv** – bei vorhandenen Racing-News aber 0 QM-PASS statt fail-closed
- [ ] **Fallback-Kennzeichnung** – „Herkunft: Aktuell" statt „COMMUNITY-FALLBACK" in write_session() + telegram_preview()

**Wartet auf Test:**
- [ ] **PR #94 mergen** → Live-Test mit `force_new_run=true`
- [ ] **Live-Test MotoGP-Content-Agent** – Erwartung: 5 echte MotoGP-Posts
- [ ] **Log prüfen:** `force_new_run resolved=true`, `RACING-QM PASS`, `turkish_rider=True`

**Gerade gemergt (24.09.):**
- [x] PR #78 – Signatur-Bug Strukturvariation
- [x] PR #79 – Rate-Limit-Hardening (Cooldown + Fallback)
- [x] PR #83 – Preflight-Selftests
- [x] PR #85 – JSON-Fehler model_router.json
- [x] PR #88 – Test-Uhr Retry-After
- [x] PR #89 – NVIDIA-Modell + Structure-QM
- [x] PR #90 – force_new_run Checkbox-Übergabe
- [x] PR #94 – Moto4 + Turkish-Rider-Flag

### Instagram Engagement (Stand 24.09.2026)

**Wartet auf Live-Test:**
- [ ] Erstes echtes `IG-XXXXXXXX`-Ticket abwarten
- [ ] `info` → `memory` → dann `antwort` ODER `ändern`

**Offen:**
- [ ] **reply_draft-Lücke** – KI-generierte Antwortvorschläge integrieren (fehlt aktuell in `instagram_engagement.ingest()`)

### Facebook (Stand 24.09.2026)

**Pausiert:**
- [ ] Facebook-Token-Problem: `pages_read_engagement` fehlt
- [ ] Graph API Explorer → `/me/accounts` → Page-Token isolieren → Secret updaten → reaktivieren

---

## 🎬 CONTENT (höchste Priorität wenn aktiv)

- [x] **MotoGP-Reel** – fertig + gepostet (22.09.2026)
- [x] **MotoGP-Karussell** (12 Slides) – fertig + gepostet (22.09.2026)
- [x] **BMW-App-Karussell** – fertig + gepostet (23.09.2026)
- [ ] Bikertreff-Reel bauen (Radevormwald + Biggesee) – Storyboard steht
- [ ] Hagen-Biker-Treff-Reel
- [ ] M1000R-Realität-Reel (Reifen, Helm, Übungsplatz)
- [ ] Instagram durchforsten → Patterns sammeln
- [ ] TÜRKBiR beobachten → erste Interaktion
- [ ] **Calimoto/Biker-App-Karussell** – weitere App-Vorstellungen

---

## 🧠 PRIO 1 – MULTI-KI CROSS-CHECK (Arbeitsweise)

**Ziel:** Kein manuelles Copy-Paste mehr zwischen Chat und Claude Code. Mehrere KIs einbeziehen, deren Antworten vergleichen, bestes Ergebnis destillieren.

**Warum jetzt (Anfangsphase):** Je früher mehrere Perspektiven im Boot sind, desto weniger blinde Flecken im Fundament.

### Kandidaten (zu testen)

**Ebene 1 – Text-Bridge (erst mal simpel)**
- `claudelink-bridge` + Chrome-Extension → Browser-Text direkt an Claude Code
- `ai-relay` → flexibler, mehrere CLIs anbindbar

**Ebene 2 – Clipboard-Workflow**
- `clipboard-ai-mcp` → strukturiertes Hin-und-Her via Clipboard

**Ebene 3 – Multi-Modell-Council (Ziel-Vision)**
- `llm-council-no-api` → `/council`-Befehl: Gemini + GPT, Claude urteilt
- `cross-review` → MCP-Server für Cross-Review
- `codeagora` / `Triumvirate` / `llm-panel` → Multi-LLM-Review

### Test-Reihenfolge
1. `claudelink-bridge`
2. `llm-council-no-api`
3. `cross-review`

### Zeitpunkt
Erste Session nach Racing-Pipeline-Stabilisierung.

### Erfolgskriterium
- [ ] Text aus Browser → Claude Code ohne manuelles Kopieren
- [ ] Mindestens 2 KIs liefern unabhängige Antwort
- [ ] Erste echte Entscheidung durch Cross-Check verbessert

---

## 🧠 KI-AGENT-REPOS – FUNDGRUBE (NEU 24.09.2026)

**Quelle:** @anklrtal Instagram-Serie „7 GitHub repos built for AI agents"

| Repo | Was | Relevanz |
|---|---|---|
| **`browser-use/browser-use`** | Browser-Automation für KI-Agenten | 🟡 **Nur externe Sites** (MotoGP.com, Bikertreff-Recherche) – ⚠️ **NICHT für Instagram/Facebook** (Meta-ToS, Account-Sperre-Risiko) |
| **`yenanjing/awesome-harness-engineering`** | Production-Agent-Patterns (Memory, Skills, Security, Evals, Orchestration) | 🔥 **Referenz-Lektüre** |
| **`Threesided-Studios/Agent-Memory`** | Persistentes Memory über Sessions | 🟡 **Inspiration** für Agent 14 |
| **`volcengine/OpenViking`** | Memory + Knowledge + Skills in einer DB | 🟢 **Ziel-Vision** nach VPS |
| **`cathrynlavery/diagram-design`** | Architektur-Diagramme | 🟢 Nice-to-have |
| `K-Dense-AI/scientific-agent-skills` | 160+ Research-Skills | ❌ nicht relevant |
| `liptonj-eng/anthropic-cybersecurity-skills` | Cybersecurity | ❌ nicht relevant |

### Nächste Schritte
- [ ] `awesome-harness-engineering` durchlesen
- [ ] `browser-use` lokal testen (nicht produktiv)
- [ ] `OpenViking` nach VPS prüfen

---

## 🐛 BUGS

- [x] Telegram-Komma-Parsing (`motogp 2,3`) – gefixt 22.09.
- [x] Telegram `/alle` mit Slash – gefixt 22.09.
- [x] Batch-Status-Mismatch – gefixt 22.09.
- [ ] Follow-Analyzer (0/8 Accounts auswertbar)
- [ ] Publisher-Status (`READY_FOR_APPROVAL` vs `FREIGEGEBEN`)
- [ ] Community-Fallback feuert zu aggressiv (siehe HEUTE)
- [ ] Fallback-Posts nicht gekennzeichnet

---

## 🛠️ SETUP

- [x] OmniRoute läuft (Port 20128) – getestet 22.09.
- [x] FFmpeg-Skript für Reels – läuft
- [x] Kinocut installiert (Python 3.14, `kino doctor` grün)
- [x] Skills: `turkish-native`, `planning-with-files` installiert
- [ ] gptcc installieren ❌ (nicht nutzbar – ChatGPT Plus inkompatibel)
- [ ] Expert Agent Memory aufbauen

---

## 📄 DOKU

- [x] `config/MEDIA_TOOLS.md` – offen (nicht angelegt?)
- [x] `config/HUMAN_WRITING_PROTOCOL.md` – existiert (V1.0)
- [x] `config/PATTERN_LIBRARY.md` – 17 Patterns (Stand 23.09.)
- [x] `docs/FREE_TOOLS.md` – angelegt 23.09.
- [x] `docs/API_REFERENZ.md` – erweitert 23.09.
- [x] `docs/APPROVAL/` – Stufe 2 umgesetzt 22.09.
- [x] `docs/ENGAGEMENT_AGENTS.md` – angelegt 24.09.
- [x] Übergabe-Update mit aktuellen Erkenntnissen – 24.09. Abend

---

## 🔮 ZUKUNFT (Ideen für später)

### Content-Patterns
- [ ] **Pattern 18**: „Content → DM → Conversion" (aus @hfnhq)
- [ ] **Pattern 19**: „Sicher vs Riskant" (Meta-API-Doku-Stil)
- [ ] Ziel: 20 Patterns bis Ende Oktober (aktuell 17)

### Instagram DM-Automation (nach VPS)
**Referenz:** @hfnhq Karussell „Instagram'ı Claude'a bağla"
**Blocker:** 24-Std-Regel braucht Echtzeit → VPS

**Ausbaustufen:**
1. Kommentar-Trigger → DM (z. B. „📍 Bergisches" → Routen-DM)
2. DM-Assistent (FAQs automatisch beantworten)
3. Content-Analytics (welcher Reel bringt Follower?)
4. Lead-Magnet (z. B. „LINK" → DM mit Link)

**Wichtig:** Nur offizielle Meta API, Business/Creator Account + OAuth, keine Drittanbieter-Bots, 24-Std-Fenster respektieren.

### Weitere Engagement-Quellen
- [ ] Erwähnungen tracken (`/mentions` – braucht Webhooks/VPS)
- [ ] Story-Replies (separater Test nötig)
- [ ] Tagged-Media-Agent (Endpoint läuft, Nutzen gering)

### Tools testen
- [ ] Expert Agent Training (yt-analysis-mcp + Gemini)
- [ ] TikTok-Integration (Apify + ClawHub)
- [ ] Wan 2.5 als Video-Generator
- [ ] MiniMax Audio als Voiceover
- [ ] SadTalker als Avatar-Generator
- [ ] n8n als Workflow-Alternative
- [ ] YouMind (youmind.com) für Prompt-Inspiration
- [ ] PromptCreek (promptcreek.com) für Agent-Skills
- [ ] Router-Erweiterung (Nemotron Ultra/Super, GLM-5, Gemma)
- [ ] Memory-Embedding (nemotron-3-embed-1b)
- [ ] Safety-Check (nemotron-3-content-safety)
- [ ] CutAI testen (Agent Mode Video-Editor)
- [ ] Kaestral reaktivieren mit größerem Modell
- [ ] yt-analysis-mcp für Expert Agent
- [ ] n8n auf VPS

### Pattern-Ideen
- [ ] **Pattern 15 nutzen:** „15 Fragen an KI vor Motorrad-Kauf" als Karussell
  - Perfekt für Biker-Zielgruppe
  - Türkisch + Deutsch möglich
  - Sehr hohes Save-Potenzial
### Agenten-Ausbau (aus Screenshots 26.09.2026)

**Referenz:** @mycaptainofficial (Karussell-Serie „Advanced AI Agents")

**Neu und nützlich:**
- [ ] **Viral Hook Generator** – pro Post 3-5 Hook-Varianten generieren
  - Integration in MotoGP-Agent (vor Editor)
  - Priorität: Mittel
  - Voraussetzung: stabiler Content-Flow
- [ ] **Headline A/B Generator** – bei Karussell-Vorschlägen alternative Überschriften
  - Integration in Telegram-Vorschau (mehrere Varianten zur Auswahl)
  - Priorität: Niedrig
  - Voraussetzung: Karussell-Workflow stabil

**Nicht relevant für uns:**
- Marketing Strategy Generator (kein Marketing-Bedarf)
- AI Marketing Consultant (zu allgemein)
- Multi-Agent Campaign Planner (zu komplex)
- Blog SEO Optimiser (kein Blog)
- Trending LinkedIn Post Finder (kein LinkedIn)
- Engineering Learning Stack (nicht unser Feld)

**Schon vorhanden (Screenshot-Bestätigung):**
- ✅ Comment Reply Assistant (Agent 17)
- ✅ Content Quality Reviewer (Chief QM)
- ✅ Multi-Platform Caption Writer (Facebook + Instagram)
- ✅ Daily Industry News Scanner (Racing Scout)
- 
---



## 🧭 TOOL-/OPEN-SOURCE-DISCOVERY – SCREENSHOTS 29.09.2026

### Tool-/Open-Source-Discovery
- [ ] **Avani Codes** – kuratierte Sammlung von 600+ Open-Source-Projekten als Fundgrube für neue Komponenten; nicht selbst Kernbaustein.
- [ ] **Hackathon Tools / Hackathon Projects** – kuratierte Tool-, API-, Template- und Projekt-Sammlungen für gezielte Recherche nach wiederverwendbaren Komponenten.
- [ ] **AlternativeTo** – bei kostenpflichtigen, geschlossenen oder ungeeigneten Tools gezielt nach freien/Open-Source-Alternativen suchen. Als Discovery-Werkzeug nutzen, nicht ungeprüft als technische Quelle übernehmen.

### API-Discovery
- [ ] **Public APIs / API-Verzeichnisse** (im Screenshot als API Layer/Public-APIs-Sammlung) – bei neuen Adaptern zuerst nach offiziellen bzw. belastbaren APIs suchen; Kandidaten anschließend einzeln auf Lizenz, Aktualität, Rate-Limits und Zuverlässigkeit prüfen.

### Hosting-Alternativen für leichte Nebenservices
- [ ] **Render, Railway, Fly.io, Deno Deploy** als mögliche Hosts für kleine APIs, Webhooks, Dashboards oder leichte Background-Services vergleichen.
- [ ] Bei Bedarf zusätzlich **Vercel, Netlify, Cloudflare Pages, GitHub Pages, GitLab Pages, Kinsta, Replit** für Frontend/Static/Development-Sonderfälle prüfen.
- [ ] Diese Dienste sind **kein Ersatz für den geplanten x86-VPS** der rechenintensiven Media-/Video-/Transkriptionspipeline. VPS-Entscheidung separat behandeln.

### Beobachtete Alternative – kein geplanter Kernbaustein
- [ ] **Poe.com** – Multi-Modell-/Bot-Plattform beobachten. Derzeit keine Architekturentscheidung und kein Ersatz für OmniRoute/eigene Modell-Orchestrierung; nur erneut bewerten, falls später ein konkreter Vorteil für Routing, Modellzugang oder Bot-Distribution entsteht.

---

## 📡 SOCIAL-/REALTIME-DISCOVERY – IDEEN 29.09.2026

**Status:** Ideenpool. Erst angehen, wenn die Kernpipeline über längere Zeit stabil autonom läuft.

- [ ] **Instagram:** offizielle/zulässige Schnittstellen bevorzugen; externe Scraper-Dienste (z. B. Apify/RapidAPI) später gegen Kosten, Zuverlässigkeit und Datenschutz prüfen. Keine Abhängigkeit der Kernpipeline von Instagram.
- [ ] **Telegram:** türkische Racing-News-/Fan-Kanäle als zusätzliche Discovery-Quelle evaluieren; Rate-/Flood-Limits berücksichtigen.
- [ ] **X/Twitter:** RSSHub/Nitter-ähnliche Feeds nur als optionale Discovery-Schicht evaluieren, nicht als Primär-Faktenquelle.
- [ ] **Structured Data / Live Timing:** MotoGP-/WorldSBK-Ergebnis- und Timing-Daten auf belastbare strukturierte Feeds/APIs prüfen; experimentelle/undokumentierte Endpunkte nur als Adapter, nicht als Single Point of Failure.
- [ ] **RSS-first:** verfügbare Racing-RSS-Feeds vor HTML-Crawling nutzen, um Last und Fehleranfälligkeit zu reduzieren.
- [ ] **Event-Klassifizierung:** CRITICAL / RESULT / SESSION / CAREER / DISCOVERY / GENERAL als spätere Priorisierungs- und Alert-Schicht.
- [ ] **Racer Registry ausbauen:** Startnummer, aktuelle Serie/Team, Historie, Aliase, Quellenbeleg und `verified_at`; aktuelle Fakten nicht ungeprüft aus Social Posts übernehmen.
- [ ] Nach Stabilisierung **1–2 Wochen Produktionsdaten sammeln** und danach gezielt entscheiden, welche Erweiterungen echten Mehrwert liefern.

---

## 🟢 NACH VPS

- [ ] VPS einrichten (Ubuntu 24.04)
- [ ] SearXNG installieren
- [ ] OmniRoute auf VPS
- [ ] `speech_router.py` (Nemotron ASR + Magpie TTS)
- [ ] `video_router.py` (Cosmos3 Nano)
- [ ] Remotion + Video-Pipeline autonom
- [ ] Meta Webhook live (statt Polling)
- [ ] Instagram DM-Automation (siehe ZUKUNFT)

---

## 🟣 STRATEGISCH

- [ ] V8.6 Promotion Debug → main
- [ ] Debug-Workflow-Split auflösen
- [ ] OpenRouter 10 $ aufladen
- [ ] Autonome Content-Fabrik

---

## ✅ ERLEDIGT (Archiv)

### 24.09.2026
- ✅ PR #78–#94 (7 Racing-Pipeline-Fixes)
- ✅ Instagram Reply Adapter (PR #72)
- ✅ Instagram API Endpoint-Test
- ✅ Test-Workflow Reply Adapter (PR #73)
- ✅ Facebook Engagement pausiert (#71)
- ✅ HUMAN_WRITING_PROTOCOL als Repo-Datei bestätigt
- ✅ `docs/ENGAGEMENT_AGENTS.md` angelegt

### 23.09.2026
- ✅ Pattern 16 + 17 in PATTERN_LIBRARY
- ✅ `docs/FREE_TOOLS.md` angelegt
- ✅ `docs/API_REFERENZ.md` erweitert
- ✅ `docs/IDEA_POOL.md` Skills erweitert
- ✅ Ziffer 12 in Übergabe (Free-Tools aktiv nutzen)
- ✅ BMW-App-Karussell gepostet

### 22.09.2026
- ✅ MotoGP-Reel fertig + gepostet
- ✅ MotoGP-Karussell fertig + gepostet
- ✅ API-Referenz (PR #55)
- ✅ Approval-Dashboard Stufe 2
- ✅ Telegram-Bugs gefixt
- ✅ FFmpeg-Lehre (Ziffer 11 in Übergabe)
- ✅ Skills installiert (turkish-native, planning-with-files)
- ✅ public-apis geklont
- ✅ Repo-Backup erstellt

### 21.09.2026
- ✅ Weather-Fix live (11-Uhr-Vorhersage)
- ✅ Instagram Zwei-Stufen-Freigabe

---

## 🧠 Claude-Code-Skills – Merkliste

**Quelle:** https://ozgurakanay.com/kutuphane/
**Stand:** 24.09.2026

### ✅ Bereits installiert
- **Planning with Files** (Othman Adi) – Nachtläufe überleben Session-Abbrüche
- **Türkçe Yazı Yazma** (`turkish-native`) – KI-Geruch aus türkischen Texten

### 🥇 Sofort relevant (diese Woche)
- **Marketing Skills** (Corey Haines) – Marketing-Agents
  - Install: `npx skills add <autor>/marketing-skills`
- **Stop Slop** (Hardik Pandya) – KI-Floskeln aus EN-Texten

### 🥈 Bald relevant
- **Context Engineering** (Murat Can Koylan) – Token-Verbrauch senken
- **Anthropic Skills** (offiziell) – Word/Excel/PDF
- **Superpowers** (Jesse Vincent) – Claude denkt wie Senior-Software-Engineer
  - Wann: Nach VPS
  - Priorität: Mittel
- **GEO/SEO Claude**
  - Wann: Wenn Content-Strategie steht
  - Priorität: Niedrig

### 🟢 Nach VPS
- **AI Video Toolkit** – vollständiger Video-Produktions-Workflow
  - Priorität: Hoch
- **Remotion Skills** – Video aus Prompt
- **Trail of Bits Skills** – Security-Audit
- **Awesome Claude Skills** (Composio) – Meta-Liste

### ❌ Nicht relevant
- UI UX Pro Max, Impeccable (Web-UI)
- Vercel Agent Skills (Next.js)
- Supabase Agent Skills (DB)
- Playwright Skill (Browser-Tests)

### 📌 Wichtige Erkenntnis
Skills können **NICHT über Jules installiert werden** – sie sind lokale CLI-Installationen (`npx skills add ...`).
- **Speicherort:** `C:\Users\Admin\.agents\skills\`
- **Weg A:** Lokal installieren (schnell)
- **Weg B:** Skill-Repos ins eigene Repo (via Jules)
- **Weg C:** Zentrales Skill-Repo (nach VPS)

### 🚦 Zeitplan
- **Diese Woche:** Marketing Skills + Stop Slop
- **Nach Racing-Stabilisierung:** Multi-KI-Cross-Check
- **Nach VPS:** AI Video Toolkit, Remotion Skills, Trail of Bits

---

**Ende Ideen-Pool – Stand 24.09.2026 Abend**
