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


## Nächste Phase nach erfolgreichen Modell- und Coding-Lane-Tests: privates mobiles Web-Dashboard

**Feste Bülent-Anforderung vom 01.10.2026:** Zugang über Android-Browser, nicht über den Laptop. Dashboard bietet Chat-Auftragseingabe, Datei-Uploads, Mikrofoneingabe und daneben einen echten Live-Status-/Log-Bereich (mobil umschaltbare Tabs). Der Nutzer kann laufende Aufgaben, Provider/Fallbacks, Zeitstempel, GitHub-Run/PR/CI und R2-Ausgabedateien verfolgen, auf Details tippen, und vor Code-Merge/Deploy explizit freigeben. Keine gefälschten Live-Ausgaben.

### Architektur
- **Frontend**: kleine responsive App mit Cloudflare Worker Static Assets oder Pages (nach offizieller Dokumentation und Deploymentprüfung), **nicht R2 als ausführender Webserver**. Öffentliche statische Assets allein enthalten keine Secrets. R2 bleibt privat als Upload- und Artefakt-/Gedächtnisspeicher.
- **API und Sicherheit**: separater Worker als authentifizierter Gateway, kurzlebige Sitzungen, CSRF-/Origin-Schutz, Rate- und Größenlimits, geschlossene CORS, GitHub- und Provider-Zugangsdaten ausschließlich als Cloudflare Worker Secrets bzw. GitHub Actions Secrets. Keine Keys im Browser, R2-Links nur temporär signiert, kein freier GitHub-Workflow-Dispatcher. Keine Entwicklung des Auth-Mechanismus ohne verifizierte offizielle Cloudflare-Doku und Bedrohungsmodell.
- **Auftragssteuerung**: Worker prüft Benutzereingaben, Rollen, Task-Typ, Prompt- und Dateigrößen, schreibt versionierten Auftragsdatensatz (R2) und stößt nur erlaubte GitHub-Workflows über eng begrenzte Berechtigung an; Freigabe von Code/Deploy ist separater bestätigungspflichtiger Schritt. Das aktuelle repo-pinned allowlist-Gate aus #277 darf nicht durch rohe Chattexte umgangen werden; dafür zunächst nur Diagnoseaufträge eines kontrollierten Schemas zulassen.
- **Upload**: signierter, befristeter Upload in isolierte private R2-Prefixes, kontrollierte MIME-Typen/Größen, Dateinamen säubern, Prüfsumme, keine aktive Ausführung hochgeladener Dateien. Erst nach Prüfung Daten als Referenz an Modelle weitergeben.
- **Sprache**: Mobil-Browser fragt Mikrofonerlaubnis nach explizitem Klick; Audioaufnahme über unterstützte Browser-API und Upload nach R2. Server-/Job-basierte Speech-to-Text-Stufe separat anhand vorhandener kostenloser Werkzeuge und realer Laufzeitlimits evaluieren. Keine automatische permanente Mikrofonaufnahme und keine Unterstellung von Browser-kompatibler SpeechRecognition.
- **Live-Bereich**: GitHub-Jobzustände und zeitgestempelte, redigierte Ereignisse in R2/geeignetem Statusspeicher ablegen. Polling zunächst im Sekundenabstand, später Worker SSE/DO/WebSocket nur wenn ein stabiler Event-Stream und Cloudflare-Laufzeitkonzept getestet sind. GitHub Actions-Logs sind nicht garantiert sekündlich verfügbar; „Echtzeit“ muss Ereigniszeitstempel mit dokumentierter Verzögerung anzeigen, niemals Fortschritt erfinden.
- **Persistenz**: Run/Task/Session-Verzeichnis mit Metadaten und Verweisen zu Objekten; private Langzeitarchivierung, Versionierung, Aufbewahrungs-/Löschregeln und Budgetgrenzen. R2 ist Objektablage, nicht relationale DB oder Nachrichtenbroker; bei Bedarf Cloudflare D1/Durable Objects/Queues nach dokumentierter Lifecycle-/Kostenprüfung ergänzen.
- **Mobile UX**: Desktop zwei Spalten Chat links / Live-Code-und-Job-Kasten rechts; Android umschaltbare „Chat“, „Live“, „Dateien“, „Freigaben“-Tabs, Stopp-/Abbruchanforderung und eindeutige Zustände. Keine Anzeige interner API-Schlüssel oder unredigierter Model-Prompts.
- **Abnahme vor öffentlichem Zugriff**: lokale/offline Frontend-Sicherheitstests; serverseitige Auth-/Rollen-/Upload-/Workflow-Abuse-Tests; private Cloudflare Preview; ein echter Chat->GitHub->Modelle->R2->Live-Status E2E mit anonymen Testdaten und GitHub-Verifikationslinks. Benutzerzugang wird erst nach expliziter Freigabe aktiviert.

**Priorität:** Nach abgeschlossener und freigegebener #276/#277-Basis und geprüfter isolierter Coding-Lane eigenes kleines Dashboard-PR in Phasen (UI-Mock ohne Backend-Zugriff, sichere API, R2-Upload, Mic/STT, Statusstream). Bestehende Cloudflare OpenChatCut-Container-Instabilität darf Dashboard-Prototyp nicht blockieren, aber es darf dieselben unbewiesenen Container-Runtime-Annahmen nicht übernehmen.


## Verbindliche Portabilitätsregel: Cloudflare Worker heute, VPS als Ausweichweg

Bülent hat am 01.10.2026 festgelegt: Der aktuelle Cloudflare-Versuch bekommt Zeit bis heute; bei weiterem Scheitern ist ein Wechsel auf einen VPS ausdrücklich vorgesehen. Dashboard und Orchestrierung dürfen **keinen harten Cloudflare-Lock-in** erzeugen. Drei klar getrennte Komponenten: (1) browserbasierte Frontend-App mit relativen/API-konfigurierbaren Endpunkten, (2) austauschbares API-/Authentifizierungs-/Job-Dispatch-Backend, zunächst Cloudflare Worker, später bei Bedarf Node/Python auf x86-VPS, (3) persistentes privates R2 über S3-kompatible Schnittstelle. GitHub Actions kann bis zur VPS-Migration die KI-Jobs weiter ausführen. Die bestehende Container-Störung ist nicht automatisch ein Fehler des normalen Workers oder von R2. Ein Wechsel der Rechenumgebung bedeutet nicht, R2 zu löschen oder neue Provider-Verbindungen aufzubauen. Wichtig: Cloudflare Worker-spezifische SDKs hinter Adaptern isolieren, weder Auth noch Job-Dispatch mit Frontend fest verdrahten. Cloudflare- und VPS-Ausführung mit denselben API-Kontrakten und E2E-Tests abnehmen. Kein bezahlter VPS und keine Kündigung ohne separate Entscheidung des Nutzers.
