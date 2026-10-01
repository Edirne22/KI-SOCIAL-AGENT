# Edirne 22 KI-Leitzentrale: gemeinsame Web-/Telegram-Vorschau

**Status:** Erstes verdrahtetes MVP auf gestapeltem Draft-PR #281, baut auf #277. Kein Produktions-Deploy, kein Auto-Publishing und kein autonomer Coding-Agent durch diese Änderung.

## Gemeinsame Datenquelle

- Vorhandener Telegram-Eingang `telegram_router.py` bleibt **einziger Telegram-getUpdates-Verbraucher**. Nur die expliziten Zusatzbefehle `/zentrale status`, `/zentrale hilfe`, `/zentrale auftrag <Text>` sind neu.
- Web und Telegram verwenden denselben privaten R2-Bucket und dieselbe Objektfamilie `ai-central/v1/inbox/YYYY-MM-DD/*.json`, Schema `AI-INBOX-V1`.
- Nachrichten und hochgeladene Dateien erhalten Status `DRAFT_REQUIRES_REVIEW` und `auto_dispatch=false`. Ein Entwurf bewirkt **keinen Modellaufruf**, keine GitHub-Aktion und keine Content-Freigabe.
- Telegram-Eingaben erhalten eine deterministische ID aus Chat/Update-ID, damit normale GitHub-Poller-Retries keine Duplikate erzeugen. Der vorhandene Telegram-Chat-ID-Check bleibt vorgelagert.
- Vorhandene Instagram-/MotoGP- und Freigabekommandos bleiben unangetastet. `content_factory_control_center.py` bleibt die spätere Grenze für echte Freigaben; dieser PR erweitert sie nicht.
- Web: passwortähnlicher privater API-Schlüssel, **nur im Tab-Speicher**, responsive Chat, bis zu 8 MB private Datei-/Audioaufnahme, gemeinsame Entwurfsliste und echte GitHub-Run-Zustände. Sprache wird zunächst als Audiodatei hochgeladen; **Transkription kommt später**. Status-Polling alle zehn Sekunden ist kein zeilengenaue Echtzeit-Konsole.
- API-Upload/Messaging sind gegen fremde Origins, nicht unterstützte Formate, übergroße Nutzlasten und offensichtliche Schlüssel im Nachrichtentext abgesichert. Hochgeladene Inhalte sind weiter untrusted; kein automatisches Weiterreichen an Modelle.

## Notwendige Konfiguration VOR privatem Live-Deploy

1. Prüfe, dass #277 vor #281 geprüft/übernommen ist. Stacked-PR #281 basiert auf dessen Branch, **nicht** auf dem OpenChatCut-Container.
2. Stelle sicher, dass `R2_BUCKET_NAME`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` als GitHub Secrets am richtigen Repo vorhanden sind. Die vorhandenen Live-Tests belegen R2-Schreibfunktion, nicht automatisch alle Cloudflare Worker-Berechtigungen.
3. **Neu erforderlich:** einen mindestens 24 Zeichen langen zufälligen `AI_DASHBOARD_TOKEN` in GitHub Actions Secrets anlegen. **Keinen** API-Key im Chat oder als GitHub Commit teilen. Dieser erste einpersonige Token ist ein MVP, noch kein Cloudflare Access/SSO.
4. Nach gesonderter Freigabe und Merge: GitHub Actions → `AI Central Dashboard – private manual Cloudflare deploy` → Run workflow. Das Deployment prüft vorher die Secrets und Worker-Tests, trägt den tatsächlichen Bucketnamen ein und setzt nach Deploy den privaten Worker Secret. Vor gesetztem Secret liefert die Dashboard-API HTTP 401. Worker Static Assets können technisch öffentlich abrufbar sein und enthalten keine internen Daten.
5. Telegram-Poller erhält die vier bestehenden R2-Secrets erst nach Merge dieser Änderungen. Es gibt **keinen zweiten Poller**, kein neues Telegram Bot Token und keine parallelen `getUpdates`-Konsumenten.
6. Danach mit falschem und richtigem Token testen: Status 401 vs. erfolgreiche Liste; im Browser eine harmlose Nachricht speichern und über `/zentrale status` sehen; `/zentrale auftrag Testauftrag` senden und im Dashboard kontrollieren. Keine sensiblen Testdaten.
7. Erst anschließend Aufgaben-Freigabeschicht, GitHub Dispatch, echte redigierte Log-/Code-Ereignisse und STT in getrennten PRs ergänzen. Keine Freigaben durch Chatmodell-Selbstauskunft.

## Grenzen und Ausweichlösung

R2 ist **Speicher, kein ausführender Server**. Die statischen Dateien sind mit geringem Aufwand auch über einen VPS bereitzustellen; die Worker-API ist zunächst ein Cloudflare-Adapter. Ein VPS kann später dieselben Endpunkte und das S3-kompatible R2-Schema nutzen. Dashboard- und Telegram-Prüfungen sind rein offline und dürfen die instabilen OpenChatCut-Container nicht starten. R2-Listings dieses ersten MVP zeigen die letzten Einträge innerhalb der aktuell ersten 100 Treffer; für größeren Dauerbetrieb braucht es einen paginierten oder indexierten Verlauf.
