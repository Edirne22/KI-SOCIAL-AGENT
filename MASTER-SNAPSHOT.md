# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 30.09.2026, ca. 13:30 Europe/Berlin  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`  
**Funktion dieser Datei:** zentraler Einstieg / Inhaltsverzeichnis für den aktuellen Projektstand.

> Diese Datei ist bewusst kurz. Sie zeigt auf die verbindlichen Detail-Snapshots und Guardrails, statt alte Projektstände zu duplizieren.

## 1. Aktueller Einstieg

**Aktueller verbindlicher Arbeits-Snapshot:**

`snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_LIVE_MEDIA_CLOUD_WORKBENCH.md`

Snapshot-Ausgangspunkt:
- Factory Blocks 1–9 gemergt.
- Cloudflare R2 als privates LIVE-Medienlager verifiziert.
- ImageRouter → Factory → R2 LIVE verifiziert.
- Agnes Video → Factory → R2 LIVE verifiziert.
- nächster P1: OpenChatCut im Cloudflare Container als reale Werkbank evaluieren und integrieren.
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
