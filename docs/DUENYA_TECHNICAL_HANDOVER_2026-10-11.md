# Übergabe / Recovery-Checkpoint – KI-SOCIAL-AGENT – 2026-10-11

**Für den nächsten technischen Bearbeiter. Lies diese Datei zuerst; keine blinden Workflow-Retries.**
**Repository:** https://github.com/Edirne22/KI-SOCIAL-AGENT
**Abgrenzung:** Das separate Projekt `Edirne22/Buelents-Jarvis` ist NICHT dieses Repository. Nicht vermischen.
**Auftrag:** Privates ca. fünfminütiges Geburtstagsvideo „Dünya – Level 12“, 9:16, aus privaten R2-Fotos und Videos, emotionaler Schnitt, Musik/Originalton, nur private Vorschau. Keine Veröffentlichung. Vorhandene Task-ID `f6f50c9f4c2690e4eb1fe978`, Revision `v4-creative1`.
**Geschäftlicher Erfolg:** Eine echte, nachweisbar gerenderte und geprüfte Videodatei. Grüne CI, Deployment oder Recovery allein zählen NICHT.

## Autoritative Regeln / Einstieg
1. `PROJECT_GUARDRAILS.md`, `AGENTS.md`, `CLAUDE.md`.
2. `SELBSTSTAENDIG_BIS_ZUM_ENDE.md`, `SELBSTSTAENDIG_BIS_ZUM_ENDE_2.md`, `SELBSTSTAENDIG_BIS_ZUM_ENDE_3.md` (Anti-Polling).
3. Aktuelles `main`, offene PRs, aktuelle Deployments und Live-R2-Status vor Eingriff erneut prüfen. Diese Übergabe ist ein **Zeitpunkt-Snapshot**, kein Ersatz für den Ist-Zustand.
4. Free-first, keine neuen Paid-Dienste ohne Freigabe. Private Fotos, Videos, Dateipfade, Tokens und R2-Zugangsdaten niemals in öffentliche Logs/PRs. Red-Team-/Regression-/Live-Abnahme vor Erfolgsmeldung.

## Nachgewiesener Zustand am 2026-10-11, ca. 19:30 UTC
- PR #506 merged `9e40daf06a7c9a3e7f71716927c2acffa9fd5944`: privacy-safe Frame-Fehlersignaturen `SIGNAL`, `FFMPEG_EXIT_NONZERO`, `NO_VALID_JPEG` in `content_factory_private_video_orchestrator.py`. Deploy-Run 38165311267: Container/Health erfolgreich; gesamter Workflow rot wegen OpenCode HTTP 502.
- PR #507 merged `95fbba91ffcd6bf8df861c2363a916cc98f793dc`: OpenCode-Checks im Deploy-Workflow non-blocking (`continue-on-error: true`), nicht aus Runtime entfernt. Dies behebt NICHT FFmpeg.
- PR #508 merged `2e1d9066e3117859077e20a04350fc42914e3d25`: Frame-Fehler nach VIDEO/IMAGE differenzieren. **Deployment von #508 zum Zeitpunkt dieser Übergabe NICHT verifiziert**; keine Aussage über neue Runtime-Diagnose treffen, bevor tatsächlich deployed.
- Recovery Run 38166771244, Job 114551265236: Job SUCCESS, aber `Agent 11 recovery-mode exact Dünya resume` und `Continue exact production through QM and private preview` SKIPPED. Agent21 `DIAGNOSE_REQUIRED` / `FRAME_RETRY_NOT_AUTHORIZED`. Das ist **kein** erfolgreicher Produktionsstart.
- Diagnose Run 38167150778, Job 114551969809: SUCCESS (nur Diagnose); R2-Status `DIAG_STAGE=creative_director`, `DIAG_STATUS=FAILED`, `DIAG_ERROR_CLASS=RuntimeError`, `DIAG_FAILURE_SIGNATURE=PRIVATE_VISION_FRAME_EXTRACTION_FAILED`, `DIAG_ACTION=AGENT21_ROOT_CAUSE_REPAIR_REQUIRED`.
- Kein erfolgreicher privater Final-Render, QM-PASS oder Preview-Link nachgewiesen.

