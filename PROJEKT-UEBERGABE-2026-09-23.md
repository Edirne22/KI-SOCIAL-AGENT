# PROJEKT-ÜBERGABE – Engagement Agents & Meta Webhook

**Stand:** 23.09.2026, 20:39 UTC  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`  
**Zweck:** Verlustfreie Übergabe des aktuellen Entwicklungsstands aus dem Chat. Dieses Dokument ergänzt `MASTER-SNAPSHOT.md`; offene PRs sind noch nicht automatisch Bestandteil von `main`.

## 1. Zielbild

Instagram- und Facebook-Interaktionen sollen über offizielle Meta-Schnittstellen empfangen, klassifiziert und mit dem bestehenden Memory-System verknüpft werden. Antwortvorschläge werden über den vorhandenen Telegram-Bot kontrolliert. Bülent entscheidet. V1 sendet keine Engagement-Antwort selbstständig.

Datenfluss:

```
Meta Webhook
    ↓
Signaturprüfung + Normalisierung
    ↓
Instagram Agent 17 / Facebook Agent 18
    ↓
Community Memory + Queue
    ↓
bestehender Telegram-Router
    ↓
antwort / ändern / ignorieren / info / memory
    ↓
SEND_APPROVED
    ↓
späterer separater Meta Reply-Adapter
```

## 2. Agent 17 – Instagram Engagement

**Branch:** `feature/instagram-engagement-agent`  
**Draft-PR:** #65 – Integrate Instagram Engagement Agent with Telegram

Vorhanden/gebaut:
- `agents/17_instagram_engagement_agent.md`
- `instagram_engagement.py`
- `test_instagram_engagement.py`
- `memory/INSTAGRAM_COMMUNITY.md`
- Integration in `telegram_router.py`

Funktionen:
- Klassifikation: `FRAGE`, `LOB`, `KRITIK`, `TRIGGER`, `SPAM`, `UNSICHER`.
- Deduplizierung nach Event-ID.
- Deterministische Ticket-ID `IG-XXXXXXXX`.
- Community-Memory speichert nur belegbare öffentliche Interaktionsmetadaten.
- Keine Identifikation/Schätzung stiller Profil- oder Post-Besucher.
- Keine sensiblen Eigenschaften ableiten.
- Keine privaten Chat-Inhalte dauerhaft ins Community-Memory übernehmen.

Telegram-Kommandos:
- `antwort IG-XXXXXXXX` – vorhandenen Entwurf freigeben.
- `ändern IG-XXXXXXXX <Text>` – Text ersetzen und freigeben.
- `ignorieren IG-XXXXXXXX` – schließen, nichts senden.
- `info IG-XXXXXXXX` – Eventdetails.
- `memory IG-XXXXXXXX` – belegbare öffentliche Interaktionshistorie.

**Wichtig:** `antwort` und `ändern` setzen aktuell nur `SEND_APPROVED`. Es gibt noch keinen automatischen Instagram-Reply.

## 3. Agent 18 – Facebook Engagement

**Branch:** `feature/facebook-engagement-agent`  
**Draft-PR:** #64 – Add Facebook Engagement Agent V1 with Community Memory

Gebaut:
- `agents/18_facebook_engagement_agent.md`
- `facebook_engagement.py`
- `test_facebook_engagement.py`
- `memory/FACEBOOK_COMMUNITY.md`
- `docs/FACEBOOK_ENGAGEMENT_TELEGRAM.md`
- Ergänzung der `rules/SAFETY_RULES.md`

Logik entspricht Agent 17 mit Ticket-ID `FB-XXXXXXXX`.

Telegram-Kommandos:
`antwort`, `ändern`, `ignorieren`, `info`, `memory`.

Auch hier bedeutet Freigabe in V1 ausschließlich `SEND_APPROVED`; kein automatischer Facebook-Reply.

## 4. Gemeinsamer Meta-Webhook

**Branch:** `feature/meta-engagement-webhook`  
**Draft-PR:** #66 – Add Meta engagement webhook foundation

Gebaut:
- `meta_engagement_webhook.py`
- `meta_engagement_dispatch.py`
- `test_meta_engagement_webhook.py`
- `docs/META_ENGAGEMENT_WEBHOOK.md`

Sicherheits-/Transportlogik:
- GET-Verifikation mit `META_WEBHOOK_VERIFY_TOKEN`.
- POST-Prüfung von `X-Hub-Signature-256` mit `META_APP_SECRET`.
- Fail-closed bei fehlendem Secret, falscher Signatur, falschem Verify-Token oder ungültigem JSON.
- Unterstützte Kommentarereignisse werden normalisiert.
- Gemeinsame Inbox: `memory/META_ENGAGEMENT_INBOX.jsonl`.
- Dispatcher leitet Instagram-Events an `instagram_engagement` und Facebook-Events an `facebook_engagement` weiter.
- Webhook veröffentlicht selbst nichts und startet keinen Publisher.

## 5. Bestehendes System, das weiterverwendet wird

Der vorhandene `telegram_router.py` ist der zentrale Telegram-Poller. Der bestehende Workflow `.github/workflows/telegram-receive.yml` startet ihn im Zeitplan. Es wird kein zweiter Telegram-Bot aufgebaut.

Das bestehende Closed-Loop-Memory aus Agent 14 bleibt die übergeordnete Lernarchitektur. Die neuen Community-Memories sollen belegbare Engagement-Signale liefern; einzelne sichtbare Interaktionen dürfen nicht als weitreichende Nutzerpräferenz oder sensible Eigenschaft interpretiert werden.

## 6. Aktueller Integrationsstatus / Grenzen

- Die drei Arbeiten liegen in separaten Draft-PRs und sind **nicht automatisch gemergt**.
- Kein Publisher wurde für diese Arbeiten gestartet.
- Keine Secrets wurden durch den Agenten angelegt.
- Der Meta-Webhook ist **noch nicht live erreichbar**.
- GitHub Actions ist kein dauerhafter HTTPS-Webhook-Server.
- Der vorhandene VPS/OmniRoute-Server ist als naheliegender Deployment-Ort vorgesehen, wurde aber noch nicht verändert.
- Für das Deployment fehlen in diesem Chat direkte SSH-/VPS-Werkzeuge.

## 7. Erforderliche Secrets für den Live-Webhook

Auf dem späteren HTTPS-Host:
- `META_WEBHOOK_VERIFY_TOKEN`
- `META_APP_SECRET`

Bestehende Plattform-Tokens bleiben getrennt. Keine Secret-Werte in Git, Logs, Dokumentation oder Chat kopieren.

## 8. Nächste Schritte in richtiger Reihenfolge

1. PR #64 und #65 auf Konflikte/Tests prüfen und kontrolliert zusammenführen; kein Auto-Merge.
2. PR #66 danach auf den zusammengeführten Stand bringen, weil der Dispatcher beide Engagement-Module benötigt.
3. Webhook auf dem vorhandenen VPS als dauerhaften Dienst hinter HTTPS deployen.
4. Meta Developer App mit der öffentlichen Callback-URL verbinden und die tatsächlich verfügbaren aktuellen Webhook-Felder/Berechtigungen bestätigen.
5. Erst danach einen separaten Reply-Adapter bauen, der ausschließlich `SEND_APPROVED`-Tickets sendet; vor Live-Senden End-to-End-Test mit Testkommentar und Telegram-Freigabe.

## 9. Nicht vergessen

Der aktuelle Stand ist bewusst Human-in-the-Loop:

> **Meta empfängt → Agent bewertet → Memory dokumentiert → Telegram fragt → Bülent entscheidet.**

Kein stiller Besucher wird erfunden. Kein Engagement wird automatisch ausgelöst. Kein Reply-Adapter darf die vorhandene Freigabe umgehen.
