# KI-Zentrale: NVIDIA / OmniRoute / Telegram – kontrollierte Integrationsstufe 1

**Status:** Entwicklungs-PR, nicht deployed, nicht produktiv freigeschaltet.

## Verbindliche Regeln
Vor Integration `PROJECT_GUARDRAILS.md` und neuesten `MASTER-SNAPSHOT.md` lesen. Keine bezahlten Modelle, kein Auto-Merge, keine Veröffentlichung, keine öffentlichen privaten Auftragsdaten. Live-Ergebnis zählt erst bei tatsächlich erfolgreichem GitHub-Job samt überprüfter Providerantwort.

## Umfang von Stufe 1
- Getrennte `--free-team`-Route: dokumentierte NVIDIA-Build-**Free Endpoint**-IDs `nvidia/nemotron-3.5-lightning-30b-a3b`, `moonshotai/kimi-k3`, plus ausschließlich `openrouter/free`; zwei unabhängige Rollen Research und Diagnosis. Danach erhält Challenge deren strikt als UNVERIFIED markierte, begrenzte Antworten zur unabhängigen Widerspruchsprüfung. Kein Claude/Anthropic-Fallback. Fehler eines NVIDIA-Endpunkts darf nur zur vorhandenen verifizierten Free-Route weitergeleitet werden.
- Fail-closed: explizite `AI_NVIDIA_DEVELOPER_FREE_VERIFIED=true` und `AI_CENTRAL_FREE_TIER_VERIFIED=true`, beide existierende Keys, exakte Anbieter-URLs und feste Modellnamen; kostenpflichtige Alias-Modellauswahl ausgeschlossen. Free-Endpunkt-Katalog ist **keine Garantie** für unbegrenzte persönliche Quoten. Katalogverweise: https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b und https://build.nvidia.com/moonshotai/kimi-k3.
- Neue isolierte `AI Central – NVIDIA free team and OmniRoute integration gate`-Action: PR-Offlineverträge ohne Anbieter-Schlüssel. Der sehr schwere OmniRoute-3.8.50-Serverstart ist als eigener, nur manuell aufrufbarer Machbarkeitstest getrennt; bisherige echte Runner-Versuche erreichten keinen antwortenden Modellkatalog. Die reine CLI-Installation ist historisch nachgewiesen, aber kein Runtime-LIVE-Beleg. Der echte Free-Team-Modellaufruf läuft ausschließlich nach **manuellem** `workflow_dispatch` auf `main`, mit fest eingebautem öffentlich bekanntem synthetischen OpenChatCut-Task. Keine privaten R2-Berichte oder Modellantworten in öffentlichen Actions-Artefakten.
- Telegram: bestehender einzige Poller und dessen Zugangskontrolle unverändert; neuer Befehl `/zentrale ergebnis <ID>` ruft streng auf ID gebundenen R2-Laufstatus ab und zeigt nur Rolle/Status/Run-ID, keine privaten Antworttexte. Nutzer öffnet für vollen Bericht das bereits geschützte Dashboard.

## Noch nicht fertig und gesondert abzunehmen
- Echter NVIDIA-Free-Team-Lauf mit tatsächlichen drei Providerantworten und `reported_model` überprüfen.
- OmniRoute-Stufe 1 beweist **nur** Installation/Start/Katalog einer kurzlebigen GitHub-Instanz, **nicht** dauerhaft laufenden Gateway-Dienst oder echte angemeldete NVIDIA-/Gemini-/Groq-Anbieterverbindungen. Diese benötigen eigene, gesichert gebootstrappte Konfiguration, Kostenrichtlinie und Reifeprüfung; niemals nur aufgrund CLI-Version als fertig melden.
- Der produktive `ai-central-inbox-agent.yml` bleibt aus Gründen des kostenkontrollierten Rollbacks unverändert auf `--free-only`. Nach dokumentiertem Team-Probe-PASS gesonderter PR für sichere Wahl Free-Team, Dashboard/Telegram-Start und tatsächlichen E2E-R2-Bericht. Claude nur bei nachgewiesen freier Route oder ausdrücklicher Kostenfreigabe.
- Echte Telegram-Ergebnis-Abnahme über den bestehenden Poller und reale R2-Daten steht bis nach geprüftem Merge aus.
- Block 6/OpenChatCut: PR #271/#278 als nächstes diagnostisch weiterprüfen, bevor irgendein Container-Image-Rollout stattfindet.

## Kontrollsequenz
1. Pull-Request-CI: Python-Syntax sowie vorhandene und neue Telegram-/Free-Team-Regressions-, Angriffs- und Positivtests. OmniRoute-Server ist derzeit separat MANUELL und muss ausdrücklich als offener Blocker bezeichnet bleiben, solange keine echte Antwort vom Gateway vorliegt.
2. Nur nach ausdrücklicher Merge-Freigabe und grünem CI auf main: separaten manuellen Free-Team-Live-Workflow sowie unabhängig davon den OmniRoute-Feasibility-Job starten; tatsächliche Modellnamen, 3 Rollen und Ausfall-/Fallbackstatus anhand Logs prüfen.
3. Produktionsanbindung erst nach eigener E2E-/Human-Authority- und Retry-/Idempotenzprüfung.
