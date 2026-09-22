## 🔴 HEUTE – 22.09.2026 Abend

### Vor dem Reel (5–10 Min)
- **Prio 1:** `public-apis` klonen → `D:\SnapShot-Agenten\refs\public-apis`
# 💡 IDEA POOL – KI-SOCIAL-AGENT

**Zweck:** Sammlung von Ideen, Aufgaben und Features. Kein Zwang – Auswahl nach Lust, Zeit und Priorität.

**Regel:** Der Pool darf wachsen. Er ist ein Werkzeugkasten, keine Bürde.

**Letzte Aktualisierung:** 2026-09-21

---

## 🎬 CONTENT (höchste Priorität wenn aktiv)

- [ ] MotoGP-Reel bauen (Storyboard steht, Material bereit)
- [ ] Bikertreff-Reel bauen (Radevormwald + Biggesee)
- [ ] Hagen-Biker-Treff-Reel
- [ ] M1000R-Realität-Reel (Reifen, Helm, Übungsplatz)
- [ ] Instagram durchforsten → Patterns sammeln
- [ ] TÜRKBiR beobachten → erste Interaktion

## 🐛 BUGS (wenn Zeit ist)

- [ ] Telegram-Komma-Parsing (`motogp 2,3` ohne Leerzeichen)
- [ ] Follow-Analyzer (0/8 Accounts auswertbar)
- [ ] Publisher-Status (READY_FOR_APPROVAL vs FREIGEGEBEN)

## 🛠️ SETUP (wenn Lust)

- [ ] gptcc installieren (Claude Code + ChatGPT Plus)
- [ ] OmniRoute testen (dauerhafte Proxy-Lösung)
- [ ] Expert Agent Memory aufbauen

## 📄 DOKU (wenn leer)

- [ ] `config/MEDIA_TOOLS.md` anlegen
- [ ] Übergabe-Update mit heutigen Erkenntnissen

## 🔮 ZUKUNFT (Ideen für später)

- [ ] Expert Agent Training (yt-analysis-mcp + Gemini)
- [ ] TikTok-Integration (Apify + ClawHub)
- [ ] Approval-Dashboard Stufe 2 (GitHub Pages)
- [ ] Wan 2.5 als Video-Generator testen
- [ ] MiniMax Audio als Voiceover testen
- [ ] SadTalker als Avatar-Generator testen
- [ ] n8n als Workflow-Alternative testen
- [ ] YouMind (youmind.com) für Prompt-Inspiration nutzen
- [ ] PromptCreek (promptcreek.com) für Agent-Skills prüfen
- [ ] Router-Erweiterung (Nemotron Ultra/Super, GLM-5, Gemma)
- [ ] Memory-Embedding (nemotron-3-embed-1b)
- [ ] Safety-Check (nemotron-3-content-safety)
- [ ] **Pattern 15 nutzen:** „15 Fragen an KI vor Motorrad-Kauf" als Karussell
  - Perfekt für Biker-Zielgruppe
  - Türkisch + Deutsch möglich
  - Sehr hohes Save-Potenzial
    - [ ] **Kinocut testen** (nächste Woche) – „Guardrailed" Video-MCP
  - Installation: `pip install kinocut`
  - Als MCP-Server registrieren
  - Chance: robuster als claudeclip
- [ ] **CutAI testen** (nächste Woche) – Agent Mode Video-Editor
- [ ] **Kaestral reaktivieren** mit größerem Modell (Kimi K3, DeepSeek V4)
- [ ] **yt-analysis-mcp** für Expert Agent – YouTube-Tutorials analysieren
- [ ] **n8n auf VPS** – Workflow-Automatisierung

## 🟢 NACH VPS

- [ ] VPS einrichten (Ubuntu 24.04)
- [ ] SearXNG installieren
- [ ] OmniRoute auf VPS
- [ ] `speech_router.py` (Nemotron ASR + Magpie TTS)
- [ ] `video_router.py` (Cosmos3 Nano)
- [ ] Remotion + Video-Pipeline autonom

## 🟣 STRATEGISCH

- [ ] V8.6 Promotion Debug → main
- [ ] Debug-Workflow-Split auflösen
- [ ] OpenRouter 10 $ aufladen
- [ ] Autonome Content-Fabrik

---

## ✅ ERLEDIGT (Archiv)

### 21.09.2026
- ✅ Weather-Fix live (11-Uhr-Vorhersage)
- ✅ Instagram Zwei

## 🧠 Claude-Code-Skills – Merkliste

**Quelle:** https://ozgurakanay.com/kutuphane/
**Stand:** 22.09.2026

### 🥇 Sofort relevant (diese Woche)

1. **Planning with Files** (Othman Adi)
   - Zweck: Nachtläufe überleben Session-Abbrüche
   - Repo: github.com/OthmanAdi/planning-with-files (URL prüfen)
   - Install: `npx skills add OthmanAdi/planning-with-files`

2. **Türkçe Yazı Yazma** (Özgür Bulut Akanay)
   - Zweck: KI-Geruch aus türkischen Texten entfernen
   - Repo: (URL aus Kütüphane-Seite holen)
   - Install: `npx skills add <autor>/turkce-yazi-yazma`

3. **Marketing Skills** (Corey Haines)
   - Zweck: Marketing-Agents (SEO, Ad-Copy, Strategie)
   - Repo: (URL aus Kütüphane-Seite holen)
   - Install: `npx skills add <autor>/marketing-skills`

### 🥈 Bald relevant

- **Stop Slop** (Hardik Pandya) – KI-Floskeln aus EN-Texten
- **Context Engineering** (Murat Can Koylan) – Token-Verbrauch senken
- **Anthropic Skills** (offiziell) – Word/Excel/PDF
- **Superpowers** (Jesse Vincent) – strukturierte Workflows

### 🟢 Nach VPS

- **Remotion Skills** – Video aus Prompt
- **Trail of Bits Skills** – Security-Audit
- **Awesome Claude Skills** (Composio) – Meta-Liste

### ❌ Nicht relevant

- UI UX Pro Max, Impeccable (Web-UI)
- Vercel Agent Skills (Next.js)
- Supabase Agent Skills (DB)
- Playwright Skill (Browser-Tests)

### 📌 Wichtige Erkenntnis

Skills **können NICHT über Jules installiert werden** – sie sind 
lokale CLI-Installationen (`npx skills add ...`).

- **Weg A:** Lokal installieren (schnell, funktioniert)
- **Weg B:** Skill-Repos in eigenes Repo einchecken (via Jules, für Team)
- **Weg C:** Zentrales Skill-Repo (nach VPS)

### 🚦 Zeitplan

- **Heute Abend:** Reel fertig (KEINE Skills)
- **Diese Woche:** Planning with Files + Türkçe Yazı lokal installieren
- **Nächste Woche:** Marketing Skills + Stop Slop
- **Nach VPS:** Remotion Skills, Trail of Bits
