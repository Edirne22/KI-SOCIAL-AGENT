# 💡 IDEA POOL – KI-SOCIAL-AGENT

**Zweck:** Sammlung von Ideen, Aufgaben und Features. Kein Zwang – Auswahl nach Lust, Zeit und Priorität.

**Regel:** Der Pool darf wachsen. Er ist ein Werkzeugkasten, keine Bürde.

**Letzte Aktualisierung:** 2026-09-30

---

## 🔴 HEUTE / DIESE WOCHE – AKTIV

### Content Factory / Media – P1 (Stand 30.09.2026)

**LIVE bestätigt:**
- [x] Factory Blocks 1–9 auf main.
- [x] Cloudflare R2 privates Medienlager: Upload → Download → SHA-256 PASS.
- [x] ImageRouter → Factory Adapter → R2 LIVE.
- [x] Agnes Video → Factory Adapter → R2 LIVE (Run 36706431947).

**Jetzt:**
- [ ] OpenChatCut im Cloudflare Container als Beta-Werkbank PoC testen.
- [ ] 720×1280/7s, 1080×1920/15s und 1080×1920/30s benchmarken.
- [ ] Caption + Audio + Remotion/FFmpeg Export + R2 + SHA-256 + ffprobe prüfen.
- [ ] OpenChatCutAdapter erst nach echtem Staffellauf von SIMULATED auf LIVE setzen.
- [ ] Danach SupoClip echte API/Auth integrieren und LIVE abnehmen.
- [ ] Gesamtweg: Source → SupoClip → OpenChatCut → FFmpeg → R2 → Golden Tablet.
- [ ] Sicherer Bild-/Video-Preview für Bülent, ohne R2 öffentlich zu schalten.

**Später:**
- [ ] R2-Belegung/Alter/Medientypen statistisch erfassen; daraus 30/60/90-Tage-Temp-Lifecycle ableiten.
- [ ] Final freigegebene/veröffentlichte Medien und bewusst archivierte Originale niemals per Temp-Cleanup löschen.
- [ ] Cloudflare-Benchmarks später 1:1 gegen x86-VPS messen.

### Historische Racing-/Engagement-Punkte

Die früher hier gelisteten PR-#94-/24.09.-Aktivpunkte sind als aktuelle Aufgaben überholt. Racing-/Engagement-Historie bleibt in `docs/PROJEKT_UEBERGABE_2_ENGAGEMENT.md`, `docs/PROJEKT_UEBERGABE_3_RACING.md` und `docs/PROJEKT_UEBERGABE_4_RUNTIME.md`. Aktuelle Arbeit wird über `MASTER-SNAPSHOT.md` und den neuesten Factory-Snapshot gesteuert.

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


---

## 📊 Instagram Feedback Loop / Composio-Radar – Fund 30.09.2026

**Quelle:** Guide „Claude an dein Instagram anschliessen“, Dennis Bayo, Stand 06.08.2026.

### JETZT / vorhandene Architektur nutzen
- [ ] Bestehenden IG-Engagement-Agenten als führende Lösung behalten: Kommentare klassifizieren (Frage/Lob/Kritik/Spam), `reply_draft` erzeugen, kein Autosenden ohne Human Approval.
- [ ] Bei späteren Analytics bereits einplanen, dass Performance-Daten regelmäßig in eigener Persistence archiviert werden; Instagram/Meta nicht als Langzeit-Memory behandeln.
- [ ] Block 1 **nicht** durch Composio/Analytics erweitern.

### SPÄTER – PerformanceLearning
- [ ] `InstagramInsightsAdapter` als austauschbare Leseschicht für eigene Account-/Post-/Reel-Insights.
- [ ] `PerformanceLearningAgent`: Views/Reichweite/Saves/Shares/Kommentare sowie verfügbare Watch-/Retention-Signale auswerten.
- [ ] Hook-Analyse: erfolgreiche Einstiege gegen schwache Einstiege vergleichen.
- [ ] Wochenreport: 7 Tage vs. vorherige 7 Tage; nur relevante Veränderungen und belastbare Muster.
- [ ] `EditorialMemory`: Performance-Hypothesen mit Zeitraum, Stichprobe und Evidenz speichern; keine vorschnellen Regeln aus wenigen Posts.
- [ ] Feedback Loop: Produktion → Human Approval → Publisher → Plattformdaten → Learning → Candidate Skill Revision.

### PoC / Tool-Battle
- [ ] **Composio** als möglicher Instagram-/Meta-Adapter prüfen, nicht als System of Record.
- [ ] Gegen bestehenden direkten Meta-/Graph-API-Zugriff vergleichen: verfügbare Insights, Auth/Scopes, Stabilität, Kosten/Limits, Datenschutz, Retry, Webhooks, Vendor Lock-in.
- [ ] Read-only Zugriff bevorzugen, wenn für Analytics ausreichend.
- [ ] Drittanbieter darf weder Human Authority noch Publisher-Approval-State besitzen.

### Verbindung zur Prompt-/Skill-Registry
- [ ] Performance darf freigegebene Skills/Prompts **nicht selbst überschreiben**.
- [ ] Learning erzeugt nur Candidate Revision + Begründung/Evidenz.
- [ ] Candidate → Regression → Red-Team → Positive Control → Freigabe → neue gepinnte Skill-Version.
- [ ] Produktionsjob speichert verwendete Skill-Version, damit Ergebnisse reproduzierbar bleiben.

### ZUKUNFT / nicht jetzt bauen
- [ ] Plattformübergreifender LearningAgent für Instagram/Facebook/TikTok/YouTube.
- [ ] Format-/Hook-/Längen-/Themenvergleich pro Plattform.
- [ ] Langfristig kontrollierte Experimente/A-B-Hypothesen, ohne Fakten-QM oder Bülent-Stil durch kurzfristige Engagement-Signale auszuhöhlen.

## Agent-Reach / Platform Discovery Adapter – geprüft 2026-09-30
- Architektur-Kandidat für Block-3/9-Discovery, nicht eigener Fakten- oder Autonomie-Layer.
- Pattern: Health-Checker/Router für austauschbare Plattform-Backends; eigentliche Abfragen über Upstream-Tools.
- Priorität: YouTube-Suche, Metadaten und Untertitel via yt-dlp; zusätzlich X, Reddit, GitHub, RSS/Web je nach verfügbarem Backend.
- Alle Funde laufen weiterhin durch Block 4 Research + Facts. Kein Discovery-Output darf VERIFIED-Status, Human Authority oder Publish-Rechte erzeugen.
- Kein harter Runtime-Lock auf Agent-Reach. Backends bleiben einzeln austauschbar; doctor/health/fallback-Konzept übernehmen.
- Vor produktiver Installation aktives kanonisches Upstream-Repo, Version/Lizenz, Server-/Cookie-Anforderungen und Plattformbedingungen erneut prüfen.

