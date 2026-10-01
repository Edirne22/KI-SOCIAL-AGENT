# Bülents KI-Zentrale – Cloud-only control plane

**Stand 2026-10-01. Laptop ausdrücklich ausgeschlossen.**

## Bewiesene Basis

- OpenChatCut-Multimodellbrücke in PR #276: GitHub-Runner ausführbar; Live-Durchlauf #36855536726 mit kataloggeprüften NVIDIA (19 passende Treffer), Groq (4), OpenRouter (119), Gemini und funktionierender privater R2-Ablage.
- Achtung: Modell-Katalogeintrag bedeutet NICHT, dass kostenloser Inferenzzugriff, hohe Leistung oder eine bestimmte Modellversion freigeschaltet sind. Zahl bezieht sich auf Filtertreffer, nicht eindeutige aktive oder kostenlose Agenten.
- GitHub-Workflow-Dateien verwenden bisher die folgenden Secrets: NVIDIA_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME. Diese Namen stammen aus eingecheckten Workflow-Konfigurationen; GitHub-App-Zugriff stellt **keine Liste der tatsächlichen Secret-Werte** bereit. Einzelne Zugänge sind nur durch die realen Runner-Ergebnisse nachgewiesen.
- Das vorhandene GitHub-Projekt-Memory wird weiter als versionierte Regel-/Quellenbasis verwendet. R2 ergänzt als **dauerhafte Arbeitsablage** für Laufprotokolle, Aufträge und Berichte; es ersetzt das Git-Repository nicht.

## Architekturschnitt

GitHub ist Auftragsquelle/CI/kurzlebige Ausführung. Github Actions Runner erhalten nur pro Job benötigte GitHub Secrets, kontaktieren direkt erlaubte Provider-Endpunkte und archivieren den Ergebnisbericht als GitHub-Artefakt und optional im privaten R2-Bucket. R2 führt **niemals** Programme aus und bewahrt weder Zugangsdaten noch frei ausführbare Arbeitsanweisungen auf. Ein späterer Cloudflare Worker kann ausschließlich als authentifizierter Auftragseingang und Statusabfrage dienen. Weder ein Always-on-Container noch ein neuer Domain-/API-Key ist für diese erste Phase erforderlich.

Die drei parallelen Beratungsrollen im MVP sind Research (Gemini > NVIDIA), Diagnosis (NVIDIA > OpenRouter), Challenge (Groq > Gemini). Jede Rolle versucht maximal zwei Provider und produziert ein begrenztes Gutachten. Ein Auftrag ist eine vorab geprüfte Datei im Repository, keine rohe externe Eingabe. Jeder Bericht landet mit eindeutigem task_id und run_id unter `ai-central/v1/tasks/<task-id>/runs/<run-id>/report.json` mit Status `PENDING_REVIEW`. Eine Modelleinigung ist keine technische Verifikation.

## Erweiterungsreihenfolge und Gates

1. **PR #276:** Diagnose-/Inventurbrücke getrennt prüfen und nur bei freigegebenem Umfang mergen.
2. **Dieser PR #277:** Zentrale Auftrags- und R2-Berichtsablage mit Offline-Tests. Erst nach Review/merge ist der manuelle GitHub-Workflow aus dem Default-Branch ausführbar. Keine Produktionsfreigabe durch grünen Mock-Test allein.
3. **Modell-Prüflabor:** echte Provider-Kataloge mit Pagination nach jeweiliger API, gezielte Kurzproben für Modell-ID, Antwortzeit, Fehler/429 und effektive Nutzbarkeit. Kleine Batches, Kosten-/Rate-Limits und explizites Laufbudget; keine unkontrollierten 100-Modell-Volltests. Ergebnisse datiert und versioniert in privatem R2 speichern.
4. **Coding-Lane:** OpenCode oder Jules mit einem isolierten, begrenzten GitHub-Auftrag; vor Aktivierung offizielle CLI-/Anbieter-Doku lesen, reale Verfügbarkeit prüfen, minimale Repo-Rechte; eigene Branches und PRs. Kein automatischer Merge/Deploy und keine Übernahme von Modell-Text als Shell-Befehl.
5. **Operative Zentrale:** nach gemessener Nutzung optional Cloudflare Worker als abgesicherter API-Eingang. GitHub-Runs bleiben Rechenfläche; R2 bleibt gemeinsames Archiv. Durable Orchestration/Queues nur nach realem Bedarf.

## Sicherheit und laufende Kosten

- Kein unbeschränkter Dauerzugriff für Modelle; bestehende Schlüssel bleiben GitHub Secrets. Nur für ausgewählte, dokumentierte Workflows und begrenzte Aufgaben benutzen.
- R2-Free-Tier-Größe, Operations- und Egress-Regeln hängen von aktuell geltenden Cloudflare-Konditionen ab; 10 GB sind keine automatisch monatlich neu verfügbaren 10 GB. Aufbewahrungs- und Löschregeln vor Langzeitbetrieb festlegen.
- Niemals Blind-Deploy für den instabilen OpenChatCut-Container. Nachgewiesene Symptome und fehlende Lifecycle-Logs bleiben gesondert in den Diagnosesnapshots dokumentiert.
- Es existiert keine unsichtbare Dauerüberwachung durch ChatGPT: Automatische Arbeit findet ausschließlich in tatsächlich konfigurierten GitHub-Jobs/Workflows statt.

## Start nach Freigabe

GitHub Actions → `Cloud AI Central – guarded dispatch` → Run workflow → Task `openchatcut-stability`. Offline-Gate läuft zwingend davor. Bei fehlenden Credentials oder Modellantworten wird kein PASS erzeugt. Ergebnis-Artifact und privater R2-Pfad werden dokumentiert.
