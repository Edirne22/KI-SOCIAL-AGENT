**Übergangslösung (aktuell):** GitHub-Actions-Polling alle 3 Std statt Webhook.

---

## 2. Agent 17 – Instagram Engagement

**Status:** ✅ aktiv (24.09.2026)

### Dateien
- `agents/17_instagram_engagement_agent.md`
- `instagram_engagement.py`
- `test_instagram_engagement.py`
- `memory/INSTAGRAM_COMMUNITY.md`
- Integration in `telegram_router.py`

### Funktionen
- Klassifikation: `FRAGE`, `LOB`, `KRITIK`, `TRIGGER`, `SPAM`, `UNSICHER`
- Dedupe nach Event-ID
- Deterministische Ticket-ID `IG-XXXXXXXX`
- Community-Memory speichert nur belegbare öffentliche Interaktionsmetadaten
- Keine Identifikation stiller Profil-/Post-Besucher
- Keine sensiblen Eigenschaften ableiten
- Keine privaten Chat-Inhalte dauerhaft ins Memory

### Telegram-Kommandos
- `antwort IG-XXXXXXXX` – vorhandenen Entwurf freigeben
- `ändern IG-XXXXXXXX <Text>` – Text ersetzen und freigeben
- `ignorieren IG-XXXXXXXX` – schließen, nichts senden
- `info IG-XXXXXXXX` – Eventdetails
- `memory IG-XXXXXXXX` – belegbare öffentliche Interaktionshistorie

### Polling
- Workflow: `meta-engagement-poll.yml` (oder analog)
- Cron: alle 3 Std (17 */3 * * *)
- First-Run-Schutz: `memory/META_ENGAGEMENT_POLL_INITIALIZED`
- Aktuell: max 50 Medien, 100 Kommentare pro Medium (Übergang)

---

## 3. Instagram Reply Adapter (PR #72, gemergt)

**Status:** ✅ auf main seit 24.09.2026

### Dateien
- `instagram_reply_adapter.py`
- Änderungen in `instagram_engagement.py`
- `test_instagram_engagement.py` (erweitert)

### Funktion
- `send_reply(comment_id, message)` → sendet via Instagram Graph API
- Nur nach expliziter Telegram-Freigabe
- SENT-Zustand terminal (kein Doppel-Senden)
- `reply_id` und `sent_at` werden gespeichert

### Sicherheit
- Kein automatischer Retry ohne Freigabe
- Bei API-Fehler: `SEND_APPROVED` bleibt erhalten + Telegram-Fehler
- 429-Cooldown (Retry-After, sonst 60 Sek)
- Provider-Fallback Agnes → Gemini → NVIDIA
- Fail-closed wenn alle Provider down

### Test-Workflow (PR #73, gemergt)
- `.github/workflows/instagram-reply-adapter-test.yml`
- Gemockter Unit-Test (kein echter Instagram-Reply)
- Status: SUCCESS

---

## 4. Agent 18 – Facebook Engagement

