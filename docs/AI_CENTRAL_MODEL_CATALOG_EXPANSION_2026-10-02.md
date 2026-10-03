# KI-Zentrale – Modellkatalog-Erweiterung: inaktive Vorbereitung

**Vorbereitung:** 02.10.2026. **Status:** `RESEARCH_ONLY / NO_RUNTIME_CHANGE`; keine Modell-Inferenz, neuen Schlüssel, Installation, Deployment, geänderten Router oder Freigabe. Diese Datei ist ein vertiefender Kandidatenvergleich; **einziger maßgeblicher Funktions-/Werkzeugindex bleibt `docs/TOOL_INDEX.md`**. Vor Umsetzung aktuellen `main`, `MASTER-SNAPSHOT.md` und `PROJECT_GUARDRAILS.md` erneut lesen.

## 1. Vorhandene Mannschaft – nicht duplizieren

| Bestehender Weg | Nachweis/Stand | Grenze |
| --- | --- | --- |
| NVIDIA `nvidia/nemotron-3.5-lightning-30b-a3b` | Bereits `--free-team`-Live-Rechercheantwort im historischen Run [36903543954](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/36903543954); genauen aktuellen Endpunkt/Account vor neuer Probe neu prüfen. | Existierende erfolgreiche Antwort ≠ unbegrenzte freie Nutzung. |
| NVIDIA `moonshotai/kimi-k3` | Bereits echte Diagnoseantwort im selben Run. | Separater Modellname/Anbieter innerhalb NVIDIA; keine zweite Kimi-Installation. |
| OpenRouter `openrouter/free` | Bestehender Free-Team-Gegenprüfungsweg, im historischen 3er-Lauf **UNAVAILABLE**. | Keine automatische Annahme unabhängiger oder verfügbarer Modellidentität ohne `reported_model`. |
| Google Gemini | `GEMINI_API_KEY` war in Secret-Existenzinventur vom 01.10. vorhanden; `config/llm_providers.json` hat konfigurierten Google-Adapter. | Einzelmodell, tatsächliche kostenlose persönliche Quota, aktuelle Antwort und 429-/Retry-Verhalten separat testen. |
| Groq | `GROQ_API_KEY` in historischer Secret-Inventur vorhanden; eigener vorhandener Groq-Adapter. | **Groq ist Inferenzanbieter, nicht Grok.** Gemini/Groq sind noch keine belegten 3/3-Free-Team-Live-Kandidaten. |
| Grok/xAI | Im bisherigen Leitbild erwähnt, im aktuell geprüften `config/llm_providers.json` **kein eigener nachgewiesener xAI-Adapter/Key**. | Keine Aktivierung/0-€-Annahme. Vorher technisch und tariflich gesondert neu prüfen. |
| Cloudflare Workers AI | In bestehendem `llm_providers.json` vorkonfiguriert. | Konto-Neuronen und geeignete Aufgaben/Modelle/Verfügbarkeit kontrollieren; R2 allein ist keine Inferenz. |
| Claude über OpenRouter | Separate bereits nachgewiesene kleine echte Claude-Probe laut `docs/AI_CENTRAL_VERIFIED_PROVIDER_SKILL_AUDIT.md`, bestehende `claude_only`-Route. | Potenziell kostenpflichtig, ausdrücklich **nicht** in automatisch kostenloses Modellteam übernehmen. |

**Wichtig:** Konfiguration, Inventur, getestete Modellantwort und volle produktive E2E-Abnahme sind vier verschiedene Evidenzstufen. Kein Umschalten des bisherigen `--free-only`-Produktionswegs durch dieses Dokument. OmniRoute bleibt `PAUSED`; Selora nicht integrieren.

## 2. NVIDIA: nach Aufgaben kuratierte RESEARCH_ONLY-Modelle

Dies ist eine **begrenzte Kandidatenliste, kein vollständig paginierter NVIDIA-Gesamtkatalog**. Die Originalseiten zeigen das jeweilige Modell bzw. geben Katalogkategorien an; Bezeichnung `Free Endpoint`/Downloadable ist **weder accountbezogene Gratisgarantie noch Freibrief zum Selbsthosting**. Vor genau einem API-Probelauf ID auf aktueller NVIDIA-API-Referenz, Nutzungsbedingungen, API-Kontingent, Quoten, individuelle Modell-Berechtigung und tatsächlichen Antwortnamen neu prüfen.

