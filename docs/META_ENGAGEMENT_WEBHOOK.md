# Meta Engagement Webhook

## Zweck
HTTPS-Eingang für zulässig empfangene Instagram-/Facebook-Kommentarereignisse. Der Adapter prüft die Webhook-Verifikation und `X-Hub-Signature-256`, schreibt nur normalisierte Events in die Inbox und sendet selbst nichts.

## Erforderliche Secrets auf dem späteren HTTPS-Host
- `META_WEBHOOK_VERIFY_TOKEN`
- `META_APP_SECRET`

Die vorhandenen Instagram-/Facebook-Tokens bleiben getrennt. Secrets werden nicht im Repository gespeichert.

## Datenfluss
Meta HTTPS Webhook → Signaturprüfung → `memory/META_ENGAGEMENT_INBOX.jsonl` → `meta_engagement_dispatch.py` → Instagram/Facebook Engagement Queue → Telegram-Freigabe → späterer Reply-Adapter.

## Deployment
GitHub Actions ist kein dauerhaft erreichbarer Webhook-Server. Der Endpoint muss auf dem vorhandenen VPS bzw. einem anderen dauerhaft erreichbaren HTTPS-Dienst laufen. Vor Live-Schaltung müssen die aktuell für die Meta-App verfügbaren Webhook-Felder/Berechtigungen im Meta Developer Dashboard bestätigt werden.

## Fail-closed
Fehlendes App-Secret, falsche Signatur, falsches Verify-Token und ungültiges JSON werden abgewiesen. Der Webhook veröffentlicht nichts und startet keinen Publisher.