**Status:** ⏸️ pausiert (PR #71, 24.09.2026)

### Dateien
- `agents/18_facebook_engagement_agent.md`
- `facebook_engagement.py`
- `test_facebook_engagement.py`
- `memory/FACEBOOK_COMMUNITY.md`
- `docs/FACEBOOK_ENGAGEMENT_TELEGRAM.md`

### Logik
Entspricht Agent 17 mit Ticket-ID `FB-XXXXXXXX`.

### Problem
- Fehler `(#10) pages_read_engagement` trotz gesetztem Token
- Verdacht: Page-Token vs. User-Token, Scopes, App-Modus
- `ENABLE_FACEBOOK_ENGAGEMENT=false` (Default)

### Aktivierung (später)
1. Graph API Explorer öffnen
2. User Token mit benötigten Berechtigungen erzeugen
3. `/me/accounts` prüfen
4. Korrekten Page Token für „Bülents biker life" ermitteln
5. Scopes/Token prüfen
6. GitHub Secret `FACEBOOK_PAGE_TOKEN` aktualisieren
7. Facebook Poll isoliert testen
8. Erst danach: `ENABLE_FACEBOOK_ENGAGEMENT=true`

---

## 5. Gemeinsamer Meta-Webhook (PR #66, gemergt)

**Status:** ✅ Foundation auf main, noch nicht live

### Dateien
- `meta_engagement_webhook.py`
- `meta_engagement_dispatch.py`
- `test_meta_engagement_webhook.py`
- `docs/META_ENGAGEMENT_WEBHOOK.md`

### Sicherheits-/Transportlogik
- GET-Verifikation mit `META_WEBHOOK_VERIFY_TOKEN`
- POST-Prüfung von `X-Hub-Signature-256` mit `META_APP_SECRET` (HMAC-SHA256)
- Fail-closed bei fehlendem Secret, falscher Signatur, falschem Verify-Token, ungültigem JSON
- Kommentarereignisse werden normalisiert
- Gemeinsame Inbox: `memory/META_ENGAGEMENT_INBOX.jsonl`
- Dispatcher leitet Instagram-Events an `instagram_engagement`, Facebook-Events an `facebook_engagement`
- Webhook veröffentlicht selbst nichts, startet keinen Publisher

### Warum noch nicht live
- GitHub Actions ist kein dauerhafter HTTPS-Webhook-Server
- VPS-Umzug nötig (siehe Hauptübergabe)

---

## 6. Bestehendes System (wird weiterverwendet)

- `telegram_router.py` bleibt der zentrale Telegram-Poller
- `.github/workflows/telegram-receive.yml` startet ihn im Zeitplan
- **Kein zweiter Telegram-Bot**
- Closed-Loop-Memory aus Agent 14 bleibt übergeordnet
- Community-Memories liefern belegbare Engagement-Signale

---

## 7. Erforderliche Secrets

### Bestehend (aktiv)
- `INSTAGRAM_USER_ID`
- `INSTAGRAM_ACCESS_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Pausiert / in Arbeit
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_TOKEN` (⚠️ pages_read_engagement-Problem)

### Für späteren Webhook
- `META_WEBHOOK_VERIFY_TOKEN`
- `META_APP_SECRET`

### Regel
Keine Secrets in Git, Logs, Dokumentation oder Chat. Bei versehentlichem Posten: sofort rotieren.

---

## 8. Instagram-API-Endpoints – Live geprüft (24.09.2026)

**Test-Workflow:** `.github/workflows/instagram-api-test.yml`

| Endpoint | Status | Verfügbar |
|---|---|---|
| `/{ig-user-id}` | 200 | ✅ Token gültig |
| `/{ig-user-id}/media` | 200 | ✅ |
| `/{ig-user-id}/tags` | 200 | ✅ (aktuell 0) |
| `/{ig-user-id}/mentions` | **400** | ❌ (nur via Webhook) |
| `/{ig-user-id}/stories` | 200 | ✅ (aktuell 0) |

**Konsequenzen:**
- Tagged-Media-Agent baubar, aber geringer Nutzen aktuell
- Story-Replies: separater Test nötig (pollbar?)
- Mentions: nur via VPS/Webhook

---

## 9. Nächste Schritte (Reihenfolge)

1. **Live-Test:** Warten auf erstes echtes `IG-XXXXXXXX`-Ticket
2. **Reply-Test:** `info` → `memory` → `antwort` ODER `ändern`
3. **Facebook-Token:** Graph API Explorer, Page-Token isolieren
4. **Facebook reaktivieren:** `ENABLE_FACEBOOK_ENGAGEMENT=true`
5. **VPS/Webhook:** Echtzeit statt Polling
6. ~~reply_draft-Lücke~~ ✅ erledigt 25.09.2026
7. **Weitere Engagement-Quellen:** Tagged Media, Story-Replies

---

## 10. Aktueller Stand (24.09.2026 Abend)

| Komponente | Status |
|---|---|
| Instagram Agent 17 | ✅ aktiv |
| Instagram Polling (3h) | ✅ aktiv |
| First-Run-Schutz | ✅ aktiv |
| Telegram-Router | ✅ aktiv |
| Community-Memory | ✅ aktiv |
| Reply Adapter | ✅ auf main |
| Mock Unit Test | ✅ PASS |
| Facebook Agent 18 | ⏸️ pausiert |
| Meta Webhook | ✅ Foundation, nicht live |
| VPS | ❌ nicht produktiv |
| reply_draft | ✅ geschlossen 25.09.2026 (KI generiert Antwortvorschläge) |

---

## 11. Wichtige Regeln

- Kein Auto-Reply ohne Freigabe
- Keine Auto-Likes
- Keine Auto-Follows
- Keine gekauften Follower
- Kein Engagement-Spam
- Keine Massen-DMs
- Keine Tokens im Repo
- Publisher nicht automatisch starten
- Keine stillen Besucher erfinden
- Nur tatsächlich von der API gelieferte Interaktionen verwenden

**Human-in-the-Loop ist Pflicht:**
> Meta empfängt → Agent bewertet → Memory dokumentiert → Telegram fragt → Bülent entscheidet.

---

**Ende Engagement-Detail-Übergabe – Stand 24.09.2026 Abend**

---
📖 NÄCHSTER TEIL:
→ Lies jetzt: docs/PROJEKT_UEBERGABE_3_RACING.md

Diese Datei ist Teil 2 von 3.
---
