# Block 6 – Video Tool Battle

Stand: 2026-10-01

## Guardrail
OpenChatCut bleibt in diesem Vergleich unverändert. Kein Kandidat wird als LIVE bezeichnet, bevor ein realer Render-/Handoff-/Storage-Staffellauf bestanden wurde.

## SupoClip – Cloudflare PoC Ergebnis
Der Worker/Auth-Vertrag funktioniert. Der reale Container-Readiness-Test blieb rot: der Container wurde provisioniert, beendete sich beim Start jedoch wieder.

Die isolierte Backend-Variante ist kein vollständiger SupoClip-Self-Host. Der Upstream benötigt für den produktiven Pfad zusätzlich PostgreSQL, Redis und einen Background Worker. Ein künstlicher Ein-Container-Umbau wird deshalb im Block 6 nicht weiterverfolgt.

Status: **DEFERRED für späteren x86-VPS / vollständigen Compose-Stack**, nicht LIVE.

Evidenz: GitHub Actions Run 36788055479, Job 110137533193.

## Ersatz-Battle

### Kandidat A – Ekaanth/OpenCut-AI
MIT, lokal/self-hosted und funktional interessant. Die beworbenen Auto-Shorts-/Virality-Funktionen werden nicht allein aufgrund der README als vorhanden angenommen. Vor Integration ist ein Code-/Runtime-Nachweis erforderlich.

Status: **DISCOVERY**.

### Kandidat B – floomhq/opencut
MIT-lizenzierter, programmgesteuerter Video-Produktionsmotor mit konkreten CLI-Einstiegen für Validate, Transcribe und Render sowie Remotion/FFmpeg-orientierter Ausgabe.

Pinned PoC commit:
`57dedbc606e17cc2013f2ca5fcbf8cc69266e488`

Die PoC-CI muss:
1. den exakten Upstream-Commit auschecken,
2. npm-Abhängigkeiten installieren; fehlendes Upstream-Lockfile als Reproduzierbarkeitsrisiko festhalten,
3. Upstream-Tests ausführen,
4. TypeScript prüfen und bauen,
5. einen echten headless 5-Sekunden-Render erzeugen,
6. das MP4 mit ffprobe validieren.

Erst danach folgt der Edirne-22-Adapter mit echtem Eingabemedium, 9:16/Caption/Audio, R2/SHA-256 und Golden-Tablet-Handoff.

Status: **LIVE_CANDIDATE / PoC**, nicht LIVE.

### Reproduzierbarkeits-Finding
Der gepinnte floomhq/opencut-Commit enthält kein `package-lock.json`. `npm ci` ist deshalb nicht möglich. Der PoC verwendet `npm install` nur zur technischen Eignungsprüfung. Für eine produktive Übernahme muss Edirne-22 entweder einen geprüften Dependency-Lock/Snapshot besitzen oder der Kandidat wird verworfen.
