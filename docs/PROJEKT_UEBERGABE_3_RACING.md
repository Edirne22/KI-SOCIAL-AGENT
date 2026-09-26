# RACING PIPELINE HARDENING – 26.09.2026

Stand: 2026-09-26 (10:30 UTC)
Repo: Edirne22/KI-SOCIAL-AGENT
Bereich: Motorcycle Racing Agency V8.5.5
Ergänzung zu: docs/PROJEKT_UEBERGABE.md

---

## 1. Ausgangsproblem

Am Morgen des 26.09.2026 fiel auf, dass die Motorcycle Racing Agency trotz vorhandener aktueller Racing-News keine bzw. kaum echte Racing-Beiträge lieferte.

Stattdessen wurden teilweise ausschließlich Community-Fallbacks ausgegeben:
- Knieschleifer aus Überzeugung
- Bike Society United
- Knieschleifer Ruhrpott

Gleichzeitig waren im Workflow-Log aktuelle und relevante Racing-News vorhanden:
- Nicolo Bulega / Iker Lecuona in Cremona
- Brad Binder → BMW / WorldSBK
- MotoGP-Kalender 2027
- Valencia als MotoGP-Saisonfinale 2027
- weitere WorldSBK/WorldSSP-News

Problem: Der Research-Agent fand die News, aber zwischen Research und finaler Telegram-Ausgabe gingen viele davon verloren.

---

## 2. Erste Fehlerursache: Persistenz-Race-Condition

Beim ersten Recovery-Run wurden tatsächlich 5 Racing-Beiträge erzeugt:

`final=5`
`status=READY_FOR_APPROVAL`

Der Lauf scheiterte anschließend beim Persistieren. Während des langen Racing-Runs hatte sich `main` durch einen anderen Merge verändert. Beim anschließenden `git pull --rebase origin main` entstanden Konflikte in mehreren `memory/*`-Dateien.

Noch problematischer: Telegram konnte die Vorschläge bereits erhalten, obwohl der neue READY_FOR_APPROVAL-State noch nicht dauerhaft gespeichert worden war.

Der Benutzer erhielt 5 Telegram-Vorschläge. Die Antwort `motogp 1, 5` wurde korrekt geparst, aber anschließend abgelehnt: „Batch ist nicht im Status READY_FOR_APPROVAL.“ Telegram-Batch und persistierter State waren nicht synchron.

---

## 3. PR #139 – Persistenz und Telegram transaktionssicher gemacht

Branch: `fix/racing-persistence-race-condition`

Merge-Commit: `2a3615d58a4242e19fe79a9485b5cde822811da2`

Neues Script: `scripts/persist_racing_state.sh`

Eigenschaften:
- Racing-State wird zuerst lokal committed.
- `origin/main` wird neu gefetcht.
- konfliktrobuster Rebase.
- bis zu 3 Persistenzversuche.
- Push erst nach erfolgreichem Rebase.
- Arbeitsbaum wird geprüft.

Telegram wurde transaktionssicher umgebaut:

Racing Agency → Telegram-Outbox → Persistenz → nur bei Erfolg Telegram Flush.

Neue Komponente: `racing_flush_notifications.py`.

Telegram wird damit erst nach erfolgreicher dauerhafter Persistenz verschickt. Regressionstest wurde eingerichtet.

---

## 4. Series-Lock-Preflight-Fehler

Nach #139 wurde ein neuer Realtest gestartet.

Run: `36232814989`

Dieser scheiterte bereits im Preflight:

`AssertionError: locked Moto3 was overwritten by generic MotoGP metadata`

Die Produktionspipeline installiert `racing_v855_hardening.install(agency)`. Der Selftest `racing_v85_selftest.py` tat dies jedoch nicht. Damit testete der Selftest eine andere Runtime-Konfiguration als die Produktion.

---

## 5. PR #140 – Series-Lock-Selftest korrigiert

Branch: `fix/racing-series-lock-regression`

Der Selftest installiert jetzt dieselbe V8.5.5-Hardening-Schicht wie die Produktion.

Zusätzlich wurde `TEST – Racing Series Lock Regression` eingerichtet. Regression erfolgreich. PR #140 wurde anschließend gemergt.

---

## 6. Nächstes Problem: Aktuelle News werden trotzdem ausgesiebt

Nach #140 wurde erneut ein vollständiger Racing-Lauf durchgeführt.

Research fand aktuelle Racing-News, darunter:
- Brad Binder / BMW
- Bulega
- Lecuona
- MotoGP-Kalender 2027
- Valencia
- Alcoba
- weitere Cremona-News

Trotzdem endete ein Lauf teilweise mit `current_q=0`, `fallback_q=0` und Community-Fallbacks.

Daraufhin wurde die gesamte QM-Kette untersucht:
- `racing_semantic_qm.py`
- `racing_v855_hardening.py`
- `motogp_quality_manager.py`
- `chief_quality_manager.py`
- `motogp_content_agency_v2.py`

