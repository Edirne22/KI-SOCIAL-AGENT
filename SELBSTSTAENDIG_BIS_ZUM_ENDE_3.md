# SELBSTSTAENDIG_BIS_ZUM_ENDE_3 – Anti-Polling / Decision Gate

> Eskalationsstufe V3. Nur einsetzen, wenn V1 und V2 den Agenten nicht aus einer wiederholten Prüf-, Polling-, Monitoring- oder Analyse-Schleife bringen.

## Warum V3 existiert

Beobachtetes Fehlerbild:
Ein Agent prüft GitHub-Workflows, Jobs, Gateway-Tests oder andere Zustände immer wieder, obwohl keine neue Information vorliegt. Die Oberfläche zeigt Aktivität, aber es entsteht kein neues Ergebnis.

V3 setzt deshalb eine harte Grenze zwischen **Beobachten** und **Handeln**.

## Oberste Regel

**Eine vollständige Bestandsaufnahme. Danach Entscheidung und Aktion.**

Eine Prüfung ist kein Fortschritt, wenn sie dieselben Informationen erneut liefert.

## Pflichtlektüre

Vor Recovery lesen:
1. `PROJECT_GUARDRAILS.md`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `SELBSTSTAENDIG_BIS_ZUM_ENDE.md`
5. `SELBSTSTAENDIG_BIS_ZUM_ENDE_2.md`
6. diese Datei.

Alle Guardrails, Kosten-, Datenschutz-, Secret- und Freigaberegeln bleiben gültig.

## Anti-Polling Decision Gate

Für jeden relevanten Workflow/PR/Build/Deploy/Job:

1. Zustand genau einmal vollständig erfassen.
2. Ergebnis klassifizieren:
   - SUCCESS / grün
   - FAILURE / rot
   - RUNNING / tatsächlich laufend
   - BLOCKED / externe Entscheidung nötig
   - STALE / keine relevante Zustandsänderung
3. Unmittelbar die passende Aktion ableiten.

### SUCCESS
Nicht erneut prüfen.
Nächsten abhängigen Schritt ausführen.

### FAILURE
Nicht nur erneut prüfen.
Logs/Evidence lesen → Root Cause → Fix → Regression → neuer Lauf.

### RUNNING
Nicht denselben Zustand in enger Schleife pollen.
Unabhängige sichere Arbeit ausführen und nur nach einer begründeten Zustandsänderung erneut prüfen.

### BLOCKED
Exakt den echten Nutzer-Blocker benennen. Keine künstliche Blockade erfinden.

### STALE
Polling abbrechen. Ursache für fehlenden Fortschritt bestimmen und aktiven nächsten Schritt wählen.

## Harte Wiederholungsgrenze

Derselbe Workflow, Job, PR oder Gateway-Test darf **nicht erneut mit identischem Zweck geprüft werden**, solange:
- keine Zustandsänderung eingetreten ist,
- kein neuer Commit/Run/Deploy existiert,
- keine neue konkrete Hypothese geprüft wird.

Zwei identische Prüfungen ohne neue Information gelten als **LOOP DETECTED**.

Bei LOOP DETECTED:
1. Polling sofort stoppen.
2. letzten gesicherten Zustand festhalten.
3. Entscheidung treffen.
4. aktive Maßnahme ausführen oder alternativen zulässigen Weg wählen.

Eine dritte identische Prüfung ist verboten, außer eine nachweisbare Zustandsänderung rechtfertigt sie.

## Aktionspflicht

Nach einer vollständigen Bestandsaufnahme muss als nächstes mindestens eines entstehen:

- Merge bzw. zulässige Merge-Aktion,
- konkreter Code-/Konfigurationsfix,
- Commit,
- neuer/aktualisierter PR,
- gezielter Regressionstest,
- Deployment/Restart/Recovery,
- Root-Cause-Evidence mit daraus folgender Reparatur,
- alternativer technischer Weg,
- oder ein echter, exakt formulierter Nutzer-Blocker.

**„Weiter überwachen“ ist keine zulässige Abschlussaktion.**

## Zeit ist kein Arbeitsersatz

Keine simulierten Wartezeiten.
Keine künstliche lange Codeausführung.
Keine Beschäftigung durch wiederholte Statusabfragen.

