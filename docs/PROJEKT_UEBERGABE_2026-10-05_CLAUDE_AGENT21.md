# Edirne22 Projektübergabe — 05.10.2026, Claude/OpenCode + Agent 21

## Verifizierte Basis
Repository: `Edirne22/KI-SOCIAL-AGENT`

Frozen Code-HEAD vor dieser Dokumentationsaktualisierung:
`0b5803324899e498284509238171d26c3e6c8ead`

Recovery-Branch:
`backup/2026-10-05-claude-agent21-pre-live`

Verbindlich: `PROJECT_GUARDRAILS.md`, `MASTER-SNAPSHOT.md`, `AGENTS.md`, tatsächlicher Code und aktuelle Actions. Historische V5/V6-Übergaben bleiben Archiv; diese datierte Übergabe ist der aktuelle Wiedereinstieg.

## Seit 04.10. verifiziert
- PR #404 `Blockrun: Claude/CODE dashboard transport` wurde gemergt; main-Merge `8d288e8e5996315e084b0e24cc32e58a86dff179`.
- Dashboard besitzt sichtbare CODE-Konsole `Claude CODE · OpenCode`; Serverroute nutzt bestehendes `PRIVATE_ASR_SERVICE`, keine Provider-Secrets im Browser.
- Zielpfad bleibt: Dashboard → Cloudflare Worker/Service Binding → privater Container → OpenCode → OpenRouter → `anthropic/claude-sonnet-4.5` → Dashboard.
- OpenCode CLI 2.0.21 und Claude-only Read-only-Konfiguration werden in das Containerimage gebacken und beim Image-Build verifiziert.
- Agent 21 Gate wurde auf Infrastrukturpfade erweitert. Commit `879ac6894cd56e68c121807eda6d184462fe8dda`; Gate-Run #40 / `37352549743` SUCCESS. Writer-Grenzen wurden nicht gelockert.
- Der Cloudflare-Deploy-Buildfehler durch staged Docker-COPY wurde mit `c9e14d6a7bd4669dfa06597f0de447cb1e2ae3f8` repariert; Deploy Run #23 war SUCCESS.
- Reale Claude-Live-Smokes sind autorisiert, minimal und kostenbewusst; bisher KEIN erfolgreicher Claude-E2E-Nachweis.

## Aktueller Blocker / Root-Cause-Kette
1. Frühere Live-Smokes endeten HTTP 503.
2. Sichere Diagnose wurde ergänzt; Run #29 / `37357083689` zeigte ausdrücklich `error=container_not_ready`, nicht `provider_unavailable`.
3. Normaler `/health` war grün, während der vorgeschaltete `/opencode/health`-Readiness-Pfad scheiterte.
4. Ursache im Worker-Ablauf: `/health` konnte den Container vor dem Secret-versorgten OpenCode-Pfad starten. Der folgende `startAndWaitForPorts(startOptions.envVars)` traf dann auf eine bereits laufende Instanz.
5. Fix `0b5803324899e498284509238171d26c3e6c8ead`: jede Route geht vor dem ersten Containerzugriff durch denselben `startAndWaitForPorts`-Start mit Runtime-Secrets und Internetzugang.
6. Private-ASR-Deploy Run #31 / `37360142879` ist zum Snapshot-Zeitpunkt QUEUED; Job existiert, aber noch kein Runner/keine Steps. Mehrere andere Repo-Actions sind ebenfalls queued, kein Repo-Workflow war zu diesem Prüfzeitpunkt in_progress. Daher noch KEIN Ergebnis des Fixes behaupten.

## Agent 21 / Wartung
- Agent 21 ist der Guarded Development/Instandhaltungsagent für Diagnose, Reparaturvorschläge und begrenzte erlaubte Schreibpfade.
- Infrastrukturänderungen an Dashboard/private-ASR/Claude-only lösen sein Gate aus.
- Agent 11 bleibt Recovery, nicht Coding/Patching.
- Bei der ersten realen privaten Videoproduktion soll beobachtet werden, ob Agent 21 bei einem echten Fehler nachweisbar aktiviert und korrekt diagnostiziert. Keine Aktivierung behaupten ohne Workflow-/Logbeleg.

## Dashboard / CODE
- CODE-Modus und sichtbare Eingabe sind implementiert.
- Windows-Diktat: Win+H in das aktive Textfeld; mobil Tastatur-Diktat. Kein separater CODE-Mikrofonbau erforderlich.
- Bestehende Block-9-ASR/Whisper-Strecke bleibt für andere Audioaufgaben bestehen und wird nicht entfernt.
- Dashboard-End-to-End ist erst fertig, wenn der Live-Claude-Smoke grün ist UND ein realer CODE-Aufruf über das Dashboard nachgewiesen wurde.
- Zukünftig dürfen neue Modelle automatisch entdeckt/angeboten werden; aktives Modell niemals automatisch wechseln. Nutzer bestätigt Modellwechsel manuell. Aktueller Default: Claude Sonnet 4.5.

## Private Produktion — nächster echter Fall
Nach erfolgreichem Claude/CODE-E2E folgt der private Auftrag `Dünya – Level 12`, Task `f6f50c9f4c2690e4eb1fe978`.
Private Fotos/Videos bleiben privat. Keine Social-Veröffentlichung ohne separate ausdrückliche Freigabe. Dieser Fall dient zugleich als erster echter Produktionsbeobachtungspunkt für Agent 21.

## Harte Grenzen
- Guardrails vor jedem technischen Schritt lesen.
- Statusmeldung ist kein Arbeitsende.
- Nach Push/PR sofort Commit/Checks/Actions prüfen.
- Fehler sofort mit Wortlaut, bisherigen Versuchen und Fixvorschlag melden.
- Keine Erfolgsaussage ohne Commit/PR/Run/Log-Beleg.
- Keine Secrets in Repo/Logs.
- Free-first; der minimale reale OpenRouter/Claude-Smoke ist ausdrücklich freigegeben.
- Keine privaten Medien oder Social-Posts ohne passende Human Authority.

## Wiederanlauf
1. Aktuellen main-HEAD, Guardrails, diesen Handover und neuesten Snapshot lesen.
2. Run #31 `37360142879` prüfen.
3. Bei ROT: Job/Steps/Logs → exakter Root Cause → kleinster sicherer Fix → sofort neuer Status.
4. Bei GRÜN: explizit `OPENCODE_CLAUDE_LIVE_OK` belegen.
5. Danach Dashboard-CODE-E2E live prüfen.
6. Erst dann `Dünya – Level 12` starten und Agent-21-Verhalten anhand echter Evidenz beobachten.
