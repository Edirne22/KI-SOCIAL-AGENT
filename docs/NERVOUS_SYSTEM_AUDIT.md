# Nervensystem V1 – Block A: nachweisorientierte Schnittstelleninventur

**Stand:** 2026-10-18. **Status: IN PROGRESS / NICHT ABGENOMMEN.** Ausgangspunkt main nach Merge #558 (`29fb6787446eb1d9b4d38a58449b2ff12391e08f`). Dieses Dokument ist ein **erster belegter Teilbefund**, keine abgeschlossene Vollinventur und keine Laufzeitfreigabe.

## Verbindliche Prüfregeln
`PROJECT_GUARDRAILS.md` hat Vorrang. Jede Agentenrolle, jeder Eintrittspunkt, jeder Handoff, jede Berechtigung, jedes Fehlerprotokoll und jeder GitHub-Workflow wird einzeln gegen Implementierung und Tests abgeglichen. Dokumentierte Soll-Architektur ist kein LIVE-Beweis. Keine neuen Kosten, Container oder VPS. Kein Social-Publishing ohne revisionsgebundene menschliche Freigabe.

## Verifizierte Ausgangskomponenten und Befunde

| Komponente | Nachweis | Aussage / Lücke |
|---|---|---|
| Hierarchie | `docs/AGENCY_ORG_AND_HANDOFF.md` | Betriebsleiter, Fachagenten, unabhängige Gates und Human Authority definiert; übergreifende Runtime und Ressourcenmanager explizit OPEN |
| Rollenindex | `agents/AGENTS_INDEX.md` | Rollen beschrieben; Dokument sagt selbst: Rolle ist keine laufende Instanz; historische ID 18 mehrdeutig |
| Sicherheitsvorgaben | `AGENTS.md`, `PROJECT_GUARDRAILS.md` | Kein implizites Publishing; Guardrail-Re-Read und evidenzgebundene Statuspflicht |
| Modell-/Agentenberechtigung | `scripts/ai_central_skill_router.py`, `config/ai_central_capabilities.json` | `agent_can` erlaubt zentral definierte Fähigkeiten, `choose_for_agent` verlangt zusätzlich live-verifizierte Provider; noch kein Beweis für sämtliche Agent-zu-Agent-Kanten |
| Jobstatus | `content_factory_core.py` | `ProductionJob` mit Job-ID, Revision und Zustandsübergängen; Anschluss aller Eintrittspunkte noch zu beweisen |
| Faktenübergabe | `content_factory_newsroom.py` | `FactPackage` trennt verifizierte Aussagen von Gerüchten/Konflikten; Verbindlichkeit in jedem Pfad prüfen |
| Creative-Maschinenvertrag | `agents/CREATIVE_DIRECTOR.md` | Szenen, Timing, Assets, Effekte, Revision, Soll-/Ist-Evidence als Pflichten; durchgängige Runtime-Prüfung offen |
| OpenMontage-Telegram | `scripts/openmontage_control.py` | Owner-Chat-Prüfung und feste Aktionen; freie Filmaufträge laut Hilfetext weiterhin nicht über diesen Einstieg ausführbar |
| Organisations-Tests | `tests/test_agency_org_contract.py` | Statische Rollen-/Dokumentationstests; Datei erklärt ausdrücklich: kein Beweis eines Live-Dispatchers |

## Kritische Architekturfragen (offen bis zum Nachweis)
1. Wer ist in **jeder** produktiven Telegram-, Dashboard- und Schedule-Lane die einzige Job-Leitung?
2. Welche konkreten Funktionsaufrufe transportieren Job-ID, Revision, Sprache, Quelle und Rechtebeleg ohne Verlust?
3. Welche gerichteten Agent-zu-Agent-Kanten sind erlaubt, technisch erzwungen und negativ getestet?
4. Wie werden veraltete Revisionen, doppelte Telegram-Updates, fehlende Medienrechte und Provider-Ausfälle fail-closed behandelt?
5. Welche Workflows des gemergten OpenMontage V3 verbinden sich real mit den bestehenden Research-, Creative-, Approval- und R2-Komponenten?
6. Wie werden parallele Content- und Werkstattjobs ohne Identitäts-/Freigabeverwechslung isoliert?

## Fortsetzungsplan – Block A (nicht überspringen)
- Alle `agents/*.md` **einzeln** lesen; je Rolle Auftraggeber, Ausführungsdatei, Input/Output, erlaubte Peers, nächste Station, Fehlerweg und Testbeleg erfassen.
- Danach alle `.github/workflows/*.yml` nach Triggern, Berechtigungen, Secrets-Namen, Übergaben und tatsächlichen Zielmodulen klassifizieren.
- Danach Telegram-/Dashboard-/Schedule-Einstiege, Kern-Factory, Publisher-/Approval-/Recovery-Adapter und OpenMontage-V3-Dateien gegen reale Funktionsaufrufe prüfen.
- Eine vollständige Kantenliste mit Status `LIVE_VERIFIED | IMPLEMENTED_UNVERIFIED | PARTIAL | ROLE_ONLY | BLOCKED | DEPRECATED` und Pfad-/Testbeleg ergänzen.
- Erst danach Block A abnehmen; in Block B fehlende Autorisierung/Verkabelung implementieren, mit positiven und negativen Regressionstests.

**Keine Erfolgsbehauptung:** In dieser ersten Fassung wurden weder alle Agenten einzeln noch alle Workflows und CI-Runs geprüft. Keine produktiven Änderungen.