Wenn ein externer Vorgang real läuft, nutze die Zeit produktiv:
- nächsten unabhängigen Schritt vorbereiten,
- relevante Dateien/Logs analysieren,
- Regression vorbereiten,
- Dokumentation/Evidence vorbereiten,
- alternative Hypothesen untersuchen.

**Parallelisieren, wo unabhängig; synchronisieren, wo abhängig.**

## Evidence vor Aktivität

Vor jeder erneuten Statusabfrage frage intern:

**Welche neue Information erwarte ich von genau dieser Abfrage und welche Aktion folgt aus jedem möglichen Ergebnis?**

Wenn darauf keine konkrete Antwort existiert:
**Abfrage nicht durchführen.**

## Zwei-Versuche-Regel

Wenn dieselbe technische Ursache nach zwei ernsthaften Reparaturversuchen weiter blockiert:
- bisherigen Lösungsweg nicht zu Tode reparieren,
- Alternativen recherchieren,
- vorhandene zulässige Provider/Tools/Architekturwege vergleichen,
- robustesten zulässigen Weg zum eigentlichen Endziel wählen.

Provider und Tool sind Mittel zum Zweck.

Keine zusätzlichen Kosten oder freigabepflichtigen Modell-/Providerwechsel ohne erforderliche Zustimmung.

## Endziel vor Teilziel

Nicht bei folgenden Zwischenständen stoppen:
- Analyse abgeschlossen,
- Workflow grün,
- PR grün,
- Commit erstellt,
- Merge erfolgt,
- Deployment erfolgreich,
- Health grün.

Wenn der Auftrag einen realen E2E verlangt, ist erst der reale E2E das Ziel.

## Recovery-Kette

`Reality Snapshot → Decision Gate → Action → Evidence → Root Cause/Fix falls nötig → Regression → CI → Deploy → Health → realer E2E → Dokumentation → operational`

## Stopbedingungen

Stoppe nur bei:
1. nachgewiesenem Endziel/E2E, oder
2. echtem Nutzer-Blocker.

Bei Nutzer-Blocker exakt:
- was blockiert,
- warum es nicht autonom lösbar ist,
- welche eine konkrete Aktion/Entscheidung benötigt wird.

## Standardprompt V3

```text
/BLOCKRUN – V3 ANTI-POLLING / DECISION GATE

Arbeite nach SELBSTSTAENDIG_BIS_ZUM_ENDE_3.md.

Du befindest dich möglicherweise in einer Prüf-/Polling-Schleife.
STOPPE diese Schleife jetzt.

Führe genau EINE vollständige Bestandsaufnahme des realen Zustands durch:
HEAD, relevanter PR, relevante Actions/Jobs, Deployment/Runtime und E2E.

Danach gilt:
SUCCESS → nächsten Schritt ausführen.
FAILURE → Logs → Root Cause → Fix → Regression.
RUNNING → unabhängige sichere Arbeit; kein enges Repolling.
STALE → Polling abbrechen und aktiven nächsten Schritt wählen.
BLOCKED → echten Nutzer-Blocker exakt benennen.

Derselbe Workflow/Job/PR darf ohne neue Zustandsänderung oder neue konkrete Hypothese nicht erneut mit identischem Zweck geprüft werden.

Zwei identische Prüfungen ohne neue Information = LOOP DETECTED.
Dann ist eine weitere identische Prüfung verboten und es MUSS eine Entscheidung/Aktion folgen.

Nach der Bestandsaufnahme muss ein greifbares Ergebnis entstehen:
Merge/Fix/Commit/PR/Test/Deploy/Recovery/Alternative oder echter Nutzer-Blocker.

Provider und Tools sind Mittel zum Zweck.
Nach zwei ernsthaften Fehlschlägen derselben Ursache Alternativen bewerten und den robustesten innerhalb der Guardrails zulässigen Weg wählen.

Status ist kein Stoppsignal.
Workflow-Wartezeit ist keine Arbeitspause.
Parallelisieren, wo unabhängig; synchronisieren, wo abhängig.

Stoppe erst beim nachgewiesenen Endziel/E2E oder echtem Nutzer-Blocker.
```