| Funktion im bestehenden Agententeam | Prüfkandidat, offizielle Quelle | Abgrenzung zum vorhandenen Team und Prüfhürde |
| --- | --- | --- |
| Schnelle Recherche/Agenten | **Nemotron 3.5 Lightning** – https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b | **Bestehend und historisch echt getestet**; als Basis/Benchmark, nicht als Neuerwerb. |
| Diagnose/langes Denken und Multimodalität | **Kimi K3** – https://build.nvidia.com/moonshotai/kimi-k3 | **Bestehend und historisch echt getestet**. Bildverständnis nur nach eigener erlaubter Input-/Rechtemessung annehmen. |
| Langer technischer Kontext | **Nemotron 3 Super 120B** – https://build.nvidia.com/models?api-key=true&label=reasoning%2CLong+Context%2CMoE | Potenzieller unabhängiger Vergleich für lange Fehler-Logs und große Quellpakete. API-only; kein 120B-Container auf unserer CPU-Werkbank. |
| Langes Planen/Coding | **Nemotron 3 Ultra 550B** – https://build.nvidia.com/models?label=Chat | Forschungs- und Kostenkandidat, nur falls Super/Lightning im konkreten Test die Aufgabe nicht lösen. Keine Massentests. |
| Coding/Tool-Nutzung | **GLM-5.2** bzw. aktueller Katalog-Codingkandidat – https://build.nvidia.com/models?api-key=true&label=coding | Kandidat für isolierte Code-Reviews, niemals selbstständig pushen oder sensible Repository-Daten an unfreigegebene Anbieter weitergeben. Exakte API-ID/aktuellen Verfügbarkeitsstatus vor Test erneut auflösen. |
| Coding/Gegenvergleich | **MiniMax M3** – https://build.nvidia.com/models?api-key=true&label=coding | Schon als `minimaxai/minimax-m3` im Provider-Config erwähnt, deshalb nicht als neue Integration behaupten. Kein redundanter Modellruf ohne Mehrwertmessung. |
| Foto/Screenshot-Vision | **Muse Glimmer 30B** – https://build.nvidia.com/models?label=Chat | Nur geeignete, erlaubte Testbilder; Text/Bild-Qualität gegen bestehendes `vision_router.py` vergleichen. |
| Video-/Audio-/Bildverständnis | **Nemotron 3 Nano Omni** – https://build.nvidia.com/models?label=Chat | Recherche für späteren realen Medienabdeckungsnachweis: *Datei tatsächlich analysiert* ≠ Videotitel entdeckt. Format-/Input-/Token-/Kostenhürden vorher klären. |
| OCR aus Screenshots/Dokumenten | Bereits konfiguriertes **Nemotron OCR V2** – Modell-ID `nvidia/nemotron-ocr-v2` im existierenden Provider-Config | Erst vorhandenen `vision_router.py` und tatsächliche Berechtigung testen; keinen zweiten OCR-Agenten installieren. |

Die aktuell separat erfassten Google-/Groq-/Cloudflare-Kandidaten stammen aus dem vorhandenen Repo, **nicht** aus verifizierten NVIDIA-Free-Tier-Preisen. Nur bestehende bereits freigegebene Dienste als Transport erwägen.

## 3. Das künftige Team arbeitet nach Funktionen, nicht nach Modellzahl

1. **Recherche/Story:** bestehende Quellen-Discovery, Apify- und Source-Fact-Contract; kleines schnelles Modell für Extraktion; ein unabhängiger LLM-Gegenprüfer nur bei konkreter Evidenzlücke. Ein LLM-Zitat ist keine Quellenbestätigung.
2. **Programmierung:** vorhandene GitHub-/OpenCode-Werkzeuge; zusätzliche API-Codingmodelle zunächst nur in read-only isolierten Prüfungen, gemessener Testqualität/Tokenverbrauch.
3. **Foto/Video/OCR:** zuerst bestehende ImageRouter, `vision_router.py`, FFmpeg und real vorhandene Dateien; spezialisierte Multimodalmodelle nur wenn tatsächlich zusätzlicher Erkennungsnutzen und Nutzungsrechte erwiesen.
4. **DE/TR-Stimme/Transkripte:** Block7 faster-whisper und Chatterbox Multilingual auf ihrem **eigenen** Live-Testpfad; keine Vermischung mit NVIDIA-Modellkatalog. Privater Konsens-/Widerrufspfad vor echten Besitzeraufnahmen.
5. **Qualitäts-QM:** deterministische Fahrer-, Zahl-, Serien-, Quellen- und Medien-Checks zuerst; LLM als unabhängige ergänzende Prüfung, **kein** LLM darf einen UNSUPPORTED-Claim selbst auf VERIFIED hochstufen.
6. **Ressourcenmanager:** kürzester geeigneter bestehender modellunabhängiger Transport mit fehlertolerantem Fallback, Obergrenzen pro Task/Tag und gemessener Token-/Latenz-/Speicherkosten; kein Modellfan-out zum bloßen Selbstzweck.

