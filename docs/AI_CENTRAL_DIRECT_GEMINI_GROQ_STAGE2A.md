# Schritt 1 / Stufe 2A: Direkte Providerbeweise vor Aktivierung
**Bülent-Auftrag:** NVIDIA als heute LIVE belegte Basis behalten; Gemini und Groq separat als mögliche Gratis-Ergänzung prüfen. OmniRoute bleibt pausiert. Kein vorhandener Production-Workflow wurde durch diesen PR umgestellt.

## Bereits echte technische Beweise
Run #36903543954: Nemotron research=ANSWER; Kimi diagnosis=ANSWER; OpenRouter challenge=UNAVAILABLE; OmniRoute separate FAIL. Die private R2/Dashboard-Strecke über ursprüngliches `--free-only` funktioniert aus früheren Nutzeraufträgen, die neue Teamstrecke ist produktiv nicht freigeschaltet. Ein reiner Workflow-SUCCESS zählt NICHT als kompletter Team-PASS.

## Exakte neue Kandidaten
- Gemini `gemini-3.7-flash` als Kandidat auf Googles öffentlicher Pricing-Seite im **Free Tier / Standard** aufgelistet: https://ai.google.dev/gemini-api/docs/pricing
- Groq `openai/gpt-oss-20b` als Modell in Groqs **Free Plan Limits** aufgeführt: https://console.groq.com/docs/rate-limits ; individuelle tatsächliche Quoten prüfen.
- Nur ein öffentliches synthetisches `READY`-Prompt, 40 Ausgabetoken maximal, 15s Timeout, KEIN automatischer Retry. Kein Grok/xAI; kein Claude; keine bezahlten Standard-Aliasse.
- Publizierte Gratis-Katalogangabe beweist **NICHT** den tatsächlichen Billing-Status eines vorhandenen persönlichen API-Schlüssels. Aus Sicherheitsgründen verweigert die neue Probe Netzverkehr, solange nicht explizit der richtige Gratis-Account bestätigt wurde. Ein bestehender Secret-Name allein reicht dafür nicht. Bei Unsicherheit Probe NICHT manuell starten.
- Die spätere Produktion erfordert eigenen streng überprüften Merge/PR, providerseitigen Gratis-Billing-Check, R2-Auftrags- und Team-Vertrag, echte Modellnamen, Failover- und Dashboard/Telegram-E2E. In diesem PR nur isolierter Probe-Kandidat plus Offline-Angriffsregressionen.
- Workflow `AI Central – direct Gemini Groq candidate audit`: PR löst nur Offline-Sicherheitsjobs aus; opt-in manuelle Einzelfallprobe ausschließlich nach Merge auf `main`, wenn die auslösende Person explizit bestätigt, dass der ausgewählte Key zu einem nachweislich kostenfreien Account gehört. Bei paid/unklar: nicht ausführen.
- Keine Änderung am bestehenden OmniRoute-Test, keine weitere OmniRoute-Schleife. Keine Source-Kopien aus Agent-Vorlagen und keine Container-Deploys.