## Relevante Code- und Workflow-Einstiege
- `content_factory_private_video_orchestrator.py`: private lokale Bildanalyse, R2-Medien-Download, SHA-256-Prüfung, FFprobe-Dauer, FFmpeg-Frame-Extraktion, JPEG-Validierung, Inferenz.
- `scripts/agent21_duenya_stall_repair.py`: Incident/Status-Abgleich und fail-closed Recovery. In `FAILED` wird bei `DUENYA_FRAME_FIX_VERIFIED=true`, passendem Stage/Error/Incident ein **einmaliger** R2-Autorisierungsmarker via `IfNoneMatch="*"` angelegt. Jeder Fehler beim Schreiben (auch bereits vorhandener Marker) ergibt `FRAME_RETRY_NOT_AUTHORIZED`. Nicht ohne Ursachenprüfung umgehen: Marker kann verbraucht sein.
- `scripts/agent11_private_video_recovery.py`: bewachter Resume nach HANDOFF_AGENT11.
- `scripts/start_duenya_level12_exact.py`: exakt gebundener Task-Start; vorhandenes FAILED wird absichtlich nicht blind neu gestartet.
- `scripts/watch_duenya_level12_production.py`: Watchdog / Produktionsstatus.
- `.github/workflows/recover-duenya-after-agent21.yml`: Recovery mit manueller `verified_frame_fix`-Eingabe oder automatischem Trigger nach erfolgreichem Deploy. **Grüner Job trotz übersprungener Agent11/Produktion möglich.**
- `.github/workflows/diagnose-duenya-creative-failure.yml`: liest gespeicherten R2-Fehler, KEIN Restart, KEIN FFmpeg-Neulauf. Eine alte Fehlersignatur bleibt alt, auch wenn neuer Code deployed wurde.
- `.github/workflows/private-asr-cloudflare-deploy.yml`: Cloudflare Deploy.
- Cloudflare-Health-Endpunkt im Recovery-Workflow: `https://edirne22-private-asr.butupeli.workers.dev/health`; Auth nur aus GitHub-Secrets, niemals hier dokumentieren.

## Exakter kritischer Codepfad / Hypothesen
`content_factory_private_video_orchestrator.py` liest je Asset maximal 100 MiB (Grenze aus Code; **kein Nachweis**, dass konkrete Medien zu groß sind), prüft optionalen Hash, nutzt `ffprobe` für Videodauer, dann `ffmpeg -ss <time> -i <source> -map 0:v:0 -frames:v 1 -vf scale=512:-2 -threads 1 <frame.jpg>`. Für Videos gibt es einen zweiten Versuch bei `-ss 0`. Erfolg erfordert Exitcode 0, Datei >2 Byte, JPEG-Signatur `FF D8 FF`. Mögliche Ursachen: nicht unterstützter Codec, falscher MIME/Dateiinhalt, kaputte Quelldatei, FFmpeg-Binary, ungültiges JPEG, Containerlimit, Timeout. **Keine dieser Hypothesen ist bestätigt.**
Der alte R2-Status meldet nur `PRIVATE_VISION_FRAME_EXTRACTION_FAILED` ohne Unterklasse; neue Unterklassen benötigen einen neuen echten Lauf nach Deployment.

## Für Nachfolger: zielgerichteter Plan (keine Schleife)
1. `main` / PRs / tatsächlichen Container-Deploy-SHA prüfen. Prüfen, ob #508 überhaupt live ist.
2. Vor einem neuen produktiven Retry **lokal bzw. in isolierter, autorisierter Container-Diagnose** einen betroffenen privaten Medien-Asset lesen und mit derselben FFprobe-/FFmpeg-Kommandozeile testen. Nur anonymisierte Metadaten und sichere Fehlerklassen ausgeben (MIME, Codec, Dauer, Bytes, Exit-Kategorie, Timeout, Bildsignatur); keine Medien oder stderr mit Pfaden veröffentlichen. Bei Bedarf einen **einmaligen diagnose-only Workflow** erstellen, der die reale R2-Quelle im sicheren Runtime-Kontext prüft, aber **weder Produktionsstatus noch Recovery-Marker mutiert**.
3. Ursache anhand reproduzierbarer Evidenz beheben; Tests für echten betroffenen Dateityp, Fehler- und Positivfall, Regression und Red-Team durchführen. Keine blind erzwungene Agent21-Freigabe.
4. Nach verifiziertem Deploy und gesicherter Recovery-Strategie den bestehenden Auftrag einmal kontrolliert fortsetzen. Falls R2-Marker bereits existiert: nicht löschen/überschreiben ohne dokumentierten, sicher begrenzten Recovery-Plan; Idempotenz und Double-Start-Risiko prüfen.
5. Agent11 und Video-Pipeline bis QM und privater Vorschau verfolgen. Erfolg nur bei tatsächlichem Render-Artefakt, Dauer/9:16/Audio/Privatsphäre-Check und nachvollziehbarer R2-Evidenz. Fehler sofort als Fehler ausweisen.

## Beleg-Links
- https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/506
- https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/507
- https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/508
- https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/38166771244/job/114551265236
- https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/38167150778/job/114551969809
- https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/workflows/diagnose-duenya-creative-failure.yml
- https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/workflows/recover-duenya-after-agent21.yml

## Wichtig zur Backup-Vollständigkeit
Dieses Dokument ist ein **technischer Übergabe-Checkpoint im Git-Repository**, KEIN vollständiger exportierter System-Snapshot: private R2-Objekte, Cloudflare-Konfiguration, Secret-Werte, Container-Dateisystem, externe Runtime-Daten und vollständige Git-Historie sind nicht in dieser Datei enthalten. Sie bleiben in ihren bestehenden Systemen. Der Nachfolger muss diese Quellen mit autorisiertem Zugriff inventarisieren und bei Bedarf separat sichern. Keine Secrets in Git kopieren.