## 4. Prüf- und Aktivierungsmatrix (nur später nach Block8/9-Sicherheitsgates)

Für **jedes** neue Modell exakt eine standardisierte Zeile anlegen mit: `provider`, `exact_model_id`, offiziellem Link, Lizenz/Modellnutzungsrecht, geplanter Funktion, benötigtem Endpoint und Auth-Secret-**Namen** (nie Wert), nachgeprüftem Konto-Freitier und Verbrauchsgrenze, maximalem Anfrageumfang, Kontextfenster/Modalitäten **laut aktueller Originalquelle**, `reported_model` vom echten Response, Prompt-/Input-Datenklasse, Rate-Limit-Verhalten (429/529/Timeout), vorhandener sicherer Fallback, Test-Run-ID, Ergebnis `PASS|FAIL|UNAVAILABLE|DEGRADED`, CI-Negativtest und konkreter Vorteil gegenüber bestehender Route. Fehlende Angaben bleiben `UNVERIFIED`; keine geschätzten Preise als Fakten.

**Vorgeschlagene Vergleichsaufträge:** a) öffentlich/synthetisches MotoGP-Quellenpaket mit absichtlich gefälschter Zahl/Teamzuordnung und eindeutiger Quellenbelegung; b) gekürztes öffentliches Python-Fehlerlog mit reproduzierbarem Offline-Test, ohne Secrets; c) eigenes autorisiertes synthetisches DE/TR-Bild-/Transkript-Beispiel. Gemessen wird richtige Evidenzbindung, falsche Fakten erkannt, keine Prompt-Injection-Ausführung, brauchbare Fehlerdiagnose, Latenz und Tokenverbrauch. Gleiche Inputs/akzeptierte Ausgaben für Basismodell und höchstens einen neuen Kandidaten je Task; keine Blindläufe oder neue Kosten.

**Aktivierungsgates:** dokumentiertes persönliches 0-€-Kontingent und Modellrechte → genau eine begrenzte öffentliche/synthetische reale Probe auf vorhandener Umgebung → separate Positiv-, Red-Team- und Regressionstests → nur opt-in in bestehenden Provideradapter (kein neuer allgemeiner Router) → tatsächlicher privater Dashboard/R2/Telegram-E2E-Bericht mit korrektem `reported_model` und nachweisbarem Fallback → geprüfter PR und ausdrücklich vereinbarte Freigabe. **Bis dahin ausschließlich Dokumentation, keine Runtime-Effekte.**

## 5. Quellen und Aktualität

- Interner Plan: `docs/PROJEKT_UEBERGABE_6_2026-10-01_KI_UNTERNEHMEN.md`; historisches Inventar `docs/AI_CENTRAL_VERIFIED_PROVIDER_SKILL_AUDIT.md`; bestehende `scripts/cloud_ai_central.py`, `config/llm_providers.json`; zentral `docs/TOOL_INDEX.md`.
- Offizieller NVIDIA-Katalog: https://build.nvidia.com/models?page=1 ; Coding-Filter: https://build.nvidia.com/models?api-key=true&label=coding ; offizielle NVIDIA NIM API: https://docs.api.nvidia.com/nim/reference/llm-apis ; self-host/licensing overview: https://docs.api.nvidia.com/nim/re/docs/overview .
- **Achtung:** Katalogfilter und Modelllisten sind zeitvariabel; dieser Text beschreibt gesichtete Kandidaten zum angegebenen Stand und erhebt keinerlei Vollständigkeitsanspruch. Downloadbare NVIDIA-NIM-Container können gesonderte Enterprise-Lizenz- oder GPU-Voraussetzungen haben. Private Auftragsdaten dürfen nicht an einen noch ungeprüften Kandidaten übertragen werden.
