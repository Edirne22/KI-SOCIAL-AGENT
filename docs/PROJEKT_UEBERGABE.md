# 📋 PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT – 17.09.2026 Nacht

## ✅ Heute erledigt (nach Abend-Übergabe)

### Telegram-Router-Fix (PR gemergt auf main)
Branch: `fix/telegram-router-fixes` → gemergt in `main`
Commit auf main: `8e0d547baaee33905dd841ed4806f56b17c2eb57`

| Fix | Datei | Status |
|---|---|---|
| FIX 1 – Komma-Auswahl robuster | `motogp_telegram_receive_v85.py` | ✅ gemergt, **noch nicht bestätigt getestet** |
| FIX 2 – Case-Insensitive | `telegram_router.py` + `telegram_receive.py` | ✅ war schon drin |
| FIX 3 – Freundlicher Fallback | `telegram_router.py` | ✅ gemergt, **im Test bestätigt** |
| FIX 4 – load_session robust | `telegram_receive.py` | ✅ gemergt, **im Test bestätigt** |

### Remotion
Video wurde gerendert und gefunden. ✅

### Was funktioniert (im Live-Test bestätigt)
- Fallback-Nachricht bei unbekanntem Kommando kommt an:
  „Danke, ich kann deine Nachricht keinem Kommando zuordnen…"
- `load_session()`-Crash ist abgefangen (`RuntimeError: … nicht drei lesbare Beiträge`)

---

## ⚠️ NEUE Probleme heute erkannt

### 1. Race-Calendar-Update-Workflow ist rot
- Workflow: `race-calendar-update.yml`
- Ursache: `scripts/update_race_calendar.py` verwendet weiterhin Gemini → alle Modelle (3.8, 3.7, 3.6, 3.5) geben **HTTP 429**
- Der JSON-Umbau betraf nur den **Lese-Pfad** (`race/race_calendar.py`), **nicht** das Update-Skript
- Kein offener PR vorhanden
- **Sofort-Schutz:** Workflow in Actions deaktivieren (bis Fix steht)
- **Fix-Optionen:**
  - A) Update-Skript ohne KI (manuelle JSON-Pflege)
  - B) Agnes als Backend statt Gemini (empfohlen, weil Agnes schon im Stack)
  - C) Nur deaktivieren, JSON manuell

### 2. Architektur-Problem Telegram-Queue
- `telegram_receive.py` ruft `get_updates()` selbst auf und **räumt die gesamte Warteschlange ab**
- Dadurch werden `motogp`-Befehle verschluckt, wenn sie **hinter** allgemeinen Befehlen (`alle`, `1` …) in der Queue liegen
- **Beispiel 17.09. 20:52:** Router sah `alle` → rief `telegram_receive.py` → der holte alle 7 Updates und schickte für jedes die Fallback-Nachricht
- **Fix morgen:** Router übergibt Update als Argumente an `telegram_receive.py` (wie schon bei MotoGP), statt es die Queue selbst abräumen zu lassen. Oder: `telegram_receive.py` darf nur **ein** Update verarbeiten

### 3. Concurrency-Konflikt
- Meldung: „Canceling since a higher priority waiting request for `published-plan-writers` exists"
- `Telegram Receive Approval` wurde abgebrochen, weil ein höher priorisierter Workflow in derselben Concurrency-Gruppe lief
- **Prüfen:** Ob `published-plan-writers` zu grob ist (Publisher + Router sollten nicht in derselben Gruppe sein)

---

## ⏳ Offen / wartet auf morgen

| Punkt | Status |
|---|---|
| FIX 1 – Komma-Auswahl final testen | Test läuft (nur `motogp 2, 4` senden, 5 Min warten, Log prüfen) |
| Race-Calendar-Update-Workflow fixen | Auftrag formulieren |
| Telegram-Queue-Architektur | Auftrag formulieren |
| Finanzplaner-Agent | Auftrag fertig, wartet |
| Remotion-PR | prüfen ob gemergt oder noch offen |

---

## 📦 Fertige Jules-Aufträge

### Auftrag 1 – Telegram-Queue-Fix (neu)
- `telegram_receive.py` so umbauen, dass es **nur das übergebene Update** verarbeitet
- `telegram_router.py` übergibt Update-ID + Chat + Text als Argumente (wie bei `motogp_telegram_receive.py`)
- Nur `main`, nur diese zwei Dateien, PR, nicht mergen

### Auftrag 2 – Finanzplaner-Agent (Vollprofi)
- 7 neue Dateien:
  - `memory/FINANCE_PLAN.json`
  - `memory/FINANCE_PLAN.md`
  - `memory/FINANCE_RATES_CACHE.md`
  - `memory/FINANCE_EVENTS.jsonl`
  - `finance_planner.py`
  - `.github/workflows/finance-planner.yml`
  - `agents/15_finance_planner.md`
- Regeln:
  - 20.000 € investierbar bei Chase, Cash 5.000 € separat (NICHT tracken)
  - Max. 2 Banken – lieber 1
  - Festgeld erlaubt
  - Chase: 4 % bis 26.12.2026, danach 2 %
  - FSA: 337 € bei Chase, NICHT löschen, nur belassen
  - Memory-Loop-Anbindung (`FINANCE_EVENTS.jsonl` + `LEARNED_RULES.md`)
  - Web-Scraping: Finanztip, Check24, Verivox, Biallo, tagesgeldvergleich.net, Test.de, Raisin, WeltSparen
  - Keine Anlageberatung, keine Transfers, kein Login

### Auftrag 3 – Race-Calendar-Update-Fix (neu)
- `scripts/update_race_calendar.py` von Gemini auf Agnes umstellen
- `race-calendar-update.yml` prüfen (GEMINI_API_KEY → AGNES_ENDPOINT o. ä.)
- Nur `main`, PR, nicht mergen

---

## ⚠️ Kritische Regeln

- **Jules:** max 3 parallele Sessions, max 15 Credits/Tag
- **Jules-Chat-Regel:** Neuer Auftrag = neuer Chat; Fix an gemergtem PR = neuer Chat
- **Telegram-Kommandos aktuell NUR einzeln:** kein Komma, keine mehrere Nachrichten hintereinander
- **Debug-Branch:** NICHT anfassen – nur Bülent + Codex
- **Workflow-Reihenfolge beachten:** kein `alle`/`1`/`2` vor `motogp`-Befehlen senden (Queue-Problem)

---

## 📎 Wichtige Links
- Repo: https://github.com/Edirne22/KI-SOCIAL-AGENT
- PRs: https://github.com/Edirne22/KI-SOCIAL-AGENT/pulls
- Actions: https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- Handbuch: docs/HANDBUCH.md
- Jules: https://jules.google.com

---

## 🎯 Empfohlene Reihenfolge morgen

1. **FIX 1 final testen** – falls Test noch nicht durch, jetzt nachholen
2. **Telegram-Queue-Fix** als Jules-Auftrag rausschicken (Auftrag 1)
3. **Race-Calendar-Update-Fix** als Jules-Auftrag rausschicken (Auftrag 3)
4. **Finanzplaner-Agent** als Jules-Auftrag rausschicken (Auftrag 2)
5. **Agency-Lauf prüfen** – soll grün sein
6. **Remotion-PR** prüfen (falls noch offen → mergen)
7. **Workflow deaktivieren** (`race-calendar-update.yml`), falls noch nicht gemacht
