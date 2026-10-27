# Kostenloser Telegram-/Publisher-Taktgeber

Eigenständiger Cloudflare Worker, kein Container und kein R2-Zugriff. Ein Cron
(`2-57/5 * * * *`) genügt. Telegram: alle fünf Minuten. Facebook: Minute 2/17/32/47,
Instagram: 7/22/37/52, rund um die Uhr. 288 Worker-Aufrufe und maximal 480
Workflow-Dispatches pro Tag. Keine neuen Provider, keine LLM-Aufrufe im Worker.

Die vorhandenen GitHub-Cron-Zeitpläne bleiben zunächst als Rückfallweg bestehen.
Aktive oder bereits in diesem Zeitfenster gestartete Läufe werden übersprungen.
Keine Garantie für exakt-einmalige Dispatches (GitHub-Listen können verzögert sein).
Bestehende Concurrency-, Freigabe- und Publication-Claim-Prüfungen bleiben maßgeblich.
Ein Dispatch-204 ist nur eine Startannahme, kein fertiger Post. GitHub-Runner können
weiterhin warten; der externe Taktgeber beseitigt die Abhängigkeit vom GitHub-Cron,
nicht sämtliche möglichen GitHub-Ausfälle.

## Betrieb / Kosten

Workers Free unterstützt Cron; dieser Worker hat keine Paid-only-Bindings.
Die Kündigung des Workers-Paid-/Container-Abos erfordert kein Container-Weiterabo
für diesen Worker. Der Kontotarif, freie Cron-Slots, die gesamte Kontonutzung und
reale CPU-Messwerte müssen beim Deployment/Livetest geprüft werden; ein Code-Test
bestätigt weder den Tarifwechsel noch tatsächliche Gebührenfreiheit des Kontos.
Offizielle Grenzen: https://developers.cloudflare.com/workers/platform/limits/
Tarife: https://developers.cloudflare.com/workers/platform/pricing/
GitHub: https://docs.github.com/en/actions/concepts/billing-and-usage
Öffentliche Repositories mit Standard-Runnern sind unabhängig vom Starttyp kostenlos.
Der Deploy prüft deshalb Sichtbarkeit und aktive Zielworkflows, ohne sie zu starten.

Der bestehende Secret `AI_GITHUB_DISPATCH_TOKEN` benötigt Actions read/write auf
Edirne22/KI-SOCIAL-AGENT. Cloudflare-Zugang benötigt Workers Scripts Edit und
Zugriff auf das bestehende Konto. Kein Token wird im Repository gespeichert.
Die Deployment-Action installiert zunächst eine deaktivierte Version, danach den
Secret und aktiviert zuletzt. Fehler lassen den Worker deaktiviert.
Es gibt keinen öffentlichen HTTP-Startendpunkt. Abschalten: Workflow
`Free GitHub Scheduler` auf main manuell mit `enabled=false` ausführen.

## Endliche Abnahmematrix

- Offline PASS: 24h-Frequenzen, versetzte Publisher, feste main-Ziele, disabled,
  fehlender Secret, aktive Jobs, gleicher Zeit-Slot, veralteter/falscher Tick,
  Lookup-403/429, kaputte Antwort, abgelehnter Dispatch, Timeout ohne POST-Retry,
  unabhängige Verarbeitung des anderen Workflows, kein öffentlicher Dispatch.
- Offline PASS: bestehende Publisher/Freigaben werden nicht verändert.
- CI: `node --test infra/github-scheduler/worker.test.mjs` ohne Netzwerk/Secrets.
- LIVE OFFEN bis Merge/Deployment: Cloudflare-Tarif/Restkontingent, CPU-Limit im
  Free-Tarif, Deployment, Token-Schreibberechtigung, Cron-Auslösung und GitHub-Starts.
- LIVE Abnahme: mindestens drei aufeinanderfolgende Telegram-Takte sowie zwei
  Takte pro Publisher anhand Cron-Logs und GitHub event=workflow_dispatch prüfen.
- N/A: neue Content-Erzeugung, private Medien, Migration von R2, Container-Restart.

Lokal: `node --test infra/github-scheduler/worker.test.mjs`.
