# CLAUDE.md — Edirne22 / KI-SOCIAL-AGENT

## Zweck
Operative Coding-Anweisung für Claude und andere Coding-Agenten in diesem Repository. Diese Datei ergänzt, aber ersetzt niemals `PROJECT_GUARDRAILS.md`, `MASTER-SNAPSHOT.md` oder die aktuelle Projektübergabe.

## Verbindlicher Guardrail-Arbeitszyklus

Vor Beginn technischen Arbeitens die aktuelle `PROJECT_GUARDRAILS.md` lesen. Die Re-Read-Trigger aus Abschnitt 0.1 gelten während der gesamten Sitzung: nach längerer Status-/Chat-Unterbrechung, nach Fehler/Abbruch vor einem Fix sowie bei Scope-/Richtungswechsel vor Push/PR/Merge/Deploy. Nach Push/PR sofort tatsächlichen HEAD, Checks und Actions prüfen. Statusmeldung ist kein Stopp; kein „später“/„im Hintergrund“ ohne reale Automation; Erfolge nur mit Beleg.

## Pflicht vor jeder größeren Änderung
1. Aktuellen `main`-HEAD, offene relevante PRs und laufende/letzte relevante Actions prüfen.
2. `PROJECT_GUARDRAILS.md` lesen.
3. `MASTER-SNAPSHOT.md` und die dort genannte aktuelle Projektübergabe lesen.
4. Vorhandene Implementierung/Tests zuerst verstehen; keine parallele Architektur bauen, wenn ein bestehender Pfad erweitert werden kann.
5. Erfolgskriterien und Nicht-Ziele kurz festlegen.

## Think before coding
- Keine stillen Annahmen bei echter Mehrdeutigkeit.
- Unsicherheit und relevante Trade-offs sichtbar machen.
- Einfachste Lösung bevorzugen, die die Anforderung vollständig erfüllt.
- Bei fehlender notwendiger Information stoppen und konkret benennen, was fehlt.

## Simplicity first
- Minimum an Code für den Auftrag.
- Keine ungefragten Features.
- Keine Abstraktion nur für hypothetische spätere Nutzung.
- Keine neue Konfiguration oder Infrastruktur ohne belegten Bedarf.
- Wenn eine deutlich kleinere Lösung denselben Zweck erfüllt, vereinfachen.

## Surgical changes
- Nur notwendige Dateien/Zeilen anfassen.
- Bestehenden Stil und Architektur beibehalten.
- Keine angrenzenden Refactorings, Formatierungsaktionen oder Cleanup-Arbeiten ohne Scope-Bezug.
- Nur durch den eigenen Patch neu verwaisten Code entfernen.
- Unabhängige Altprobleme melden, nicht heimlich mitfixen.
- Jede geänderte Zeile muss auf Anforderung, Test oder zwingende technische Folge zurückführbar sein.

## Diff-Guard
Vor jedem PR/Merge:
- Basis-HEAD bestätigen.
- Ahead/Behind prüfen.
- Liste geänderter Dateien prüfen.
- Diff-Größe und Dateigrößen auf Plausibilität prüfen.
- Unerwartet großer Diff = STOP. Nicht mergen.
- Bei verdächtigem Patch die gewünschte Änderung aus sauberem aktuellem `main` neu aufbauen.

Regression 04.10.2026: Beim ersten Versuch des Publisher-/Dedupe-Fixes für PR #378 entstand unbeabsichtigt ein massiv aufgeblähter/duplizierter Datei-Diff. Er wurde verworfen und aus sauberem `main` minimal neu aufgebaut. Dieses Muster darf nicht weitergeschoben werden, selbst wenn einzelne Tests grün wären.

## Goal-driven execution
Für Bugs:
1. Fehler reproduzieren → verify: gezielter Regressionstest/Nachweis schlägt vor Fix fehl.
2. Minimal beheben → verify: Regressionstest grün.
3. Relevante Negativfälle + Positive Control + bestehende Regression → verify: finaler HEAD grün.
4. Diff/Scope prüfen → verify: keine sachfremden Änderungen.

Für mehrstufige Features die Abnahmematrix aus `PROJECT_GUARDRAILS.md` verwenden.

## Edirne22 harte Projektgrenzen
- Private Medien standardmäßig privat.
- Keine eigenständige Social-Veröffentlichung; nur konkrete menschliche Freigabe für den exakten Beitrag/Revision/Asset.
- Free-first; keine neuen Kosten ohne Freigabe.
- Keine Secrets, privaten Medien oder personenbezogenen Inhalte in Logs/Repo/CI.
- Bestehende Human-Authority-, Dedupe-, Idempotenz-, Fakten-/Quellen-QM- und Publisher-Gates nicht umgehen.
- FFmpeg FIRST; vorhandene Architektur wiederverwenden.
- OpenChatCut, SupoClip und OmniRoute/Omniroot/OmniHut bleiben PAUSED, solange der aktuelle Snapshot nichts anderes ausdrücklich festlegt.
- Selora bleibt Backup-Idee und wird nicht eigenständig integriert.
- Keine zweite Telegram-Polling-Schleife oder konkurrierendes Publishersystem bauen.
- Containerarbeit über die zentrale Readiness/Warm-up-Regel der Guardrails; reine Reads wecken keinen Container.

## /BLOCKRUN
Wenn ein Auftrag als `/BLOCKRUN` läuft:
- zuerst HEAD/Guardrails/Snapshot/PRs/Actions verifizieren;
- keine bereits erledigte Arbeit doppelt ausführen;
- keine unnötigen parallelen Branches;
- Regression/CI/Red-Team/Positive Control nach Scope;
- sichere bestehende technische Vollmacht nutzen, aber Privacy-, Kosten- und Publishing-Grenzen niemals daraus ableiten oder überschreiten;
- nur tatsächlich belegte Zustände als LIVE/FERTIG melden.

## Abschluss
Ein Auftrag ist erst fertig, wenn die vereinbarten Erfolgskriterien auf dem finalen HEAD belegt sind. Statusmeldungen sind kein Ersatz für Tests. Ein grüner CI-Lauf ist kein Beweis für ungeprüfte Live-Funktionalität.
