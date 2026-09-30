# SNAPSHOT – 2026-09-30 – CONTENT FACTORY NIGHT BUILD HANDOVER

Statuszeitpunkt: 2026-09-30 ca. 02:15 Europe/Berlin  
Repository: Edirne22/KI-SOCIAL-AGENT  
Main beim Snapshot: `1b0aef3ae21a78d22853ce3b1f1491195cf3b375`

## 1. Zweck

Dieser Snapshot ist der aktuelle Übergabepunkt für den Nachtbau der autonomen Edirne-22 Content Factory.
Er ersetzt NICHT den eingefrorenen Milestone-Snapshot vom 29.09.2026 und verändert den Backup-Branch nicht.

Verbindlich bleiben `PROJECT_GUARDRAILS.md`, Human Authority und das Staffellauf-Prinzip:
ANALYSE GESAMTWEG → BUILD → REGRESSION → HANDOFF/SCHNITTSTELLENTEST → STAFFELLAUF → RED TEAM/NEGATIVE CONTROL → POSITIVE CONTROL → ROOT CAUSE/FIX → STAFFELLAUF ERNEUT → CI GRÜN → MERGE.

Keine Tests umgehen, keine künstlichen PASS-Ergebnisse, keine QM-/Security-Gates deaktivieren.
Simulierte Adaptertests dürfen nie als echte Live-E2E-Integration bezeichnet werden.

## 2. Zielbild

Die fertige Fabrik arbeitet 24/7 und kann drei Eingangstypen verarbeiten:
1. Bülents Befehl plus eigene Medien/Audio.
2. Ein Link bzw. vorhandenes Quellenmaterial.
3. Autonome Discovery/Event-/Schedule-Trigger.

Kanonischer Weg:
INPUT → JOB API → BETRIEBSLEITER/ORCHESTRATOR → SPEZIALAGENTEN/MASCHINEN → MEDIA STORAGE → QM/FACT-CHECK → PREVIEW → HUMAN AUTHORITY → PUBLISHER → PLATTFORM/NACHWEIS.

Autonom erlaubt: finden, bewerten, recherchieren, produzieren und QM.
Veröffentlichen bleibt an die Human Authority gebunden.

## 3. Blockplan 1–9

1. Factory Core + Autonomous Queue
2. Persistence + Crash/Resume + R2
3. Discovery + Editorial Scheduler
4. Research + Facts Newsroom
5. Creative Director + Bülent Writing
6. Media Production
7. Voice + Captions + Avatar/Motion
8. End-QM + Goldenes Tablett
9. Web-App + 24/7-Betrieb + bestehender Publisher

Jeder Block wird isoliert getestet UND im vollständigen Weg bis zum aktuell implementierten Endpunkt geprüft.

## 4. Block 1 / PR #230 – aktueller Stand

PR: #230 `feat: establish content factory core contracts`  
Branch: `feat/content-factory-core-v1`  
HEAD beim Snapshot: `c46238952c170a3070d9f52bab4e8e00e48c84a4`  
Status: OPEN, mergeable/clean beim letzten Check.

Enthalten:
- `ProductionJob` und explizite Statusmaschine.
- `MediaRef` mit SHA-256, URI, MIME, Größe, Provenance und Version.
- `LocalScratchStorage` mit Pfadschutz und Integritätsprüfung.
- idempotenter Job-Eingang.
- `ToolTask`/`ToolResult` Maschinen-Handoff mit Job-/Revision-/Task-Korrelation.
- Blockade von Cross-Job-, stale-, noncanonical- und Provenance-Spoof-Handoffs.
- autonome EVENT-/SCHEDULE-Editorial-Trigger ohne Publish-Recht.
- Human Authority für APPROVED/REJECTED/CHANGES_REQUESTED.
- kanonischer `publish_payload`, dessen kompletter Inhalt zusammen mit Revision und Medien in den Approval-Manifest-Hash eingeht.
- idempotenter Publish-Handoff.
- negative Controls gegen Medien-/Caption-/Platform-/zukünftige Publish-Feld-Manipulation.
- MIME/Provenance müssen vorhanden sein.
- nicht JSON-serialisierbarer Publish-Payload wird vor Approval abgewiesen.
- simulierter Staffellauf Discovery → ProductionJob → Maschinen → QM → Human Approval → Publish Queue.

CI:
- Run #18: SUCCESS.
- Run #20 auf HEAD `c462389...`: SUCCESS.
- Syntax/Imports sowie Regression/Red-Team/Positive Controls grün.

WICHTIG:
Die im Staffellauf verwendeten SupoClip-/Pollo-Maschinen sind simulierte Adapter. Das ist ein Contract-E2E, keine Behauptung einer echten Live-SupoClip-/Pollo-Integration.

Vor endgültiger Block-1-Abnahme soll #230 sicher mit dem dann aktuellen `main` synchronisiert und auf dem kombinierten Stand erneut getestet werden.

Bewusste Block-2-Grenzen:
- persistentes JobRepository
- Crash/Resume
- CAS/Concurrency
- Task-Attempt-Ledger
- R2-Backend
- echte Retry-/Recovery-Semantik nach Prozessabsturz.

## 5. Merge-Vollmacht für Nachtbau

Bülent hat am 30.09.2026 ausdrücklich die Vollmacht erteilt, die Blöcke 1 bis 9 während des Nachtbaus selbstständig fertigzustellen und den jeweiligen PR zu mergen, WENN der Block vollständig nach Guardrails abgenommen ist.

