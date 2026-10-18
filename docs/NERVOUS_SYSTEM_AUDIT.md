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

## Block A.1 – Rollen-Einzelprüfung der 19 nummerierten Rollen (2026-10-18)

Alle **19** im verbindlichen Rollenindex genannten nummerierten Agenten-Dateien wurden auf dem aktuellen Repository-Stand einzeln abgerufen und inhaltlich auf Mission, Grenzen, Übergaben und benannte Abhängigkeiten untersucht. Dies ist **Rollenvertragsprüfung**, keine Bestätigung einer ausführbaren Runtime. Das Mapping der tatsächlichen Python- und Workflow-Einstiegspunkte ist noch ausstehend.

| Rolle | Zuständigkeit und erlaubte Weitergabe aus Rollenvertrag | Besonders zu verifizierende Runtime-Kante |
|---|---|---|
| 01 Content Creator | Text/Hook aus belegten Fakten; keine Publikation | Newsroom → 01 → Creative Director |
| 02 Instagram Curator | Instagram-Format/Plattformversion; keine Freigabe | Creative/01 → 02 → Format-/Media-QM |
| 03 TikTok Strategist | TikTok-/Shorts-Formatkonzept | Creative/01 → 03 → Format-/Media-QM |
| 04 Social Media Strategist | Themen- und Wochenplanung; keine Runtime-Steuerung | Planung → Produktionsleiter; Memory-Inputs |
| 05 Research Synthesist | Recherche und Quellbelege | Ingest → Newsroom/Fact-QM → Redaktion |
| 06 Reddit Community Builder | Reddit-Antwortentwürfe; kein automatischer Versand | Quellen/Brand → 06 → Human Review |
| 07 Video Optimization | Schnitt-/Caption-Plan; nicht eigenmächtig rendern/posten | Creative → 07 → Maschinenvertrag |
| 08 Paid Social Strategist | Nur bezahlte Kampagnenentwürfe, keine Budgetfreigabe | Planung → 08 → Eigentümer |
| 09 Quality Agent | System-/Workflow-QM; **kein** Ersatz für Fact-/Media-/Security-QM | Runs/Logs → 09 → Betriebsbericht |
| 10 Follow Analysis | Nur freigegebene öffentliche Profile; Muster als Inspiration | Öffentliche Inputs → 10 → Ideen/Strategie |
| 11 System Restart | Eng begrenzte Restart-/Recovery-Allowlist | Validierter Incident/Handoff → 11 → erlaubter Workflow |
| 12 Music Agent | Autorisierte Musik, Lizenz- und Format-Preflight | Creative/Media-Rechte → 12 → Audio-Maschine |
| 14 Memory Curator | Evidenzgebundenes Lernen; keine neue Autorität | Receipts/QA → 14 → Memory-Kontext |
| 15 Finance Planner | Zins-/Finanzüberblick; keine Transfers/Banklogins | Geplanter Montag-Trigger → 15 → Telegram-Bericht |
| 17 Instagram Engagement | Zulässige Events klassifizieren, Antworten vorschlagen | Instagram-Event → 17 → einzelne Nutzerfreigabe |
| 18 Tour Ride Story | Private Tourdaten in belegbares Story-Paket | Autorisierte Tourdaten → 18 → Creative |
| 19 KI-Integrationsingenieur | Kontrollierte Adapter/PRs; Rollenvertrag, kein autonomer LIVE-Coder | Scout/Research/Security → 19 → unabhängige Abnahme |
| 20 Maschinen-Scout | Neue Tools suchen; GitHub-Scout als ROLE_ONLY beschrieben | Lücken/QM → 20 → Research/19 |
| 21 Instandhaltungsagent | Kontrollierte Diagnose und Reparatur; keine eigenmächtige Publisher-Freigabe | Incident → 21 → validierter Repair-/Recovery-Pfad |