---

## 7. Semantic-QM war zu hart

### A. Technische Providerfehler

Beispiele aus den Logs:
- `ReadTimeout`
- `JSONDecodeError`
- `coverage_complete must be true`
- fact evidence invalid

Diese technischen Probleme führten dazu, dass ein Kandidat praktisch verloren ging, obwohl kein Faktenfehler festgestellt worden war.

Grundsatz: **TECHNISCHER FEHLER != FAKTENFEHLER.**

### B. Community-/Meinungsfragen

Beispiel: „Wie seht ihr die Lage für Bulega?“

Solche Fragen konnten vom Semantic-QM als `UNSUPPORTED` bewertet werden. Damit konnte eine reine Community-Frage eine ansonsten vollständig belegte Racing-News blockieren.

### C. Dezimalpunkt vs. Dezimalkomma

Quelle: `0.119s`

Deutscher Beitrag: `0,119s`

Die Source-Fact-Whitelist konnte dies als unterschiedliche Zahlen behandeln, obwohl faktisch dieselbe Zahl gemeint war.

---

## 8. PR #141 – Balanced Racing QM

Ziel: QM nicht generell lockern. Harte Fakten bleiben NULL-TOLERANZ, technische Fehler dürfen aber keine verifizierten News vernichten.

Neue Regeln:

**Unsupported FACT:** bleibt HARD FAIL. Erfundenen Fahrerzuordnungen, Zahlen oder Fakten werden weiterhin blockiert.

**OPINION_QUESTION:** Eine echte offene Frage ist kein Faktenclaim. „Wie seht ihr die Lage für Bulega?“ darf einen belegten Artikel nicht mehr blockieren.

**Zahlen:** `0.119` und `0,119` werden semantisch als dieselbe Zahl behandelt. Eine tatsächlich abweichende Zahl bleibt Fehler.

**Semantic Provider Failure:** Wenn Source-Fact-Whitelist PASS und Racing-QM PASS vorliegen, Semantic-QM aber ausschließlich technisch nach Retries scheitert, wird `semantic_qm = DEGRADED-PASS` gesetzt.

Das ist kein Blind-Pass. Nachgelagerte Batch-/Media-/Chief-/Final-Gates bleiben vorgesehen.

Regression: `TEST – Racing QM Balanced Gates` erfolgreich. PR #141 wurde gemergt.

---

## 9. Realtest nach #141

Run: `36234592025`
Job: `108383960191`

Ergebnis:
- `raw=203`
- `fresh=9`
- `current_q=5`
- `fallback_q=1`
- `final=3`

Finaler Mix:
- MotoGP: 1
- WorldSBK: 1
- Community: 1

Telegram lieferte Valencia 2027 Saisonfinale, Lecuona/Bulega Cremona und Bike Society Hagen als Community-Fallback.

Brad Binder, MotoGP-Kalender 2027 und weitere Bulega-News fehlten weiterhin.

---

## 10. Detailanalyse des Runs 36234592025

### Brad Binder

`RACING-QM PASS` für „Bringing Brad on board is a bit strategic“ – Muir breaks down Binder’s appeal to BMW.

Danach Semantic-QM Technical Retry wegen `ReadTimeout`, anschließend `coverage_complete must be true`, schließlich `SEMANTIC-QM DEGRADED PASS`.

Binder war damit nach #141 ausdrücklich nicht faktisch abgelehnt.

### Bulega

„I’m just angry about Friday“ – Bulega explains his two crashes at Cremona.

`RACING-QM PASS`; danach `ReadTimeout` / `JSONDecodeError`; anschließend `SEMANTIC-QM DEGRADED PASS`.

### MotoGP-Kalender 2027

„MotoGP News 2027 MotoGP calendar revealed“

`RACING-QM PASS`; danach technische Semantic-Probleme; anschließend `SEMANTIC-QM DEGRADED PASS`.

### Valencia

„MotoGP confirms Valencia GP as 2027 season finale...“

Ergebnis: `FULL COPY-QM PASS`. Diese Story gelangte in die finale Telegram-Auswahl.

### Lecuona/Bulega

„REPORT: Lecuona quickest on Friday at Cremona, Bulega second but crashes twice“

Ergebnis: `FULL COPY-QM PASS`. Auch diese Story gelangte in Telegram.

---

## 11. Entscheidender Bug nach #141

In `motogp_content_agency_v2.py`, Funktion `finish_item()`, akzeptierte die nachgelagerte Finalisierung weiterhin ausschließlich `semantic_qm == PASS`.

Damit geschah:

Binder → Racing-QM PASS → Semantic DEGRADED-PASS → `finish_item()` → sofort False → kein Media → kein Chief-QM → Kandidat verschwindet.

Dasselbe traf MotoGP-Kalender 2027 und die separate Bulega-Story.

