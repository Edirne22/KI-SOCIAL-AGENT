# Futuristisches Mission-Control-Cockpit: Stand und Datenspeicherung

Abhängigkeiten: #277 Cloud AI Central → #281 gemeinsame Web-/Telegram-R2-Inbox → #282 OpenCode/Claude-Modellroute → dieser PR (nur sichere mobile Benutzeroberfläche). **Kein Merge/Deploy ohne ausdrückliche Freigabe.**

## Für Bülent jetzt vorbereitet
- Responsives dunkelblau/türkisfarbenes Dashboard, Desktop-Zweispaltenansicht und mobile Chat-/Live-Tabs, Datei-Upload, Mikrofonaufnahme, gemeinsame Telegram-/Web-R2-Liste, echte GitHub-Laufzustände im 10-Sekunden-Takt.
- Neue Moduswünsche: KI-Zentrale, nur Claude, Programmieren mit Claude, Bilder, Audio, Video und Office. Ausgabeformat Chat/PDF/Word/Excel/Bild/Video. **Wünsche werden nur als Text eines R2-Entwurfs gespeichert**. Sie sind ausdrücklich **noch kein sicher implementierter Produktions-Dispatch** und starten keine kostenpflichtigen APIs, Container oder Coding-Agenten. Nach Einführung des formal validierten Routing-Schemas ersetzt dieses UI-Entwurfsformat der strukturierte Task.
- Eine Telemetrie zeigt nur tatsächlich rückgemeldete Auth-/R2-/GitHub-Zustände. Kein simuliertes Code-Streaming. Für echten Event-Stream benötigt es ein getrennt abgesichertes PR mit GitHub-/R2-Event-Ingestion, validiertem Status-Schema und ggf. SSE/Polling.
- OpenCode mit Claude Sonnet 4.5 über OPENROUTER_API_KEY hat bereits eine reale Modellantwort auf GitHub geliefert. **Das ist OpenCode mit Claude als Modell**, nicht die proprietäre Claude Code-Anwendung. Echte Dateiänderungen aus dem Dashboard sind NICHT automatisch freigeschaltet und brauchen einen separaten isolierten PR-/CI-/Human-Approval-Workflow.
- Frontend bleibt technisch auf VPS portierbar; Cloudflare Worker ist nur der erste API-/Hosting-Adapter.

## Dateien: temporärer Container versus dauerhafter R2
Gemäß Cloudflare Containers FAQ und Lifecycle-Dokumentation sind Container-Datenträger **standardmäßig ephemer**. Wenn eine Instanz einschläft, startet sie danach mit frischem Dateisystem aus dem Image; auch ein Rollout kann Instanzen ersetzen. Fertige Medien, XLSX, PDF, DOCX, Agentenzustand und Logs dürfen daher nicht ausschließlich unter lokalen Containerpfaden liegen.

Verbindliche Pipeline: Benutzerupload → privat in R2 mit Task-ID/Prüfsumme → kurzlebiger GitHub-Runner oder bedarfsweise Video-Container lädt Kopie in temporäre Workspace → validierter Prozess generiert Artefakt → bei erfolgreicher Prüfung wird das Artefakt mit Version/Task-ID/Prüfsumme privat nach R2 geschrieben → erst danach Erfolg bzw. Download/Telegram-Link. Worker prüft Zugriffsrechte und gibt keine dauerhaft öffentlichen Bucket-URLs aus. Bei Absturz vor dem Upload wird der Auftrag als FAILED/RETRYABLE markiert, nicht als erledigt. R2 selbst führt keine Tools oder Agenten aus.

Cloudflare unterstützt Snapshot-Restore und R2/FUSE für Sonderfälle, aber das wird NICHT als alleinige Sicherung oder native SSD-Leistung eingeplant. Ein VPS kann dieselbe R2-Ablage über S3-API nutzen. Berechtigungen, Speicherfristen, Kosten und bucketweite Public-Access-Konfiguration vor Live-Freigabe nochmals prüfen.

Quellen: https://developers.cloudflare.com/containers/faq/ und https://developers.cloudflare.com/containers/concepts/architecture/
