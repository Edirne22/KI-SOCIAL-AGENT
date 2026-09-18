# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

Stand: 2026-09-18 Nacht

## ✅ Heute erledigt (gemergt)

### Telegram-Stack
- P0 – Exit-2-Crash behoben
- P1 – Queue atomar (ein Update pro Lauf)
- P2 – Concurrency entkoppelt
- Parser-Robustheit (fehlende Posts blockieren nicht mehr)
- active_batch_id-Fix (PR #17)
- Workflow-Persistenz (`git add -A`)
- End-to-End-Test MotoGP → Instagram + Facebook erfolgreich

### Doku & Werkzeuge
- P3 – Gemini-Inventur (`docs/GEMINI_INVENTORY.md`)
- P4 – V8.6-Promotionsplan (`docs/V8.6_PROMOTION_PLAN.md`)
- Race-Calendar-Pipeline V4 (6 Fixes + 3 Review-Korrekturen)
- `AGENTS.md` (Jules-Regeln + i-have-adhd)
- `docs/PROJEKT_UEBERGABE.md`

### Multi-Modell-Router (Kern-Erfolg)
- `llm_router.py` + `config/llm_providers.json` live
- 5 Anbieter mit Auto-Fallback: Groq, Google, OpenRouter, NVIDIA, Cloudflare
- Cooldown bei 429, Retry-After-Beachtung
- Skip-Logik bei fehlendem Key
- Config-Validierung, max_tokens=2000
- **`follow_analyzer.py` auf Router umgestellt**
- **Isolierter Test-Workflow `llm-router-test.yml`**
- **Alle 3 Router-Tests grün** (default/reasoning/fallback)

### Secrets in GitHub
- `GROQ_API_KEY` ✅
- `GEMINI_API_KEY` ✅ (vorher schon)
- `OPENROUTER_API_KEY` ✅
- `NVIDIA_API_KEY` ✅ (Ablauf 18.03.2027)
- `CLOUDFLARE_API_TOKEN` ✅
- `CLOUDFLARE_ACCOUNT_ID` ✅

## 🔄 Läuft gerade (Jules)

- Deal-Hunter + Inspiration-Orchestrator auf Router umstellen

## ⏳ Offen / wartet

| Aufgabe | Status |
|---|---|
| Deal-Hunter + Inspiration auf Router | läuft in Jules |
| Workflow-Env für deal-hunter.yml + inspiration-agent.yml | mit Auftrag |
| Weekly-Plan, Ride-With-Me, Generate-Ideas auf Router | danach |
| Search-Provider auf Router | später |
| Racing-Pipeline auf Router (Agnes bleibt Bilder) | später |
| **Serie-Filter** (Formel-1 → kein Bike-Block) | offen |
| **Agnes-Story strenger** (erfundene Namen verhindern) | offen |
| Cloudflare-Bildgenerierung (FLUX + Leonardo) | Auftrag fertig |
| Publisher-Workflow `git add -A` (Insta + FB) | klein |
| VPS einrichten (Ubuntu 24.04) | nach Router-Migration |
| SearXNG auf VPS | nach VPS |
| OmniRoute auf VPS | nach VPS |
| Remotion + KI-Video (LTX, Wan, Hunyuan) | nach OmniRoute |
| Kinocut als Video-Editor | nach Video-Setup |
| V8.6 Promotion Debug → main | Plan liegt vor |

## 🎯 Vision

Autonome Content-Fabrik: Agenten erstellen aus einem Prompt selbstständig Videos, Bilder und Texte. OmniRoute bündelt alle KI-Anbieter. Remotion rendert Videos. KI-Video-Modelle liefern Rohmaterial. Kinocut schneidet. Agent gibt Prompt → fertiger Reel.

## 🧰 Router-Architektur (live)

| Task-Typ | Reihenfolge |
|---|---|
| `fast_chat` | Groq → Google → NVIDIA |
| `reasoning` | **OpenRouter** → Google → NVIDIA |
| `coding` | OpenRouter → NVIDIA → Groq |
| `long_context` | NVIDIA → OpenRouter → Google |
| `default` | Groq → Google → OpenRouter → NVIDIA → Cloudflare |

### Bekannte tote Modelle (nicht verwenden)
- `deepseek/deepseek-r1:free` (nicht mehr kostenlos)
- `deepseek-ai/deepseek-v4-pro` (EOL 07.08.2026)
- `deepseek-ai/deepseek-v4-flash` (EOL 07.08.2026)
- `gemini-2.5-flash` (nur für Bestandsnutzer)

## 🧰 Gemerkte Tools

- **awesome-llm-apps** – Inspirationsquelle für Agenten/RAG
- **OpenResearch** – parallele Recherche-Agenten
- **i-have-adhd** – Coding-Agent-Regeln (in `AGENTS.md`)

## ⚠️ Kritische Regeln

- Jules: max 3 Sessions, max 15 Credits/Tag
- Debug-Branch `debug/motogp-pipeline-output`: nicht anfassen
- Kein Auto-Merge, kein Auto-Publish
- Secrets nur notieren, nie committen
- NVIDIA-Key läuft am 18.03.2027 ab – rechtzeitig erneuern

## 📎 Links

- Repo: https://github.com/Edirne22/KI-SOCIAL-AGENT
- Actions: https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- Handbuch: docs/HANDBUCH.md
- Gemini-Inventur: docs/GEMINI_INVENTORY.md
- V8.6-Plan: docs/V8.6_PROMOTION_PLAN.md
- Agenten-Regeln: AGENTS.md
- Router-Test: Actions → LLM Router Test

## 🚀 Nächste Schritte (morgen)

1. Deal-Hunter + Inspiration PR mergen + testen
2. Weekly/Ride/Generate-Ideas auf Router
3. Search-Provider auf Router
4. Serie-Filter + Agnes-Regeln strenger
5. Cloudflare-Bilder + Publisher-Fix

## 📝 Hinweis für neue Chats

Wenn du in einem neuen Chat mit der KI startest, poste den Inhalt dieser Datei. Dann ist der Assistent sofort auf Stand.
