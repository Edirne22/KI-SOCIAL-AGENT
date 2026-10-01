# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 30.09.2026, ca. 22:49 Europe/Berlin  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`  
**Funktion dieser Datei:** zentraler Einstieg / Inhaltsverzeichnis für den aktuellen Projektstand.

> Diese Datei ist bewusst kurz. Sie zeigt auf die verbindlichen Detail-Snapshots und Guardrails, statt alte Projektstände zu duplizieren.

**Live-Übergabe 01.10.2026 (neu):** `snapshots/SNAPSHOT_2026-10-01_OPENCHATCUT_DEPLOY_67_HANDOVER.md`. Dieser Zeitpunkt-Snapshot dokumentiert PR #271, den grünen Check #65 und den zum Erstellungszeitpunkt laufenden echten Deploy #67. Bei Wiederaufnahme **erst** aktuelle GitHub-Jobs/HEAD prüfen; den älteren 30.09.-Snapshot als Architektur-/Meilensteinbasis zusätzlich lesen.

## AKTUELLER EINSTIEG – 01.10.2026, 18:40 MESZ – HANDOVER NR. 5

**Neuester verifizierter Projektstand:** `docs/PROJEKT_UEBERGABE_5_2026-10-01.md`  
**Aktueller Zeitpunkt-Snapshot:** `snapshots/SNAPSHOT_2026-10-01_AI_CENTRAL_LIVE_BLOCK6_HANDOVER_V5.md`  
**Code-Wiederherstellungspunkt:** `backup/2026-10-01-ai-central-live-v5`, erstellt vom verifizierten `main` `efad1f9e7000864a20fc235b5b235be4760d2e06`. Backup-Branch nicht überschreiben; er ist nicht technisch schreibgeschützt.  
**Backup-Protokoll:** `docs/BACKUP_PROTOKOLL_2026-10-01_V5.md`.

Die KI-Zentrale ist seit heute nach sechs genehmigten PR-Merges als **privater Dashboard→GitHub→kostenloses Modell→R2→Dashboard-Pfad real E2E geprüft**; zweiter Diagnoseauftrag hatte allerdings nur **eine** erfolgreiche von zwei Rollen. Claude/OpenCode sind separat getestet, nicht als produktive Dashboard-Claude-Lane freigeschaltet. OpenChatCut/SupoClip bleiben im vollständigen Block-6-Medienweg NICHT LIVE. OpenChatCut-Diagnose #278 ist bereits gestapelt auf #271 vorbereitet, beide noch offen. Nicht erneut dieselben Experimente entwickeln.

**Lesereihenfolge bei Chatwechsel:** `PROJECT_GUARDRAILS.md` → diese Datei → `docs/PROJEKT_UEBERGABE_5_2026-10-01.md` → aktueller V5-Snapshot → älterer OpenChatCut-Snapshot → live HEAD/PRs/Actions verifizieren. Der weiter unten stehende Einstieg vom 30.09. und Live-Handover zu Run #67 sind historische Arbeitsstände und dürfen die neuere Übergabe nicht übersteuern. Die ursprünglich erwähnte originale Übergabe Nr. 4 ist derzeit nicht eindeutig auffindbar; V5 kennzeichnet diese Archivlücke.

---

## 1. Aktueller Einstieg

**Aktueller verbindlicher Arbeits-Snapshot:**

`snapshots/SNAPSHOT_2026-09-30_OPENCHATCUT_BLOCK6_LIVE_CANDIDATE.md`

Snapshot-Ausgangspunkt:
- Factory Blocks 1–9 gemergt.
- R2, ImageRouter → R2 und Agnes Video → R2 LIVE verifiziert.
- OpenChatCut Cloudflare-PoC deployed und als LIVE_CANDIDATE bis MCP/create_project/target_project real verifiziert.
- begin_edit_session zeigte einen Cloudflare-Disconnect; PR #259 diagnostiziert Restart/State-Verlust vs. Transportproblem fail-closed.
- aktueller Produktionslauf: 36773936472.
- OpenChatCut bleibt bis Import/Edit/Headless-Render/R2/SHA/ffprobe/7-15-30s-Caption-Audio-Abnahme NICHT LIVE.
- danach SupoClip LIVE integrieren und vollständige Video-Staffel testen.

**Verbindliche Guardrails:**

`PROJECT_GUARDRAILS.md`

Vor größeren Änderungen immer zuerst Guardrails + aktuellen Snapshot lesen.

## 2. Snapshot-Historie

### 30.09.2026 – LIVE Media / Cloud Workbench
`snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_LIVE_MEDIA_CLOUD_WORKBENCH.md`

