# Dünya V3 – revisionsgebundener Produktionsstart

Verbindlich: PROJECT_GUARDRAILS.md, AGENTS.md und SELBSTSTAENDIG_BIS_ZUM_ENDE_3.md.

Task: `f6f50c9f4c2690e4eb1fe978`; Produktionsrevision `v3`; Runtime-Ziel `duenya-creative-chain-v3`.
Vorhandener Inbox-Auftrag, privates R2-Material und bestehender Renderer bleiben maßgeblich.
Keine Veröffentlichung, kein neuer Dienst, keine zweite Runtime.

## Belegter Ausgangspunkt

- PR #476 / main `5db011d687f4a5cda316f2870c77dcdeed6ab7b7`: Runtime nimmt production_revision entgegen.
- Deployment `37655009226`: Restart HTTP 503; authentifiziertes Revision-Health-Gate wurde übersprungen.
- PR #477 / Merge `e5265120bb1e988142eb9e83d081aab75a9d9c20`: nur transienter Restart-503 wird dem bestehenden Health-Gate überlassen; CI `37656550775` erfolgreich.
- Deployment `37657036261`: alter statischer Vertragstest verlangt bisherige Shell-Bedingung, Fehler `restart must require HTTP 202`. Korrektur und Aufnahme desselben Tests in PR-CI: PR #478.

## Fehlende Übergabe und minimale Ergänzung

Der bisherige exakte Start liest nur den allgemeinen Status und sendet ausschließlich task_id. Ein alter COMPLETED-Status verhindert dadurch V3. Der bestehende Starter erhält deshalb eine fest begrenzte optionale V3-Auswahl; der bestehende Watcher verwendet die gleiche Revision. Der Start-Workflow setzt V3 und ruft danach denselben Watcher auf. Der separate Watch-Workflow bleibt manuell verfügbar, startet aber nicht zusätzlich automatisch beim selben Merge.

Vor einem V3-POST: authentifizierte echte Zielrevision prüfen, exakten bestehenden Inbox-Auftrag validieren, revisionsgebundenen Status prüfen und bisherige allgemeine Status-/Preview-Manifeste einmalig unter revisions/legacy-before-v3 sichern. Bestehende Archive nicht überschreiben. Die eigentlichen alten MP4-Dateien werden nicht verändert.

POST einmalig mit task_id und production_revision. Antwort muss exakte Task-ID, v3 und ACCEPTED/RUNNING belegen; danach muss der V3-R2-Status stimmen. Kein blindes POST-Retry. Ein bereits existierender V3-Lauf wird nicht dupliziert. FAILED eskaliert; alte COMPLETED/READY_FOR_HUMAN-Werte zählen nicht als V3.

## Endliche Abnahmematrix

- Normal: exakter Auftrag, passende authentifizierte Runtime, einmaliger V3-POST, V3-Status, V3-Preview.
- Negativ: alte/falsche/fehlende Revision, falsche Task-ID, falsche Antwortform, nicht bereite Runtime, HTTP-Authfehler.
- Wiederanlauf: vorhandenes RUNNING kein POST; unsicherer POST kein Retry; bestehendes Archiv nicht überschreiben.
- Datenschutz: nur feste Status-/Revisionsnachweise loggen; private Prompt-/Medieninhalte und Zugangsdaten bleiben verborgen.
- Schnittstellen: bestehender Starter → bestehende Runtime → revisionsgebundener R2-Status → bestehender Watcher; private Vorschau benötigt V3 sowie private=true/publishable=false.
- Parallelität: vorhandene Workflow-Concurrency und Runtime-Lock bleiben erhalten; kein zusätzlicher automatischer Watch-Lauf.
- Neue Provider-/Renderfunktionen: N/A, unverändert.
- Live: erst nach erfolgreichem authentifiziertem Runtime-Health und tatsächlicher ACCEPTED/RUNNING-Antwort als gestartet melden. Tests allein sind kein Live-Nachweis.

Zum Zeitpunkt dieser Dokumentation ist V3 noch nicht live nachgewiesen gestartet.
