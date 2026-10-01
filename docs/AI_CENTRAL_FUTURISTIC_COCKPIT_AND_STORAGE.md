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


## Verbindlicher Ausbau: mehrere voneinander unabhängige Coding-Agenten

**Nutzerwunsch 01.10.2026:** Das Cockpit darf sich nicht auf Claude Code oder OpenCode festlegen. Ein gemeinsamer Task-Vertrag wählt bewusst einen einzelnen Codierer oder eine abgegrenzte Gegenprüfung durch mehrere; jedes Ergebnis bekommt Provenienz (Programm, Provider, Modell, GitHub-Commit, Tests und Kosten, soweit verfügbar). Ohne ausdrückliche Auswahl keine ungefragte Ersatz-KI für einen ausdrücklich gewünschten Codierer. Kein eigenmächtiger Merge oder Deploy.

| Kandidat | Rolle | Realer Projektstand / Integrationsgrenze |
|---|---|---|
| **OpenCode** + Claude Sonnet via OpenRouter | unabhängiger Cloud-Coding-Agent | CLI auf GitHub-Runner sowie ECHTER begrenzter Claude-Antworttest erfolgreich (#282); Repo-Dateiänderungen/PRs und Tool-Berechtigungen bleiben gesondert freizugeben und zu testen |
| **OpenCode** + andere zugelassene Provider/Modelle | Coding-Redundanz / Review | Vorhandene API-Schlüssel (OpenRouter, NVIDIA, Google, Groq) einzeln auf Coding-Fähigkeit/Toolaufrufe prüfen; keine pauschale Freischaltung aller Katalogmodelle |
| **Claude Code** (Anthropic-Produkt) | optionaler separater Coding-Worker | Nicht identisch mit OpenCode + Claude-Modell. Tatsächliche Authentifizierung, Lizenz/API-Abrechnung und für unattended Cloud-Runner zulässiger Betrieb separat prüfen; aktuell KEIN bestätigter direkter ANTHROPIC_API_KEY |
| **OpenAI Codex** | optionaler Coding-Agent | ChatGPT-Abonnement ist nicht automatisch OpenAI-API-Guthaben und ein Codex-Connector ist nicht automatisch ein unbeaufsichtigter API-Zugang; Integration nur nach verifiziertem Berechtigungsmodell/Preis |
| **GitHub Copilot** | optionaler Coding-/Review-Dienst | GitHub-Repository-Zugang oder Copilot-Abo ist kein beliebig weiterverwendbarer Backend-API-Schlüssel. Offizielle GitHub-Workflow-/Agent-Zugänge und gesonderte Freigabe prüfen |
| **Google Jules** | optionaler asynchroner Coding-Agent | Eigenständige Produktberechtigung/Quota und aktuelle offiziell unterstützte GitHub-Integrations-/API-Schnittstelle prüfen; Gemini-AI-Studio-Key allein belegt keinen Jules-Pro-Zugang |
| **Cursor** | optionaler Entwicklungsagent | Cursor-Abo und Cursor-Background-Agent/API-Berechtigungen getrennt prüfen; keine unbelegte Verbindung über vorhandene LLM-API-Keys behaupten |

Geplanter gemeinsamer **Coding-Dispatcher**: Dashboard/Telegram -> task_id + gewünschter Coding-Modus -> Auth/Policy/Credit-Gate -> ausgewählter Coding-Adapter -> isolierter GitHub-Runner bzw. offiziell autorisierter Remote-Coding-Dienst -> Branch + Draft-PR -> CI und mehrere unabhängige Review-Rollen -> private R2-Artefakte/Log-Ereignisse -> Bülents explizite Freigabe. Modelle, Provider-Kataloge und separat lizenzierte Coding-Produkte sind drei verschiedene Inventare. GitHub-Secrets bleiben der geheime Quellort für Schlüssel in GitHub Actions; Cloudflare-Worker-Secrets für von Workers selbst benötigte Zugänge. Schlüssel werden niemals vom Browser ausgelesen oder in R2 mit Reports gespeichert.

**Physischer Ablauf:** Cloudflare Worker hostet Oberfläche/API, private R2-Ablage hält alle Dateien und Ergebnisversionen dauerhaft; **GitHub Actions ist zurzeit die eigentliche, kurzlebige Rechenmaschine**, die OpenCode startet und Modell-APIs anspricht. Auf R2 selbst wird weder OpenCode noch Claude Code „installiert“ oder ausgeführt. Falls Cloudflare-Container unzuverlässig bleibt, können Coding-Jobs weiter auf GitHub Actions laufen; bei Bedarf wird nur der Compute-Adapter auf einen x86-VPS migriert. Ein dauerhafter, ständig verfügbarer Dienst oder UI-Live-Stream ist erst nach gesondertem Deploy und Abnahmetest real.
 
**Späteres ausdruckbares A3-Diagramm:** Eingang (Telegram/Web) -> Steuerung/Auth -> Master/Agenten -> getrennte Coding-/Bild-/Audio-/Video-/Dokument-Lanes -> Runner/Container/VPS -> QA/Freigabe -> R2/GitHub -> Antwort. Legende muss „LIVE“, „getesteter Baustein“, „geplant“ und „externer Dienst benötigt Zugang“ sauber unterscheiden.