Diese Kandidaten wurden also nicht vom Chief-QM fachlich abgelehnt. Sie erreichten den Chief-QM überhaupt nicht.

---

## 12. PR #142 – DEGRADED-PASS Finalization Fix

Branch: `fix/racing-degraded-pass-finalization`

Neue Logik: `semantic_qm` darf `PASS` oder `DEGRADED-PASS` sein, bei weiterhin erforderlichem `racing_qm == PASS`.

Damit darf ein DEGRADED-PASS weiter zu Media, Chief-QM und Finalprüfung. `semantic_qm == FAIL` bleibt STOP.

Regression: `TEST – Racing Degraded Pass Finalization`
Run: `36235757556`
Ergebnis: SUCCESS.

Explizit getestet:
- DEGRADED-PASS erreicht Media + Chief-QM.
- FAIL erreicht weder Media noch Chief-QM.

PR #142 war mergeable und wurde anschließend gemergt.

---

## 13. Aktueller Status

Nach Merge von #142 wurde die MotoGP Content Agency am 26.09.2026 gegen 10:30 UTC erneut manuell gestartet.

Dieser Lauf ist der aktuelle End-to-End-Realtest.

Besonders zu kontrollieren:
- Brad Binder / BMW
- MotoGP-Kalender 2027
- Bulega
- Lecuona/Bulega
- Valencia
- Anzahl `fresh`
- Anzahl `current_q`
- Anzahl `final`
- finaler Serienmix
- Chief-QM Entscheidungen
- Media-Erstellung
- Persistenz
- Telegram Flush

Ziel: Wenn mindestens 5 aktuelle, belegte und qualifizierte Racing-News vorhanden sind, sollen diese bevorzugt die fünf Telegram-Slots füllen. Community-Fallback darf keine qualifizierte wichtige Racing-News verdrängen.

---

## 14. Architekturprinzip nach den Fixes

Gewünschte Kette:

Research → Freshness/Racing Relevance → Editor → Source-Fact-Whitelist → Racing-QM → Semantic-QM.

Semantic-QM:
- FACT FAIL → STOP
- PASS → weiter
- rein technischer Providerfehler nach Retries → DEGRADED-PASS → Media → Chief-QM → Final Guard → Persistenz → Telegram Flush → READY_FOR_APPROVAL

**Technischer QM-Fehler ≠ faktischer QM-Fehler.**

Ein technisch ausgefallener Semantic-Agent darf eine bereits deterministisch verifizierte Top-News nicht kommentarlos vernichten.

Gleichzeitig dürfen erfundene Fakten, Zahlen, Fahrer, Teams, Serien oder Ereignisse weiterhin niemals durchgelassen werden.

---

## 15. Wichtige PRs vom 26.09.2026

| PR | Was |
|---|---|
| #139 | Persistenz-Race-Condition + Telegram transaktionssicher |
| #140 | Series-Lock-Selftest Runtime-Parität |
| #141 | Balanced Racing QM (Opinion, Dezimal, DEGRADED-PASS) |
| #142 | DEGRADED-PASS bis Media/Chief-QM durchreichen |

---

## 16. Noch offen

Der nach #142 gestartete neue End-to-End-Run muss ausgewertet werden.

1. Welche aktuellen Kandidaten wurden gefunden?
2. Welche wurden `FULL COPY-QM PASS`?
3. Welche wurden `DEGRADED-PASS`?
4. Erreichen DEGRADED-PASS-Kandidaten jetzt tatsächlich Media?
5. Erreichen sie Chief-QM?
6. Falls Chief-QM ablehnt: exakten Ablehnungsgrund dokumentieren.
7. Werden Binder/Kalender/Bulega final ausgewählt?
8. Werden 5 echte Racing-Storys erreicht?
9. Wird Community-Fallback nur verwendet, wenn wirklich nicht genügend Racing-Kandidaten die komplette Kette bestehen?
10. Persistenz vor Telegram bestätigen.

Keine Tests umgehen. Keine künstlichen PASS-Ergebnisse. Keine Fakten-QM-Sicherungen deaktivieren. Kein automatisches Mergen.

---

## Kurzfazit

Der Research-Agent war nicht das Hauptproblem. Er fand die relevanten aktuellen News.

Das Problem bestand aus mehreren nachgelagerten QM-/Pipeline-Widersprüchen:

Research findet News → überstrenges/technisch instabiles Semantic-QM → DEGRADED-PASS eingeführt → nachgelagerte Finalisierung kannte DEGRADED-PASS nicht → wichtige News verschwanden → Community-Fallback wurde unnötig aktiviert.

Mit #141 und #142 wurde diese Kette gezielt korrigiert.

Der nach #142 gestartete End-to-End-Test entscheidet, ob Binder, Kalender und Bulega vollständig bis Telegram durchlaufen.

---

✅ ENDE DER ÜBERGABE
Alle Teile gelesen (1 bis 3).
Du bist jetzt vollständig auf Stand.
---
