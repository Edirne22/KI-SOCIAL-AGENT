# Gemini Inventar & Migrationsanalyse

Dieses Dokument erfasst alle Vorkommen von Gemini API-Aufrufen, Konfigurationen und `GEMINI_API_KEY`-Verwendungen im Repository `Edirne22/KI-SOCIAL-AGENT` (Stand: September 2026) zur Vorbereitung der Umstellung auf Agnes AI (`AGNES_API_KEY`).

---

## 1. Inventar-Tabelle

| Datei | Zeile | Modell | Retry | Produktiv? | Agnes-Äquivalent vorhanden? |
|---|---|---|---|---|---|
| `scripts/update_race_calendar.py` | 14, 18, 54 | `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash` | Model-Fallback-Schleife über Modellliste bei Fehlern (Timeout 120s) | **Ja** (Workflow `race-calendar-update.yml` läuft scheduled auf main; aktuell rot wegen HTTP 429 Rate Limit) | **Ja** (`agnes-2.5-flash` via API / Router) |
| `follow_analyzer.py` | 281, 295 | `gemini-3.8-flash` | Explizite Retry-Schleife: 3 Versuche mit Delays 30s, 60s, 120s | **Ja** (Workflow `follow-analyzer.yml` läuft täglich auf main) | **Ja** (Agnes Chat Completion via Router) |
| `search_provider.py` | 16, 17, 422 | `gemini-3.8-flash` | Kein Retry Loop; Fallback von Grounded Search auf Knowledge Base | **Ja** (Teil der MotoGP/Search Pipeline) | **Teilweise** (Agnes Text-LLM vorhanden, Web-Grounding erfordert Tavily / SearXNG / DuckDuckGo Provider) |
| `weekly_plan.py` | 5, 15, 24 | `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite` | Model-Fallback-Schleife über 5 Modelle bei Fehlern | **Ja** (Workflow `weekly-plan.yml` auf main) | **Ja** (Router-Task `weekly_plan` in `model_router.json`) |
| `ride_with_me.py` | 4, 10, 22 | `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite` | Model-Fallback-Schleife über 5 Modelle bei Fehlern | **Ja** (Workflow `ride-with-me-analysis.yml` auf main) | **Ja** (Router-Task `ride_with_me` in `model_router.json`) |
| `generate_ideas.py` | 10, 33, 53 | `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite` | Model-Fallback-Schleife über 5 Modelle bei Fehlern | **Ja** (Workflow `daily-ideas.yml` auf main) | **Ja** (Router-Task `content_ideas` in `model_router.json`) |
| `fetch_stock_photo.py` | 8, 13–15, 177, 277 | `gemini-3-pro-image`, `gemini-3.1-flash-image`, `gemini-3.1-flash-lite-image` | Model-Fallback-Schleife über 3 Bildmodelle | **Ja** (Workflow `fetch-stock-photo.yml` auf main) | **Ja** (`generate_agnes_media.py` / `agnes_generate_image` mit `agnes-image-2.1-flash`) |
| `race/poster_generator.py` | 18, 43, 54 | `gemini-3.1-flash-image` | Kein Retry Loop (einzelner HTTP Request, Timeout 120s) | **Ja** (Race Poster Generierung) | **Ja** (`agnes-image-2.1-flash` via `generate_agnes_media.py`) |
| `race/poster_style.py` | 15, 24, 36 | `gemini-3.8-flash` | Kein Retry Loop (einzelner HTTP Request) | **Ja** (Race Poster Stil-Analyse) | **Ja** (`agnes-2.5-flash` Text) |
| `inspiration/orchestrator.py` | 20, 174 | `gemini-3.8-flash` | Explizite Retry-Schleife in `_gemini_with_retry` mit Debug-Logging | **Ja** (Workflow `inspiration-agent.yml` auf main) | **Ja** (Agnes Text Completion) |
| `llm_client.py` | 50, 54, 65 | Dynamisch via Router (`base_url` + Model Name) | Retry wird vom Aufrufer gesteuert; Timeout 120s | **Ja** (Zentraler LLM Router Client) | **Ja** (`llm_client.py` unterstützt bereits `_generate_agnes_text`, `_generate_agnes_image`, `_start_agnes_video`) |
| `config/model_router.json` | 6, 7, 8 | Config Definition `gemini` (`gemini-3.8-flash` bis `3.5-flash`) | Timeout-Konfiguration (`timeout_seconds: 120`) | **Ja** (Zentrale Router-Konfiguration) | **Ja** (`"agnes"` ist in `model_router.json` bereits als Provider konfiguriert) |

---

## 2. Migrationsreihenfolge & Empfehlungen

Um eine unterbrechungsfreie Migration von Gemini auf Agnes AI durchzuführen, wird folgende Reihenfolge empfohlen:

### Phase 1: Router-basierte Skripte umstellen (Geringstes Risiko)
1. **`config/model_router.json` & Router-Tasks**:
   - Die Router-Tasks `content_ideas`, `research`, `translation_de_tr`, `weekly_plan`, `ride_with_me` und `quality_check` in `model_router.json` von `"provider": "gemini"` auf `"provider": "agnes"` umstellen.
   - **Vorteil**: Keine Codeänderungen in Skripten erforderlich (`generate_ideas.py`, `weekly_plan.py`, `ride_with_me.py` nutzen bereits bzw. lassen sich direkt über `llm_client.py` leiten).

### Phase 2: Akut blockierte & fehlerhafte Direct-Gemini-Skripte umstellen
2. **`scripts/update_race_calendar.py`**:
   - **Status**: Aktuell rot in Production wegen HTTP 429 Rate Limit (Gemini Quota exhaustion).
   - **Aktion**: Direkt auf `agnes-2.5-flash` oder lokalen JSON/RACE_CALENDAR Fallback umstellen.
3. **`follow_analyzer.py`**:
   - **Status**: Verwendet eigene Retry-Logik (30/60/120s) auf Gemini.
   - **Aktion**: API-Call auf Agnes Chat-Completions Endpoint (`https://apihub.agnes-ai.com/v1/chat/completions`) mit Modell `agnes-2.5-flash` anpassen.
4. **`inspiration/orchestrator.py`**:
   - **Status**: Direkter Request an Gemini Endpoint.
   - **Aktion**: Umstellen auf Agnes Chat Endpoint.

### Phase 3: Bildgenerierung umstellen
5. **`fetch_stock_photo.py` & `race/poster_generator.py`**:
   - **Status**: Nutzen Gemini Bildmodelle (`gemini-3.1-flash-image`).
   - **Aktion**: Umstellen auf `agnes-image-2.1-flash` via `generate_agnes_media.py` / Agnes Image Generation Endpoint.
6. **`race/poster_style.py`**:
   - **Status**: Nutzt Gemini für Prompterstellung.
   - **Aktion**: Umstellung auf `agnes-2.5-flash`.

### Phase 4: Spezialfälle & Bereinigung
7. **`search_provider.py`**:
   - **Status**: Nutzt Google Grounding / Gemini 3.8 Flash.
   - **Aktion**: Gemini Grounding durch Tavily / DuckDuckGo Search Provider + Agnes Synth-LLM ersetzen.
8. **Workflows & Secrets**:
   - Nach erfolgreicher Migration aller Skripte `GEMINI_API_KEY` aus GitHub Workflows entfernen.