Merge-Bedingungen pro Block:
- Architektur/Gesamtweg geprüft
- Build vollständig für den definierten Blockumfang
- Syntax/Imports grün
- Regression grün
- negative Controls/Red Team grün
- positive Control grün
- Staffellauf Start → aktueller Endpunkt grün
- gefundene sichere Fehler behoben und erneut getestet
- CI grün
- PR mergebar
- keine Tests/QM/Human Authority umgangen.

Fehlende externe Accounts/API-Keys/Plattformzugänge dürfen nicht erfunden oder umgangen werden. In diesem Fall Contracts/Adapter/Test-Harness vollständig bauen und den echten Live-Schritt als externen Inbetriebnahmepunkt dokumentieren.

## 6. Offene Research-/Dokumentations-PRs

### PR #229 – Tool Battle
OPEN. HEAD beim Snapshot: `14d7ca748b1864c7c75a58cb93eb6adbbf0e02a8`.
Enthält Architekturentscheidungen/Kandidaten u. a. OpenChatCut, OpenCut-AI, FFmpeg, SupoClip und Pollo. Kein Runtime-Code.

### PR #231 – Prompt/Skill Radar
DRAFT OPEN. HEAD: `becb91079fcd2945b8b5d42953cc9c8a286f00c2`.
Nur kuratierte nützliche Muster aus den gelieferten Guides/PDFs:
- Bülent Voice Profile
- Writing Finalizer/Humanizer-QM
- Repurpose
- Plan + Audit
- YouTube-/Instagram-Skill-Muster
- LUPE/Evidence Guard
- Playbook-Prinzip
- Cross-Model Independent Review
- RAW → WIKI → OUTPUT / EvidenceRawStore → EditorialKnowledge → GeneratedArtifacts
- ECC als Agent-/Skill-/Security-Radar
- Scrapling als späterer WebExtractionAdapter-Kandidat.
Duplikate, reine Tarif-/Marketinginfos und ungeprüfte Provider-Versprechen werden nicht als Produktionsarchitektur übernommen.

### PR #227
OPEN. HEAD: `e927f5d91f47634101999c489179524a6195a375`.
Research-Handover für Model-Fallback; keine Runtime-Änderung.

## 7. Werkzeug-/Maschinen-Zielbild

- Betriebsleiter bleibt Controller/System of Record.
- Externe Tools immer hinter austauschbaren Adaptern.
- SupoClip: priorisierter Kandidat Longform/Quellmaterial → Short/Reel.
- Pollo: GenerativeMediaAdapter-Kandidat für fehlende/generative Medien.
- OpenChatCut: editierbarer Master/Targeted Repair.
- FFmpeg: Low-Level Render/Transcode/Fallback.
- R2: geplanter persistenter Media Store hinter MediaStorageAdapter.
- lokale Whisper/faster-whisper Richtung TranscriptionAdapter.
- VoiceAdapter mit DE/TR und autorisierter Bülent-Stimme; Anbieter austauschbar.
- AvatarAdapter/MotionAdapter inklusive späterem PADDOCK_PRESENTER.
- bestehender eigener Publisher bleibt für MVP bevorzugt; Human Approval darf kein externes Tool übernehmen.

## 8. Human Authority

Automatische Produktion endet vor Veröffentlichung.
Bülent entscheidet: Ändern / Verwerfen / Posten.
Ein explizites `Posten` ist die finale Freigabe der exakt freigegebenen Revision.
Kein nachgelagerter KI-/QM-Agent darf eine gültige manuelle Freigabe erneut vetoen.
Änderungen nach Freigabe müssen die Freigabe ungültig machen bzw. werden durch Approval-Manifest/Revision blockiert.

## 9. Betriebsziel / UX

Ziel-Weboberfläche:
[ + Dateien ]  [ Produktionsauftrag / Freitext ]  [ Mikro ]  [ Senden ]

Status:
Transkribiert → Recherche → Skript → Produktion → QM → Bereit für Bülent.

Preview:
Ändern | Verwerfen | Posten

Telegram bleibt parallel für mobile Status-/Freigabewege.
ChatGPT ist Entwicklungs-/Programmierpartner, aber keine notwendige Produktionsabhängigkeit der fertigen Fabrik.

## 10. Externe Inbetriebnahmepunkte

Je nach später ausgewählten Adaptern können noch nötig sein:
- VPS/Deployment
- Cloudflare/R2 bzw. S3-kompatible Zugangsdaten
- Meta/Instagram/Facebook App-/API-Berechtigungen
- TikTok/YouTube/X-Zugänge, soweit genutzt
- Pollo/SupoClip/sonstige Provider-Konfiguration
- Domain/TLS/Web-Login
- autorisierte Voice-/Avatar-Referenzen.

Diese Punkte hindern die Architektur, Contracts, Test-Harnesses und Offline-/Mock-Staffelläufe nicht am Bau, dürfen aber nicht als echte Live-Integration ausgegeben werden, bevor sie real verifiziert sind.

## 11. Bestehender Milestone-Backup

Der ältere Snapshot bleibt:
`snapshots/SNAPSHOT_2026-09-29_CONTENT_FACTORY_MILESTONE.md`

Der eingefrorene Backup-Branch `backup/2026-09-29-content-factory-milestone` bleibt unverändert.

## 12. Wiederaufnahme

Für eine neue Session:
"Lies snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_NIGHT_BUILD.md, PROJECT_GUARDRAILS.md und den aktuellen Stand der offenen Content-Factory-PRs. Setze den Nachtbau ab dem ersten noch nicht vollständig abgenommenen Block fort. Keine Merge-Freigabe ohne vollständige Guardrail-Abnahme; die dokumentierte Nachtbau-Vollmacht gilt für technisch vollständig abgenommene Blöcke 1–9."
