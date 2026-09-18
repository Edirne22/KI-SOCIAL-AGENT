# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

Stand: 2026-09-18 Spätabend

## ✅ Heute erledigt (gemergt)

- P0 – Telegram Exit-2-Crash behoben
- P1 – Telegram-Queue atomar (ein Update pro Lauf)
- P2 – Concurrency entkoppelt (`telegram-receive` eigene Gruppe)
- P3 – Gemini-Inventur (`docs/GEMINI_INVENTORY.md`)
- P4 – V8.6-Promotionsplan (`docs/V8.6_PROMOTION_PLAN.md`)
- Parser-Robustheit (fehlende Posts blockieren nicht mehr)
- active_batch_id-Fix (PR #17)
- Workflow-Persistenz (`git add -A` statt selektiv)
- End-to-End-Test MotoGP → Instagram + Facebook erfolgreich
- Remotion-Video gerendert und gefunden
- Race-Calendar-Pipeline V4 (6 Fixes + 3 Review-Korrekturen)
- `AGENTS.md` angelegt (Jules-Regeln + i-have-adhd)
- `docs/PROJEKT_UEBERGABE.md` aktualisiert
- **5 API-Keys in GitHub Secrets angelegt:**
  - `GROQ_API_KEY`
  - `OPENROUTER_API_KEY`
  - `NVIDIA_API_KEY` (läuft am 18.03.2027 ab!)
  - `CLOUDFLARE_API_TOKEN`
  - `CLOUDFLARE_ACCOUNT_ID`
  - (`GEMINI_API_KEY` war schon da)

## 🔄 Läuft gerade (Jules)

- Multi-Modell-Router + Follow-Analyzer (Auftrag 8/15 verbraucht)

## ⏳ Offen / wartet

| Aufgabe | Status |
|---|---|
| Router-PR prüfen + mergen | wartet auf Jules |
| Follow-Analyzer Test-Lauf | nach Router-Merge |
| **Serie-Filter** (Formel-1 → kein Bike-Block) | offen, ~1 Credit |
| **Agnes-Story strenger** (erfundene Namen verhindern) | offen, ~1 Credit |
| Deal-Hunter auf Router | nach Router-Test |
| Inspiration-Orchestrator auf Router | nach Router-Test |
| Weekly-Plan, Ride-With-Me, Generate-Ideas auf Router | später |
| Search-Provider auf Router | später (braucht Websuche) |
| Cloudflare-Bildgenerierung (FLUX + Leonardo) | Auftrag fertig, wartet |
| Publisher-Workflow `git add -A` (Insta + FB) | klein, wartet |
| VPS einrichten (Ubuntu 24.04) | nach Router |
| SearXNG auf VPS | nach VPS |
| OmniRoute auf VPS | nach VPS |
| Remotion + KI-Video (LTX, Wan, Hunyuan) | nach OmniRoute |
| Kinocut als Video-Editor | nach Video-Setup |
| V8.6 Promotion Debug → main | Plan liegt vor |

## 🎯 Vision

Autonome Content-Fabrik: Agenten erstellen aus einem Prompt selbstständig Videos, Bilder und Texte. OmniRoute bündelt alle KI-Anbieter. Remotion rendert Videos. KI-Video-Modelle liefern Rohmaterial. Kinocut schneidet. Agent gibt Prompt → fertiger Reel.

## 🧰 Gemerkte Tools

- **awesome-llm-apps** – Inspirationsquelle für Agenten/RAG
- **OpenResearch** – parallele Recherche-Agenten
- **i-have-adhd** – Coding-Agent-Regeln (in `AGENTS.md` eingebaut)

## 📊 Router-Architektur (nach Merge)

| Agent | Primär | Fallback-Kette |
|---|---|---|
| Follow-Analyzer | OpenRouter (deepseek-r1) | NVIDIA → Google |
| Deal-Hunter | OpenRouter (deepseek-r1) | NVIDIA → Google |
| Inspiration | OpenRouter (deepseek-r1) | NVIDIA → Google |
| Weekly-Plan | Groq (gpt-oss-120b) | Google → OpenRouter |
| Ride-With-Me | Groq (gpt-oss-120b) | Google → OpenRouter |
| Generate-Ideas | Groq (gpt-oss-120b) | Google → OpenRouter |
| Search-Provider | OpenRouter | NVIDIA → Google |
| Racing-Pipeline | OpenRouter | NVIDIA → Groq |
| Bilder | Agnes / Cloudflare | – |

## ⚠️ Kritische Regeln

- Jules: max 3 Sessions, max 15 Credits/Tag
- Debug-Branch `debug/motogp-pipeline-output`: nicht anfassen
- Kein Auto-Merge, kein Auto-Publish
- Secrets nur notieren, nie committen
- **NVIDIA-Key läuft am 18.03.2027 ab – rechtzeitig erneuern**

## 📎 Links

- Repo: https://github.com/Edirne22/KI-SOCIAL-AGENT
- Actions: https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- Handbuch: docs/HANDBUCH.md
- Gemini-Inventur: docs/GEMINI_INVENTORY.md
- V8.6-Plan: docs/V8.6_PROMOTION_PLAN.md
- Agenten-Regeln: AGENTS.md

## 🚀 Nächste Schritte (morgen)

1. Router-PR prüfen + mergen
2. Follow-Analyzer Test-Lauf
3. Serie-Filter (Formel 1 → kein Bike-Block)
4. Agnes-Story strenger
5. Cloudflare-Bilder + Publisher-Fix

## 📝 Hinweis für neue Chats

Wenn du in einem neuen Chat mit der KI startest, poste den Inhalt dieser Datei. Dann ist der Assistent sofort auf Stand.
