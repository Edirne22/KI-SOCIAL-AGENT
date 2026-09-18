# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

Stand: 2026-09-18 Abend

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

## 🔄 Läuft gerade (Jules)

- Race-Calendar-Pipeline V4 (6 Fixes + 3 Review-Korrekturen)

## ⏳ Offen / wartet

| Aufgabe | Status |
|---|---|
| Race-Calendar PR prüfen + mergen | wartet auf Jules |
| Race-Calendar-Workflow testen | nach Merge |
| Multi-Modell-Router (Groq, Google, OpenRouter, NVIDIA, Cloudflare) | Auftrag fertig, wartet |
| Follow-Analyzer auf Router | nach Router |
| Inspiration-Orchestrator auf Router | nach Router |
| Weekly-Plan, Ride-With-Me, Generate-Ideas auf Router | nach Router |
| Search-Provider auf Router | nach Router |
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

## ⚠️ Kritische Regeln

- Jules: max 3 Sessions, max 15 Credits/Tag
- Debug-Branch `debug/motogp-pipeline-output`: nicht anfassen
- Kein Auto-Merge, kein Auto-Publish
- Secrets nur notieren, nie committen

## 📎 Links

- Repo: https://github.com/Edirne22/KI-SOCIAL-AGENT
- Actions: https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- Handbuch: docs/HANDBUCH.md
- Gemini-Inventur: docs/GEMINI_INVENTORY.md
- V8.6-Plan: docs/V8.6_PROMOTION_PLAN.md
- Agenten-Regeln: AGENTS.md

## 🚀 Nächste Schritte

1. Race-Calendar-PR prüfen + mergen
2. Multi-Modell-Router rausschicken
3. Follow-Analyzer + Inspiration migrieren
4. Cloudflare-Bilder + Publisher-Fix
5. VPS + SearXNG + OmniRoute
6. Video-Pipeline (Remotion + KI-Modelle)

## 📝 Hinweis für neue Chats

Wenn du in einem neuen Chat mit der KI startest, poste den Inhalt dieser Datei. Dann ist der Assistent sofort auf Stand.