**Konkrete Rollenkonflikte und Risiken:**
- Historische ID `18` ist nicht eindeutig: heutige Tour-Ride-Rolle versus alte Facebook-Engagement-Nennung. Nummern ohne Rollenname dürfen nicht automatisch dispatchen.
- `09` System-QM darf nicht als unabhängiges Fakten-, Medien- oder Rechte-QM ausgegeben werden.
- `11` Recovery und `21` Repair sind verschieden; die Übergabe muss eng allowlisted und revisionsgebunden sein.
- `19` und `20` enthalten ausdrückliche ROLE_ONLY-/Nicht-LIVE-Einschränkungen; nicht als automatisch laufende Coding-/Scout-Instanzen zählen.
- `15` nennt einen Montag-Cron; die Existenz des wirklichen Schedulers und seiner Zeitzone ist noch nicht nachgewiesen.
- Medienrollen `01/02/03/07/12/18` haben einen Format-/Stil-Preflight; dessen tatsächliche Durchsetzung ist separat zu testen.

**Status:** 19/19 Rollenverträge einzeln gelesen; **0/19** allein dadurch als LIVE verifiziert. Nächste Teilprüfung: `.github/workflows`-Trigger und reale Python-Einstiegspunkte, dann gerichtet erlaubte Kommunikationskanten und Testbelege. Keine produktive Verdrahtung geändert.

## Block A.2 – zusätzliche reale Rollen und erste Workflow-Kanten

**Wichtige Inventurkorrektur:** Die 19 Einträge in `agents/AGENTS_INDEX.md` sind **nicht alle Agenten-Dateien**. Zusätzlich wurden die tatsächlichen Dateien `agents/13_motogp_content_agency.md`, `agents/15_chief_quality_manager.md` und `agents/16_turkish_riders_scout.md` gefunden und gelesen.

- **13 Racing Content Agency:** explizite Research → Domain-QM → Semantic-QM → Chief-QM → Telegram → Human Approval → Publisher-Kette. Keine alte QM-Freigabe nach Rewrite wiederverwenden.
- **15 Chief Quality Manager:** kollidiert numerisch mit `15_finance_planner.md`! Zwei verschiedene Rollen verwenden dieselbe Agentennummer. **P0: niemals nach Nummer 15 allein routen**; stabile Rollen-IDs/kompatible Aliasse festlegen und testen.
- **16 Turkish Riders Scout:** spezialisierte türkische Racing-Recherche mit Unicode-/ASCII-Namensnormalisierung; im aktuellen Rollenindex nicht geführt. Vor Live-Dispatch registrieren und autorisieren.

**Damit mindestens 22 nummerierte Rollen-Dateien geprüft** (19 Indexeinträge + 3 zusätzliche), und mindestens eine bisher nicht erfasste Nummernkollision. Es können weitere Dateien existieren; kein Anspruch auf vollständiges Verzeichnis.

**Erste tatsächliche Workflow-Trigger (Dateien einzeln gelesen):**
- `.github/workflows/telegram-receive.yml`: Cron `2-57/5 * * * *`, `workflow_run`-Abhängigkeiten von Morning/MotoGP/Digest, `workflow_dispatch`, eigene Concurrency `telegram-receive`; GitHub-Scheduler-Liveness und echte Zustellung noch nicht gemessen.
- `.github/workflows/openmontage.yml`: `workflow_dispatch` mit `diagnose/demo/erstellen/planen`, Main-Branch-Gate, Concurrency `openmontage-runtime`, Job benötigt `contents: write` für Request-Claim; prüfen, ob der Telegram-Router sämtliche Produktionsmodi wirklich ansteuert.
- `.github/workflows/openmontage-creative.yml`: synthetischer Render-Test mit FFmpeg und ffprobe, `pull_request`/manueller/`workflow_call`-Trigger; kein Nachweis eines echten Telegram-News-Produktionsauftrags.
- `.github/workflows/agency-org-contract.yml`: statische Tests für Rollen/Organisation/Ressourcenmanager, nur auf festgelegte Pfadänderungen; `docs/NERVOUS_SYSTEM_AUDIT.md` triggert diesen Workflow nicht automatisch.

**Sofortige Sicherheitsforderung für Block B:** kanonische, eindeutige Rollen-IDs unabhängig von historischen Nummern; ID 15 und 18 dürfen nicht unqualifiziert dispatchen. Rollenindex und Allowlist auf reale Module abgleichen, nicht bloß Dokumentation zählen.
