# SELBSTSTAENDIG_BIS_ZUM_ENDE_2 – Raus aus der Schleife / Final Recovery

> Eskalationsregel für BLOCKRUN-Aufträge. Diese Datei wird verwendet, wenn ein Auftrag trotz `SELBSTSTAENDIG_BIS_ZUM_ENDE.md` in Warte-, Polling-, Status- oder Simulationsschleifen festhängt.

## Zweck

Das Ziel ist nicht Aktivität, sondern ein nachweisbares Endergebnis. Diese Regel ersetzt nicht die Projekt-Guardrails. Sie verschärft ausschließlich die Arbeitsweise bei festgefahrenen Aufträgen.

## Sofortmaßnahme

STOPPE SOFORT alle bisherigen internen Warte-, Polling- und Simulationsschleifen.

Insbesondere:
- keine simulierten Wartezeiten,
- keine simulierte lange Codeausführung,
- keine wiederholte Workflow-Abfrage ohne daraus folgende Aktion,
- keine Statusschleifen,
- keine Wiederholung bereits nachweislich grüner Arbeit,
- ein laufender Workflow, PR, Build oder Deploy ist keine Arbeitspause.

## Pflichtlektüre vor Recovery

Lies zuerst die für das Projekt geltenden Steuerdateien, insbesondere:
1. `PROJECT_GUARDRAILS.md`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `SELBSTSTAENDIG_BIS_ZUM_ENDE.md`
5. diese Datei.

Projekt-Guardrails, Sicherheitsregeln, Kostenregeln, Datenschutz und Freigabegrenzen bleiben vollständig gültig.

## Realitätscheck

Vor neuer Arbeit:
1. tatsächlichen aktuellen HEAD und Zielbranch prüfen,
2. zuletzt gemergte relevante PRs prüfen,
3. relevante Actions/Deployments/Tests prüfen,
4. bereits bewiesene grüne Strecken als Ausgangspunkt akzeptieren,
5. ausschließlich die noch fehlende Strecke bis zum Endziel bestimmen.

Keine Neuarchitektur und kein Neubau funktionierender Komponenten, solange dafür kein konkreter technischer Grund nachgewiesen ist.

## Arbeitsmodus

Untersuche die bestehende Verdrahtung und identifiziere die exakte fehlende oder defekte Stelle.

Arbeitskette:
`Evidence/Fehler → Root Cause → betroffene Stelle → Fix → Regression → CI/Test → Deploy → Health → realer E2E → Dokumentation`

Nach einer echten Codeänderung müssen nachvollziehbare Artefakte entstehen:
- Commit SHA,
- Branch/PR, soweit der Projektprozess dies vorsieht,
- Checks/Actions,
- Merge nach Guardrails,
- Deployment, soweit relevant,
- realer E2E-Beweis.

Wenn keine Codeänderung erforderlich ist, muss stattdessen der vollständige bestehende E2E-Weg konkret nachgewiesen werden.

## Fehlerregel

Bei Fehler:
1. konkrete Logs/Evidence sichern,
2. Root Cause bestimmen,
3. betroffene Datei/Stelle eingrenzen,
4. gezielt reparieren,
5. Regression ausführen,
6. erneut testen und bis zum E2E fortsetzen.

NICHT:
`Fehler → warten → erneut prüfen → warten → simulieren → erneut prüfen`.

Wenn dieselbe technische Ursache nach zwei ernsthaften Reparaturversuchen weiterhin blockiert:
- nicht endlos denselben Ansatz sanieren,
- selbstständig praktikable Alternativen recherchieren und bewerten,
- innerhalb der bestehenden Guardrails den robustesten zulässigen Weg zum Ziel wählen,
- Provider, Tool oder Implementierungsdetail als Mittel zum Zweck behandeln, nicht als Selbstzweck.

Keine zusätzlichen Kosten, geheimen Zugriffe, automatischen Modellwechsel oder sonstigen freigabepflichtigen Änderungen ohne die dafür erforderliche Zustimmung.

## Initiative und Innovation

Du darfst und sollst selbstständig:
- Ursachen tiefer untersuchen,
- bestehende Komponenten anders kombinieren,
- zulässige Alternativen vergleichen,
- unabhängige Arbeiten parallelisieren,
- Regressionen und Diagnosewerkzeuge ergänzen,
- einen festgefahrenen Lösungsweg verlassen, wenn ein besserer zulässiger Weg das Endziel zuverlässiger erreicht.

Dabei gilt:
**Parallelisieren, wo unabhängig; synchronisieren, wo abhängig.**

Nicht blind auf Ergebnisse aufbauen, die noch nicht feststehen.

## Status und Wartezeiten

Eine Statusmeldung ist kein Stoppsignal. Danach unmittelbar mit dem nächsten sinnvollen Schritt fortfahren.

Während Actions, Builds, PR-Checks oder Deployments laufen:
- sichere unabhängige Arbeit erledigen,
- nächsten abhängigen Schritt vorbereiten,
- Code, Tests, Logs oder Dokumentation analysieren.

Nach SUCCESS Ergebnis verifizieren und unmittelbar fortsetzen.
Nach FAILURE Root Cause und Recovery-Kette starten.

## Agenten

Vorhandene Agenten dürfen entsprechend ihrer tatsächlich im Repository verdrahteten Rollen eingesetzt werden. Keine Fähigkeiten oder Zuständigkeiten erfinden.

Diagnose-, Reparatur-, Deployment-, Restart- und Recovery-Schritte müssen nachvollziehbar bleiben.

## Stopbedingungen

STOPPE erst, wenn:
1. das konkrete Ziel vollständig und real E2E nachgewiesen ist, **oder**
2. eine echte Entscheidung/Aktion des Nutzers technisch zwingend erforderlich ist.

Im zweiten Fall exakt nennen:
- was blockiert,
- warum es nicht selbstständig erledigt werden kann,
- welche eine konkrete Aktion oder Entscheidung erforderlich ist.

## Definition „Fertig“

„Fertig“ bedeutet, soweit für den Auftrag relevant:
- Implementierung vorhanden,
- Regression/CI grün,
- Deployment/Runtime aktuell,
- Health bestätigt,
- realer E2E-Weg bestätigt,
- Dokumentation/Evidence vorhanden,
- System wieder operational.

## Standard-Eskalationsprompt

```text
/BLOCKRUN – RAUS AUS DER SCHLEIFE / FINAL RECOVERY

Arbeite nach SELBSTSTAENDIG_BIS_ZUM_ENDE_2.md.

Stoppe alle Warte-, Polling-, Status- und Simulationsschleifen.
Prüfe zuerst die tatsächliche Realität: HEAD, PRs, Actions, Deployments und bereits grüne Strecken.
Bestimme ausschließlich die noch fehlende Strecke bis zum konkreten Endziel.

Arbeite danach selbstständig:
Evidence → Root Cause → Fix → Regression → CI/Test → Deploy → Health → realer E2E → Dokumentation.

Nach zwei ernsthaften Fehlschlägen derselben technischen Ursache:
Alternativen recherchieren und den robustesten innerhalb der Guardrails zulässigen Weg zum Ziel wählen.
Tool oder Provider ist Mittel zum Zweck, nicht das Ziel.

Statusmeldungen sind keine Stoppsignale.
Laufende Workflows sind keine Arbeitspause.
Parallelisieren, wo unabhängig; synchronisieren, wo abhängig.

Stoppe erst bei nachgewiesenem E2E-Ergebnis oder einem echten Nutzer-Blocker.
```
