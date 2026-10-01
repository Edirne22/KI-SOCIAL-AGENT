# KI-Zentrale – überprüfte Fähigkeiten, Provider und Dokument-Skills

**Prüfstand:** 2026-10-01, GitHub Live-Run [#36866075251](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/36866075251). Private R2-Archivkopie unter `ai-central/v1/inventory/github-run-36866075251.json`; GitHub-Aktionsartefakt `ai-central-model-audit-36866075251`. Diese Daten enthalten **nur Secret-Vorhandensein und Modell-IDs**, keine Schlüssel. Die abgefragten 11 Namen sind keine Garantie, dass wir alle GitHub-Repo-Secrets enumeriert haben.

## Tatsächlich nachgewiesene Zugangsvoraussetzungen

| Name in GitHub Actions | Ergebnis | Bedeutung |
|---|---|---|
| GEMINI_API_KEY | VORHANDEN | Google Modellkatalog erreichbar, Bildinferenz und Preis **nicht geprüft** |
| NVIDIA_API_KEY | VORHANDEN | NVIDIA Modellkatalog erreichbar, individuelle Modelle weiter zu prüfen |
| GROQ_API_KEY | VORHANDEN | Groq Modellkatalog erreichbar, ausgewählte Modelle weiter zu prüfen |
| OPENROUTER_API_KEY | VORHANDEN | OpenRouter Modellkatalog mit Claude-Modellen erreichbar, konkrete Claude-Inferenz **nicht getestet** |
| AGNES_API_KEY | VORHANDEN | Im bisherigen Media-Router vorgesehen, Zugriff nicht durch diese Inventur inferenzgeprüft |
| TOGETHER_API_KEY | VORHANDEN | Bestehender Bild-Router; noch kein neues Live-Inferenzgüteurteil |
| POLLINATIONS_API_KEY | VORHANDEN | Bestehender Bild-Router; noch kein neues Live-Inferenzgüteurteil |
| CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID | VORHANDEN | Worker/Workers-AI-Routen konfiguriert; OpenChatCut-Container weiterhin getrennt instabil |
| R2_BUCKET_NAME | VORHANDEN | R2-Speicher bereits durch gesonderten erfolgreichen Cloud-E2E-Test beschrieben |
| ANTHROPIC_API_KEY | **NICHT vorhanden** | Direktes Anthropic Claude benötigt gegebenenfalls neuen Schlüssel. Alternativ existiert ein Claude-Katalogweg über OpenRouter; Nutzbarkeit und Kosten offen. |

**Nicht Gegenstand des Audits:** `AI_DASHBOARD_TOKEN` im Dashboard-PR #281. Der private Dashboard-Deploy prüft dieses zusätzliche Secret; vor Nutzung muss Bülent den zufällig generierten >=24-Zeichen-Token in GitHub Secrets hinterlegen. Keine API-Schlüssel im Telegram-Chat, in Git-History, an ChatGPT oder in R2 speichern.

## Modellkatalog und Kategorien (KEIN kostenloser Massenfreibrief)

| Dienst | Gefilterte Katalog-IDs | Im Katalog bestätigte Beispiele |
|---|---:|---|
| Google AI Studio | 47 | `gemini-3.1-flash-image` (Nano Banana 2), `gemini-3-pro-image`, Veo 3.1 Preview-Varianten |
| NVIDIA NIM | 20 | Nemotron Lightning, Nemotron Ultra/Super, multimodale Varianten |
| Groq | 6 | Im Ergebnisarchiv dokumentiert; tatsächliche Antwortmodelle separat testen |
| OpenRouter | 231 | Claude Sonnet/Opus/Haiku-IDs, Qwen, Gemini-Bildmodelle und weitere – dynamischer Katalog |
| Anthropic direkt | 0 | Kein `ANTHROPIC_API_KEY` in diesem überprüften Workflow |

Dies sind durch Filter gezählte Namen; Listen können doppelte Versionen, kostenpflichtige Modelle, alte Modelle oder Modelle ohne Guthaben enthalten. Keine 231 parallelen Aufrufe. Die erste cloud-only KI-Zentrale verwendete bereits Google, OpenRouter und Fallbacks erfolgreich. Ein negativer NVIDIA-/Groq-Test eines Einzelmodells ist nicht gleichbedeutend mit genereller Anbieter-Störung.

## Aufgabenspezialisten – Ist, vorbereitet, fehlt

| Aufgabe | Vorhandene Werkzeuge | Aktivierung der zentralen Route |
|---|---|---|
| Text, Recherche, Gegenprüfung | Google, OpenRouter, NVIDIA, Groq | Teilweise echtes E2E über #277 |
| Programmierung | OpenCode CLI auf gehostetem GitHub Runner installiert und Versionstest **PASS** | Einzelnen isolierten Coding-Job samt Rechte-/CI-Gate noch implementieren |
| Nur Claude anfordern | Direkte Anthropic-API oder exakte Anthropic-Claude-Modell-ID über OpenRouter | Zwei zugelassene **Claude-Transporte**, null stiller Gemini-Fallback; keine behauptete Claude-Inferenz ohne Live-Probe |
| Bildgenerierung | Vorhandener `image_router.py`: Agnes, Cloudflare FLUX, Together, Pollinations, NVIDIA FLUX | Google Nano-Banana-2-Adapter in diesem PR als separate, explizit freizugebende Schnittstelle ergänzt; echte Bildgenerierung **noch nicht** gestartet |
| Bildanalyse, OCR | `vision_router.py`: NVIDIA Muse/Nemotron OCR/Omni | Bestehende Funktionsweise separat testen und in KI-Auftragsroute wiederverwenden |
| Video aus Prompt | Bestehendes Agnes Video, Google-Veo-IDs im Katalog | Agnes vorhandene Pipeline; Veo bisher **nur Katalog**, keine Implementierung/Freigabe |
| Videobearbeitung | FFmpeg + FFprobe, OpenChatCut | FFmpeg Cloud-Probe in diesem PR; OpenChatCut separat instabil |
| Audio | FFmpeg/FFprobe für technische Bearbeitung; Whisper/Faster-Whisper nur vorbereitete Schnittstelle | Transkription/Audio-KI und Laufzeitmodell noch implementieren |
| PDF/Word/Excel neu erzeugen | ReportLab, python-docx, XlsxWriter im gehosteten CI-Skill-Job | Drei echte Smoke-Dateien wurden im Job erstellt; nicht gleichbedeutend mit fertig getesteten Nutzer-Uploads |
| Vorhandene Excel hochladen und bearbeiten | Geschützter Upload als **R2-Entwurf** in #281 | Originaltreue, Formeln, Charts, Claude-only-Inferenz und finaler Excel-Download **noch eigener E2E-Test** |

## Sicherer Ablauf des gewünschten Claude-only Excel-Auftrags

1. Bülent lädt die XLSX-Datei über das private Dashboard hoch; R2 speichert Original + Hash unverändert.
2. Das System validiert Dateiformat, Größe, Makro-/Formelrisiken und erstellt einen separaten Task. Das vorhandene Original bleibt unverändert.
3. Die Modellauswahl erhält `forced_provider=claude`; zulässig sind ausschließlich **nachweislich inferenzfähige Claude-Modelle**, direkt oder exakt über OpenRouter. Ansonsten Fehler, **kein automatischer Gemini-/Qwen-Fallback**.
4. Claude entwickelt den Änderungsvorschlag in einem isolierten Runner. Die tabellarische Datei wird mit einem eigenen fidelity-getesteten Excel-Editor bearbeitet, nicht unkontrolliert neu geschrieben.
5. Prüfen: Eingabe-/Ausgabe-Hash, erwartete Formeln und Struktur, Datenverlust, Dateiformat; Ergebnis privat nach R2 mit Provenienz und Freigabestatus; danach einmaliger signierter Download/Telegram-Hinweis.
6. Keine Veröffentlichung, kein Merge, kein unbegrenzter Modellverbrauch ohne vorherige Freigabe.

## Kosten- und Zugangsgrenzen

OpenCode ist Open Source, aber seine Modellanfragen sind nicht automatisch kostenlos. Die Modelle hinter OpenRouter, Google Nano Banana 2, Google Veo oder Claude können kostenpflichtig oder kontingentiert sein. Vor produktivem Test jeweils Preis/Quota prüfen, maximal ein kontrollierter Modellaufruf nach ausdrücklicher Freigabe; Rate-Limits und Circuit-Breaker. GitHub Actions laufen zeitlich begrenzt; R2 **führt keine Programme aus**. Bei Wechsel auf x86-VPS bleiben die S3-kompatiblen R2-Daten und GitHub-Memory erhalten.

## Nächste Handlung nur falls nötig

- Ein neuer Google-AI-Studio-Key ist **derzeit nicht nötig**, der bestehende funktioniert für die Google-Katalogabfrage einschließlich Nano-Banana-Einträge. Für tatsächliche kostenpflichtige Bildgenerierung bleibt Quota-/Billing-Prüfung ausstehend.
- Ein separater Anthropic-Key ist **optional**, wenn der nachgewiesene Claude-OpenRouter-Katalogweg mit vorhandenem Guthaben wirklich funktioniert. Ist direkte Anthropic-Abrechnung gewünscht, **nur Bülent** legt `ANTHROPIC_API_KEY` in GitHub Secrets an.
- Für den Dashboard-Zugang benötigt der separate PR #281 bei Aktivierung das Secret `AI_DASHBOARD_TOKEN` oder später einen geprüften Cloudflare-Access-Login; kein SSH-Passwort.


## Konkrete OpenCode-Skills auf diesem PR

Die im Quellcode versionierten Skills liegen in `.opencode/skills/`: `pdf-export`, `word-export`, `excel-export`, `media-processing` und `excel-safe-edit`. Die ersten vier haben Anweisungen für die bereits getesteten Werkzeuge. `excel-safe-edit` bleibt **absichtlich nicht automatisch aktiv**: Er beschreibt das noch nicht umgesetzte, originaltreue Bearbeiten eines hochgeladenen Workbooks.

Für einen strikt auf Claude begrenzten, nicht schreibenden Lauf existiert `infra/ai-central-tools/claude-only/opencode.jsonc`: ausschließlich OpenRouter ist als Anbieter erlaubt, der gewählte Modellpfad lautet `openrouter/anthropic/claude-sonnet-4.5`. Shell-Befehle, Dateiänderung, Subagenten und Web-Fetch sind in der Prüfstufe hart gesperrt. Der GitHub-Runner bestätigt Installation und statische Policy/Skill-Validierung; **kein kostenpflichtiger Claude-Modellaufruf oder echter XLSX-Edit wurde behauptet**.

Der aktuelle GitHub-Runner kann FFmpeg und FFprobe aus der Ubuntu-Paketquelle installieren; der separate tatsächliche Audio-/Video-Smoke-Test ist Teil des PR-Gates. Auch diese Installationen sind kurzlebig pro GitHub-Runner; R2 speichert nur Daten/Provenienz, keine laufenden Tools.