Aktueller Stand nach Factory 1–9, R2 LIVE, ImageRouter LIVE und Agnes Video LIVE. Enthält außerdem Cloudflare-Container-/OpenChatCut-Strategie, SupoClip-Plan, Storage-/Lifecycle-Plan und P1/P2/P3-Roadmap.

### 30.09.2026 – Night Build
`snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_NIGHT_BUILD.md`

Historischer Übergabepunkt zu Beginn des Factory-Nachtbaus. Damals war Block 1 / PR #230 noch offen. Nicht mehr als aktueller Arbeitsstand verwenden.

### 29.09.2026 – Content Factory Milestone
`snapshots/SNAPSHOT_2026-09-29_CONTENT_FACTORY_MILESTONE.md`

Historischer Meilenstein nach Stabilisierung der Turkish-Rider-Human-Approval-/Publisher-Kette und vor dem großen Factory-Ausbau.

Backup:
`backup/2026-09-29-content-factory-milestone`

Dieser Backup-Branch bleibt eingefrorener Wiederherstellungspunkt.

## 3. Aktuelle Architektur in einem Blick

`INPUT → JOB/ORCHESTRATOR → DISCOVERY/NEWSROOM → CREATIVE → MEDIA → AV → FINAL QM/GOLDEN TABLET → HUMAN AUTHORITY → PUBLISHER`

Media-Zielweg:

`SOURCE / GENERATED MEDIA → SUPOCLIP → OPENCHATCUT → FFMPEG → R2 → GOLDEN TABLET → BÜLENT → PUBLISHER`

Aktuell real LIVE nachgewiesen:
- Cloudflare R2 Storage.
- ImageRouter → R2.
- Agnes Video → R2.

Noch nicht als LIVE abgenommen:
- SupoClip.
- OpenChatCut.

SIMULATED darf niemals als LIVE bezeichnet werden.

## 4. Infrastruktur-Merksatz

- **GitHub** = Baupläne, Code, CI.
- **Cloudflare Container / später VPS** = Werkbank und Maschinen.
- **Cloudflare R2** = dauerhaftes privates Medienlager.
- **Golden Tablet** = finale Human Preview.
- **Bülent** = finale Veröffentlichungsautorität.

Cloudflare Container dient zunächst als Beta-Messstand für OpenChatCut/FFmpeg. Ein späterer x86-VPS wird anhand real gemessener Qualität, Quantität, CPU/RAM/Disk, Renderzeit und Kosten dimensioniert.

## 5. Human Authority

Autonom erlaubt:
- Discovery.
- Recherche.
- Faktenprüfung.
- Creative.
- Medienproduktion.
- QM.

Veröffentlichung:
- Bülent entscheidet `Ändern / Verwerfen / Posten`.
- gültige Human-Freigabe darf von nachgelagerter KI nicht erneut vetoed werden.
- Änderung nach Approval macht die Freigabe ungültig.
- keine automatische Veröffentlichung ohne gültige Human Authority.

## 6. Wiederaufnahme-Anweisung

Bei neuer Session oder Projektübergabe:

1. `MASTER-SNAPSHOT.md` lesen.
2. `PROJECT_GUARDRAILS.md` lesen.
3. `snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_LIVE_MEDIA_CLOUD_WORKBENCH.md` vollständig lesen.
4. aktuellen `main` gegen den dort dokumentierten Stand prüfen.
5. bei P1 fortsetzen:
   - OpenChatCut Cloudflare-Container PoC.
   - echter OpenChatCutAdapter.
   - OpenChatCut → FFmpeg → R2 Live-Staffellauf.
   - SupoClip LiveAdapter.
   - Source → SupoClip → OpenChatCut → FFmpeg → R2 Gesamtstaffellauf.
   - sicherer Bild-/Video-Preview für Bülent.

Keine Tests umgehen, keine künstlichen PASS-Ergebnisse, keine QM-/Security-Gates deaktivieren und keine simulierten Provider als LIVE ausgeben.

## 7. Historischer Hinweis

Der frühere Inhalt dieser Datei dokumentierte detailliert den Racing-Stand vom 16.09.2026. Dieser Stand ist inzwischen durch zahlreiche spätere Commits, Übergaben und Snapshots überholt.

Historische Racing-Details bleiben in Git-Historie, Projektübergaben und älteren Snapshots nachvollziehbar. `MASTER-SNAPSHOT.md` dient ab jetzt als **lebender Projektindex zum jeweils aktuellen Snapshot** und nicht mehr als eingefrorene Vollkopie eines einzelnen Tages.
