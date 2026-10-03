# PROJECT GUARDRAILS – VERBINDLICHE ARBEITSREGELN

> **STATUS: VERBINDLICH**
>
> Diese Datei definiert die dauerhaften Entwicklungs-, Qualitäts-, Red-Team-, Fakten-QM-, Monitoring- und Merge-Regeln für **Edirne22/KI-SOCIAL-AGENT**.
>
> Sie ist bei jeder größeren Änderung, jedem neuen Agenten und jeder Projektübergabe zu berücksichtigen.
>
> Ein PROJECT_HANDOVER oder Snapshot darf diese Datei nicht ersetzen. Neue Erkenntnisse und dauerhaft geltende Regeln müssen hier ergänzt werden.

## 1. Pflicht-Abschlusskette

Eine Funktion, ein Agent oder eine größere Änderung gilt nicht allein deshalb als fertig, weil die normale CI grün ist.

```text
BUILD
→ REGRESSION
→ CI
→ RED-TEAM / FAKE-NEWS / HALLUCINATION ATTACK
→ POSITIVE CONTROL
→ ROOT-CAUSE
→ FIX
→ ATTACK AGAIN
→ CI GREEN
→ MERGE-FREIGABE DURCH BÜLENT
```

## 2. Red-Team-/Fake-News-/Halluzinationstests

Nach relevanten Änderungen müssen die Agenten bewusst mit manipulierten oder erfundenen Informationen angegriffen werden.

Pflicht-Fallklassen, soweit für die Änderung relevant:

- erfundene Fahrer und Fahrer-Verwechslungen
- falsche Schreibweisen/Namensvarianten
- erfundene Teams und falsche Hersteller
- erfundene Orte
- manipulierte Zahlen, Platzierungen und Zeitabstände
- falsche Rennserien und Serien-Hashtags
- falsche Sessions (z. B. Superpole vs. Superpole Race, Race 1 vs. Race 2)
- erfundene Verträge und Teamwechsel
- Gerücht/Signal wird als bestätigte Tatsache dargestellt
- unsichere Quelle wird zu einer definitiven Aussage hochgestuft
- falsche Nationalitäten
- Sprach-/Grammatikfehler und fremdsprachige Textreste
- mehrere manipulierte Fakten gleichzeitig
- korrekte Quelle + absichtlich falscher generierter Post
- Provider-/Semantic-QM-Ausfall
- DEGRADED-PASS unter manipulierten Fakten

Ziel: Nicht belegte oder widersprüchliche Fakten müssen zuverlässig blockiert werden.

## 3. Positivkontrollen sind Pflicht

Jeder neue Schutzmechanismus braucht passende Positivkontrollen. Echte, von der Quelle belegte Fakten dürfen nicht durch überaggressive Guards blockiert werden.

Beispiele:

- Quelle enthält Barcelona → Barcelona im Post darf verwendet werden.
- Quelle enthält Ducati → Ducati im Post darf verwendet werden.
- Quelle enthält Can Öncü → Can Öncü darf korrekt verwendet werden.
- Quelle kennzeichnet etwas als Gerücht → eine entsprechend vorsichtige Formulierung darf PASS erhalten.

## 4. Jeder gefundene Fehler wird Regression

Wird in einem realen Lauf oder Red-Team-Test ein neuer reproduzierbarer Fehler entdeckt, soll daraus ein permanenter Regressionstest entstehen.

**Ein Fehler, den wir einmal gefunden haben, darf von einer zukünftigen Version nicht unbemerkt erneut produziert werden.**

Bekannte Fallklassen umfassen u. a.:

- Superpole Race → fälschlich Superpole
- Gerücht/Signal → definitive Aussage
- „vor dem Renne“
- erfundene Zahl
- erfundener Fahrer
- erfundener Ort
- erfundenes Team (z. B. Phoenix-Werksteam)
- falsche Serie / falscher Serien-Hashtag
- Semantic-Ausfall + DEGRADED-PASS
- Run #138: unsicherer Roh-Titel („starkes Signal“) darf durch ein generiertes Summary nicht zu „bestätigt“ hochgestuft werden
- Run #138: Motorrad-Racing darf nicht „Werkswagen“ verwenden
- Run #138: unnatürliche Übersetzungsartefakte wie „Duble“, „Weekend ... erledigt“ und „Double-Wochenende“ müssen ins Human-Writing-Retry\n- Run #139: ein generiertes/aktualisiertes Summary darf einen Zukunfts-/Transfer-Titel ohne expliziten Bestätigungsmarker nicht zu einer definitiven Aussage hochstufen\n- Run #139: „Ein enger Schnitt für den nationalen Sportler“ und grammatisch falsche CTA wie „Wie einschätzen ihr ...?“ müssen ins Human-Writing-Retry

## 5. Source-Provenance / Wahrheitsprinzip

> **Behaupte nichts, wofür nicht gezeigt werden kann, woher die Information stammt.**

Jede konkrete Tatsachenbehauptung eines Posts muss auf die zugelassenen Quellenfakten zurückgeführt werden können.

Relevante Quellen-/Vertragsinformationen können sein:

- Titel
- Zusammenfassung
- explizit zugelassenes Source-Fact-Packet / Locked Metadata
- Series-Lock
- Session
- Fahrer
- Zahlen
- Orte
- Teams
- Hersteller
- Transfer-/Vertragsstatus
- weitere ausdrücklich belegte Fakten

Die URL ist Provenienz/Verweis und nicht automatisch eine Faktenquelle.

Keine belegbare Herkunft → Claim blockieren oder zum Editor zurückgeben.

## 6. DEGRADED-PASS

DEGRADED-PASS bleibt erhalten. Ein technischer Ausfall eines LLM-/Semantic-Providers darf einen ansonsten korrekten Beitrag nicht automatisch vernichten.

Aber DEGRADED-PASS darf niemals deterministische Wahrheits- oder Qualitätsregeln umgehen.

Auch bei Semantic-/Provider-Ausfall müssen die verfügbaren deterministischen Gates greifen, insbesondere für:

- Fahrer
- Zahlen
- Serie
- Session
- Orte
- Teams
- Hersteller
- Claim-Strength / Gerücht vs. Tatsache
- Sprache / Human-Writing
- Final-Guard

**Technischer Provider-Ausfall ist kein Freifahrtschein für unbelegte Fakten.**

## 7. Turkish Rider vs. normale Racing-Pipeline

Turkish Rider darf eine eigene Relevanz-Lane besitzen. Eine ausdrückliche T1–T5-/Human-Auswahl darf z. B. einen belegten türkischen Nebenfahrer als Thema setzen, obwohl ein anderer Fahrer Hauptthema der Quelle ist.

Die Turkish-Rider-Lane bekommt jedoch **keine gelockerten Wahrheitsregeln**.

```text
NORMAL RACING
→ normale Relevanzprüfung
→ gemeinsame harte TRUTH-LINE

TURKISH RIDER
→ T1–T5 / Human-Relevance
→ Turkish-Relevance
→ gemeinsame harte TRUTH-LINE
```

Die Relevanzentscheidung darf unterschiedlich sein. Die Faktenwahrheit darf nicht unterschiedlich sein.

Für beide gelten dieselben harten Regeln für Fahrer, Zahlen, Serie, Session, Orte, Teams, Hersteller, Verträge, Transfers, Gerücht/Fakt, Sprache und Source-Provenance.

## 8. Monitoring laufender Prozesse

Es darf nicht behauptet werden:

- „Ich behalte das im Auge.“
- „Ich überwache den Lauf.“
- „Ich melde mich, wenn er fertig ist.“
- „Ich passe im Hintergrund auf.“

wenn tatsächlich keine technische Überwachung, Automation oder Erinnerung eingerichtet wurde.

Wenn eine zukünftige Überwachung zugesagt wird, muss sie tatsächlich eingerichtet werden. Andernfalls muss klar gesagt werden, dass der Status nur im aktuellen Turn geprüft werden kann.

Bei laufenden PRs/CI:

```text
FAIL
→ Logs prüfen
→ konkrete Root Cause bestimmen
→ sicheren Fix durchführen
→ geänderten Code prüfen
→ Fix pushen
→ neue CI prüfen/verfolgen
→ erneut analysieren
```

Keine Tests umgehen. Keine künstlichen PASS-Ergebnisse. Keine Sicherheits-, Fakten- oder QM-Prüfungen deaktivieren.

## 9. Merge-Regel

Analyse, Branches, Codeänderungen, Tests, Regressionen, CI-Analyse, sichere Fixes, Commits und PR-Vorbereitung dürfen selbstständig durchgeführt werden.

**MERGE NUR NACH AUSDRÜCKLICHER FREIGABE VON BÜLENT.**

### Ausdrückliche dauerhafte /BLOCKRUN-Freigabe von Bülent (02.10.2026, 19:26 MESZ)

Bülent hat im laufenden Chat die zuvor erteilte **dauerhafte technische Merge-Vollmacht bis zur Fertigstellung von Block 9** erneut ausdrücklich bestätigt. Diese Erklärung erfüllt für die darunter fallenden PRs die erforderliche ausdrückliche Freigabe: Die bestehende projektbezogene Vollmacht muss nicht bei jedem technisch geprüften Teil-PR erneut eingeholt werden. Die autonome Freigabe deckt die Umsetzung, Reparatur, Tests, Red-Team/Sicherheitsprüfung, CI-Fixes, grünen Merge und bewachten Deploy von bereits beauftragten Block-6-bis-9-Teilarbeiten und dazugehörigen Dashboard-/Systemmonitor-Erweiterungen ab. Nach jedem Merge tatsächlichen Lauf/Deployment nachweisen, keinen fiktiven PASS melden, HEAD/Guardrails/Snapshot vor jedem Eingriff erneut prüfen und keine parallelen Branches erzeugen.

**Ausnahmen und Grenzen:** Block 7 benötigt Bülents persönliche Einwilligung und Bereitstellung seiner **Fotos, Videos und eigenen Sprachaufnahmen**, bevor diese Dateien zur Avatar-/Stimmproduktion verarbeitet werden; rein synthetische technische Vorbereitungen bleiben möglich, ohne solche Daten vorauszusetzen. Keine kostenpflichtigen neuen Dienste/Hoster oder stillschweigende Kosten. **Keine Veröffentlichung echter Social-Media-Beiträge ohne Bülents konkrete Freigabe pro Beitrag**; technische Tests oder synthetische Vorschauen sind nie Veröffentlichungsautorität. Neue Aufgaben **außerhalb** dieser beauftragten Blöcke oder eine Erweiterung dieser Ausnahmen benötigen separate Rücksprache. Bewachte Deploys auf der bestehenden genehmigten Infrastruktur sind Teil der Freigabe; ein neuer Anbieter oder Vertragsabschluss ist es nicht.



Beispiele für eine Freigabe:

- „Merge 204“
- „Kann gemerged werden“
- „Merge den PR“

Ohne ausdrückliche Freigabe bleibt der PR ungemerged.

## 10. Snapshot / Projektübergabe / Handover

Bei „Snapshot“, „Projektübergabe“, „Handover“ oder einer vergleichbaren Projektstand-Zusammenfassung müssen diese Guardrails berücksichtigt werden.

Jede Übergabe soll weit oben einen deutlich sichtbaren Hinweis enthalten:

```markdown
## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN

Vor Arbeiten am Repository zuerst lesen:

PROJECT_GUARDRAILS.md

Diese Regeln gelten unabhängig vom aktuellen Entwicklungsstand und dürfen durch diese Projektübergabe nicht überschrieben werden.
```

Die Guardrails dürfen in einer Übergabe nicht zwischen normalen technischen Details versteckt werden.

## 11. Entwicklungsgrundsatz

Nicht nur fragen:

> Funktioniert die neue Funktion?

Sondern zusätzlich aktiv versuchen:

> Wie kann diese Funktion absichtlich kaputtgemacht oder ausgetrickst werden?

Gezielt falsche, widersprüchliche, erfundene und manipulierte Eingaben erzeugen. Erst wenn die Fallen erkannt werden **und** legitime Kontrollfälle weiterhin akzeptiert werden, gilt die Änderung als ausreichend abgesichert.

```text
BUILD → TEST → ATTACK → VERIFY → FIX → ATTACK AGAIN → CI GREEN → MERGE-FREIGABE
```


## 12. End-to-End-/Staffellauf-Prinzip für neue Projektblöcke

Bei jedem neuen Entwicklungsblock reicht es **nicht**, nur die neu hinzugefügte Funktion isoliert zu testen.

Vor einer Merge-Freigabe muss der gesamte bereits aufgebaute Weg **vom ersten Nutzereingang bis zum aktuell erreichten Endpunkt des Systems** erneut geprüft werden.

Für die Content-Fabrik bedeutet das mit wachsendem Ausbau sinngemäß:

```text
BÜLENTS BEFEHL / INPUT
→ JOB API / EINGANG
→ BETRIEBSLEITER / ORCHESTRATOR
→ ZUSTÄNDIGE AGENTEN UND MASCHINEN
→ MEDIA-/DATEN-STORAGE
→ HANDOFF AN NÄCHSTE STUFE
→ QM / FACT-CHECK / FINAL-GUARDS
→ PREVIEW
→ HUMAN AUTHORITY
→ PUBLISHER
→ PLATTFORM / NACHWEIS
```

Es wird jeweils nur bis zu dem Punkt getestet, der im Projekt bereits tatsächlich implementiert ist. Mit jedem neuen Block verlängert sich dieser verpflichtende Staffellauf.

### 12.1 Schnittstellen und Handoffs sind Teil der Funktion

Wenn Agenten, Tools oder Maschinen Dateien, Transkripte, Claims, Metadaten oder Statusinformationen untereinander weiterreichen, gehört die Übergabe selbst zur zu testenden Funktion.

Insbesondere prüfen:

- Job-ID bleibt über alle Stationen eindeutig erhalten.
- Revision/Version bleibt korrekt gebunden; veraltete Ergebnisse dürfen aktuelle Arbeit nicht überschreiben.
- Media-ID/URI/Hash/MIME/Größe/Provenienz bleiben nachvollziehbar.
- Keine Maschine darf unkontrollierte lokale Pfade oder eigene geheime Zustände zum System of Record machen.
- Ein Tool darf keine fremden Job-Ergebnisse in einen anderen Job einschleusen.
- Doppelklicks, Retries oder wiederholte Events dürfen keine ungewollten Doppeljobs/Doppelpublikationen erzeugen.
- Dateien dürfen beim Wechsel zwischen Storage, VPS und Werkzeugen nicht unbemerkt verändert, vertauscht oder verloren werden.
- Externe Tools bleiben austauschbare Maschinen hinter definierten Adaptern.
- Fakten-QM, Human Authority und kanonischer Approval State bleiben unter Kontrolle der Edirne-22-Fabrik.

### 12.2 Fehler-, Recovery- und Resume-Prüfung

Soweit für den jeweiligen Block relevant, muss zusätzlich geprüft werden:

- Tool/Provider nicht erreichbar
- Timeout
- Prozess-/VPS-Neustart
- unvollständige Datei
- manipulierte Datei / Hash-Mismatch
- veraltete Revision
- doppeltes Event / Retry
- Abbruch mitten im Handoff
- Fehler nach Rendering, aber vor Speicherung
- Fehler nach Freigabe, aber vor Veröffentlichung
- erneuter Start/Resume nach Fehler.

Ein Recovery darf nicht stillschweigend eine alte, ungeprüfte oder nicht mehr freigegebene Version veröffentlichen.

### 12.3 Proaktive Architekturprüfung ist Pflicht

Vor dem Build eines neuen Blocks muss aktiv gefragt werden:

> Welche Schwachstellen, Abhängigkeiten, unnötigen Kopiervorgänge, Single Points of Failure, Sicherheitsprobleme oder späteren Sackgassen entstehen durch diesen Schritt?

Die Entwicklungsarbeit soll nicht nur vorgegebene Einzelaufgaben ausführen. Sie soll **proaktiv**:

- Schwachstellen suchen,
- bessere technische Varianten erkennen,
- unnötige Eigenentwicklung vermeiden,
- geeignete bestehende Tools/Adapter empfehlen,
- Kosten-/Speicher-/Netzwerk-/Performance-Folgen beachten,
- Wartbarkeit und Austauschbarkeit prüfen,
- gefundene Verbesserungen vorschlagen und bei sicherem Scope in den Entwicklungsblock einarbeiten.

Beispiel: Wenn eine große Mediendatei zwischen VPS, Object Storage und mehreren Werkzeugen unnötig mehrfach übertragen würde, muss dies als Architekturproblem erkannt und eine effizientere Übergabe vorgeschlagen werden.

### 12.4 Definition of Done für jeden neuen Block

Ein neuer Block gilt erst als technisch vorbereitet für die Merge-Freigabe, wenn mindestens Folgendes erfolgt ist:

```text
ANALYSE DES GESAMTWEGS
→ BUILD
→ ISOLIERTE REGRESSION
→ HANDOFF-/SCHNITTSTELLENTEST
→ STAFFELLAUF VOM START BIS ZUM AKTUELLEN ENDPUNKT
→ NEGATIV-/RED-TEAM-TESTS
→ POSITIVKONTROLLEN
→ FEHLER-/RETRY-/RESUME-PRÜFUNG, SOWEIT RELEVANT
→ ROOT-CAUSE + FIX BEI FUND
→ STAFFELLAUF ERNEUT
→ CI GREEN
→ ERGEBNIS / REST-RISIKEN TRANSPARENT ZEIGEN
→ MERGE-FREIGABE DURCH BÜLENT
```

Ein grüner Einzeltest ersetzt **niemals** den Staffellauf. Ein simulierter Adaptertest darf **nicht** als echter Live-E2E-Test eines externen Tools ausgegeben werden.

### 12.5 Maschinen-, API- und CLI-Untersuchung vor Einbau

Vor dem Einbau oder der Integration einer neuen Maschine, API, CLI oder eines externen Services muss zuerst die offizielle Dokumentation in der genau verwendeten Version vollständig untersucht werden:
- Prereqs & Systemanforderungen
- Lifecycle & Boot-Verhalten
- Port-Readiness & Probe-Mechanismen
- Ressourcen & System-Limits
- Persistenz & Session Storage
- Rechte & Token/Auth-Modell
- Deployment-, Container- & Rollout-Verhalten
- Logging, Telemetrie & Exit-Codes
- Recovery-, Disconnect- & Retry-Strategien



## 13. BLOCKRUN – verbindliche End-to-End-Durcharbeitung

`/BLOCKRUN` ist die ausdrückliche Freigabe durch Bülent, einen benannten Entwicklungsblock oder einen benannten Bereich von Blöcken ohne freiwilliges Anhalten an normalen Zwischenständen bis zur vollständigen Definition of Done durchzuarbeiten.

### 13.1 Umfang der Freigabe

Mit `/BLOCKRUN Block X` umfasst die Arbeitsfreigabe innerhalb des benannten Scopes insbesondere:

- aktuellen Repository-/main-/HEAD-Stand und diese Guardrails prüfen,
- Architektur und vorhandene Komponenten analysieren,
- Arbeitsbranch anlegen bzw. den autorisierten Branch verwenden,
- Code bauen und fachlich notwendige Tests ergänzen,
- Commits und Pushes auf dem Arbeitsbranch durchführen,
- Pull Request erstellen/aktualisieren,
- relevante Runs und CI verfolgen,
- Logs bei Fehlern analysieren,
- Root Cause bestimmen und fachlich korrekt reparieren,
- Syntax-/Importprüfung, Regression, Positive und Negative Controls durchführen,
- Red-Team-, Security-, Manipulations-, Retry-, Idempotenz-, Crash-/Resume- und Handoff-Prüfungen durchführen, soweit für den Block relevant,
- vollständigen Staffellauf nach Abschnitt 12 durchführen,
- nach jedem Fix die betroffenen Angriffe und die relevante Gesamtregression erneut ausführen,
- den Block abschließend gegen seine Definition of Done prüfen.

Besteht für den benannten Scope zusätzlich eine ausdrückliche Merge-Freigabe, darf nach vollständiger technischer Abnahme gemergt und der Merge-Stand anschließend verifiziert werden.

### 13.2 Statusmeldung ist kein Stopp

Während einer aktiven Arbeitsausführung darf nach normalen Zwischenschritten nicht freiwillig angehalten und auf einen neuen Anstoß gewartet werden.

Insbesondere sind folgende Ereignisse nur Zwischenstände:

- Code geschrieben,
- Commit/Push erfolgt,
- PR erstellt,
- CI gestartet,
- einzelner Test oder CI grün,
- Regression grün,
- Red-Team gestartet,
- Finding gefunden,
- Fix erstellt.

Grundsatz:

```text
STATUS MELDEN → WEITERARBEITEN
```

Bei längerer aktiver Arbeit sollen kurze sichtbare Fortschrittsmeldungen nach dem Muster **Wo bin ich? → Was prüfe ich? → Was ist passiert? → Was mache ich jetzt?** gegeben werden. Die Fortschrittsmeldung beendet die Ausführung nicht.

### 13.3 ROT erzwingt die Reparaturschleife

Wird ein relevanter Test, Run oder CI-Lauf rot, gilt ohne erneute Freigabe:

```text
ROT
→ LOGS UNTERSUCHEN
→ ROOT CAUSE BESTIMMEN
→ FACHLICH KORREKT REPARIEREN
→ SYNTAX / IMPORTS PRÜFEN
→ FIX COMMITTEN / PUSHEN
→ BETROFFENEN TEST ERNEUT AUSFÜHREN
→ ERGEBNIS PRÜFEN
→ BEI ROT SCHLEIFE WIEDERHOLEN
```

Tests, Assertions, QM-, Security- oder Human-Authority-Prüfungen dürfen niemals abgeschwächt, umgangen oder entfernt werden, nur um ein grünes Ergebnis zu erzeugen.

### 13.4 Grün bedeutet nicht automatisch fertig

Ein grüner Einzeltest oder CI-Lauf beendet `/BLOCKRUN` nicht. Danach folgen die für den Scope relevanten Prüfungen aus Abschnitt 12, insbesondere Regression, Negative und Positive Controls, Red Team, Handoffs, Retry/Idempotenz, Crash/Resume, Staffellauf und Architektur-Review.

Erst die vollständige Definition of Done beendet den Block.

### 13.5 Red Team ist eine Angriffsschleife

Red Team bedeutet aktives Brechen der Implementierung, nicht nur einmaliges Starten vorhandener Tests. Je nach Block sind insbesondere falsche Zustände, ungültige Übergänge, Cross-Job-/Cross-Series-Leaks, Race Conditions, Duplicate Events, Retries, stale revisions, manipulierte IDs/Medien/Hashes/Provenienz, Prompt Injection, Fake News/Halluzinationen, fehlende Quellen, falsche Zuordnungen, kaputte Providerantworten, Timeouts, Neustarts, Abbrüche zwischen Prozessschritten, doppelte Publish-Versuche und Umgehungsversuche der Human Authority anzugreifen.

Jedes technisch lösbare Finding durchläuft:

```text
FINDING
→ ROOT CAUSE
→ FIX
→ REGRESSIONSTEST FÜR DIE FEHLERKLASSE
→ ANGRIFF ERNEUT
→ RELEVANTE GESAMTREGRESSION ERNEUT
```

### 13.6 Human Authority bleibt unantastbar

`/BLOCKRUN` erweitert niemals die fachlichen Rechte eines Agenten gegenüber der Human Authority. Kein Agent darf Bülents erforderliche endgültige Freigabe ersetzen oder eine gültige Human-Authority-Entscheidung durch einen späteren KI-Gate heimlich aufheben.

### 13.7 Architektur vor Patchwork

Vor einem lokalen Fix ist zu prüfen, ob nur ein Symptom oder die Root Cause behandelt wird. Root-Cause-Fixes sind Workarounds vorzuziehen. Zusätzlich sind vorhandene Komponenten, Doppelimplementierungen, Block-Abhängigkeiten, Datenverlust, Concurrency, Idempotenz, Recovery, Security, Provider-Coupling, Kostenfallen, Single Points of Failure und Rückwärtskompatibilität zu prüfen.

### 13.8 Keine erfundenen Erfolge

Es darf niemals behauptet werden, CI/Test/Live-E2E/Deployment/API/Plattformpost/Merge sei erfolgreich, wenn dies nicht tatsächlich verifiziert wurde.

```text
SIMULIERT = SIMULIERT
LIVE = LIVE
NICHT GEPRÜFT = NICHT GEPRÜFT
```

### 13.9 Nur echte externe Blocker dürfen unterbrechen

Nur ein technisch nicht selbst behebbarer externer Blocker darf einen aktiven `/BLOCKRUN` vor der Definition of Done unterbrechen, z. B. fehlender API-Key/Zugang, notwendige Anmeldung oder 2FA, fehlende externe Berechtigung, notwendige Zahlung, Provider-Ausfall, fehlende Tool-/GitHub-Berechtigung oder eine nicht freigegebene irreversible bzw. kostenpflichtige externe Aktion.

Eine Blockermeldung muss konkret enthalten:

- **BLOCKER:** Was blockiert?
- **BETROFFENER SCHRITT:** Wo steht der Lauf?
- **BEREITS ERLEDIGT:** Was ist vollständig fertig?
- **BENÖTIGT VON BÜLENT:** Welche konkrete Aktion/Entscheidung ist nötig?
- **FORTSETZUNG:** Welcher Schritt folgt unmittelbar danach?

### 13.10 Merge-Regel unter BLOCKRUN

Besteht Merge-Freigabe, erfolgt der Merge erst nach vollständiger technischer Abnahme gemäß Abschnitt 12. Bei Merge-Konflikten wird nicht blind überschrieben: aktuellen main analysieren, Konflikt fachlich lösen, relevante Tests/CI/Red-Team-Prüfungen wiederholen und erst anschließend mergen. Der gemergte Stand wird danach erneut verifiziert.

### 13.11 Mehrere freigegebene Blöcke

Bei `/BLOCKRUN Block X bis Block Y` wird jeder Block vollständig nach seiner Definition of Done abgearbeitet. Nach Abschluss und ggf. autorisiertem Merge von Block X wird ohne neue Freigabe unmittelbar mit dem nächsten bereits freigegebenen Block fortgefahren. Ein fertiger Zwischenblock ist bei einer Mehrblock-Freigabe kein Stopp-Punkt.

### 13.12 Laufzeit-Wahrheit und Hintergrundarbeit

`/BLOCKRUN` erlaubt keine erfundene Hintergrundarbeit. Solange eine aktive Tool-/Arbeitsausführung möglich ist, wird nicht freiwillig an einem normalen Zwischenstand gestoppt.

Wenn eine Chat-Ausführung technisch endet, darf nicht behauptet werden, ein normaler Chat arbeite heimlich stundenlang weiter. Verlangt Bülent ausdrücklich eine Weiterarbeit während seiner Abwesenheit oder über Nacht, muss dafür eine tatsächlich geeignete Hintergrund-/Automation-/Work-Ausführung eingerichtet und vor Verlassen des aktiven Laufs verifiziert werden. Ein solcher Hintergrundlauf muss seinen eigenen Fortschritt und Fehlerzustand nachvollziehbar machen.


### 13.14 HARD RULE – sichtbare Meldungen dürfen die Ausführung niemals beenden

Diese Regel hat innerhalb eines aktiven `/BLOCKRUN` Vorrang vor Komfort, Gesprächsrhythmus und dem Wunsch, nach einem Status auf eine Antwort zu warten.

> **Eine an Bülent gesendete Status-, Fortschritts-, Fehler-, Diagnose-, Commit-, PR-, CI-, Deploy- oder Testergebnis-Meldung ist ausschließlich Telemetrie. Sie ist niemals ein impliziter Stopp, niemals eine Rückgabe der Arbeitsverantwortung an Bülent und niemals eine Aufforderung, den Agenten erneut anzustoßen.**

Nach jeder sichtbaren Zwischenmeldung muss in derselben aktiven Arbeitsausführung unmittelbar die nächste technisch mögliche Aktion folgen.

Verbotenes Muster:

```text
STATUS MELDEN
→ Antwort beenden
→ auf "mach weiter", "prüf", "und?", "grün?" oder ähnlichen neuen Nutzerimpuls warten
```

Verbindliches Muster:

```text
STATUS MELDEN
→ NÄCHSTE TOOL-AKTION AUSFÜHREN
→ ERGEBNIS AUSWERTEN
→ BEI ROT LOGS HOLEN
→ ROOT CAUSE BESTIMMEN
→ FIX BAUEN
→ TESTEN
→ PUSH/PR/CI
→ ERNEUT AUSWERTEN
→ SCHLEIFE BIS DoD ODER ECHTEM EXTERNEN BLOCKER
```

Insbesondere gilt:

- `ROT` ist ein **Arbeitsauftrag**, kein Berichtsendpunkt.
- `queued` oder `in_progress` ist kein Grund, freiwillig aufzuhören, wenn parallel sinnvolle Prüf-, Analyse-, Dokumentations- oder Vorbereitungsschritte möglich sind.
- Ein Finding ist kein Endergebnis. Es muss, soweit technisch selbst behebbar, bis Root Cause + Fix + Re-Test verfolgt werden.
- Ein Fix ist kein Endergebnis. Der dadurch ausgelöste Test/CI-Lauf muss ausgewertet werden.
- Ein grüner Einzeltest ist kein Endergebnis. Die restliche DoD wird weiter abgearbeitet.
- Eine Statusmeldung darf nicht mit Formulierungen enden, die Bülents erneuten Startimpuls voraussetzen, solange kein echter externer Blocker vorliegt.
- Die nächste Aktion darf nur dann nicht ausgeführt werden, wenn sie technisch gerade unmöglich ist, außerhalb des freigegebenen Scopes liegt, eine ausdrücklich vorbehaltene Human-Authority-Entscheidung benötigt oder unter Abschnitt 13.9 als echter externer Blocker fällt.

**Selbstprüfung vor jeder Zwischenantwort in einem aktiven `/BLOCKRUN`:**

```text
1. Ist die Definition of Done erreicht?
   JA → Abschlussstatus mit Nachweisen.
   NEIN → weiter.

2. Liegt ein echter externer Blocker nach 13.9 vor?
   JA → konkrete Blockermeldung.
   NEIN → weiter.

3. Gibt es eine technisch mögliche nächste Aktion?
   JA → TOOL/ACTION JETZT AUSFÜHREN; nicht auf Bülent warten.
   NEIN → nur den tatsächlich unvermeidbaren Wartezustand transparent melden.

4. Ist ein Lauf ROT?
   JA → Logs JETZT holen und Reparaturschleife starten.

5. Ist ein Lauf GRÜN?
   JA → nächste DoD-Prüfung JETZT starten.
```

**Fail-safe-Leitsatz:**

```text
SOLANGE DoD = FALSE UND EXTERNAL_BLOCKER = FALSE:
    STATUS IST NUR TELEMETRIE
    NICHT PAUSIEREN
    NÄCHSTE AKTION AUSFÜHREN
    ROT => ZERLEGEN + REPARIEREN + NEU TESTEN
    GRÜN => NÄCHSTE DoD-STUFE
```

Diese Regel soll ausdrücklich verhindern, dass Bülent durch wiederholte Nachrichten wie `mach weiter`, `prüf jetzt`, `und grün?` oder `starte den nächsten Schritt` einen bereits freigegebenen `/BLOCKRUN` künstlich am Leben halten muss.


### 13.13 BLOCKRUN-Kurzform

Die verbindliche Kurzform lautet:

```text
/BLOCKRUN Block X

ANALYSIEREN
→ BAUEN
→ TESTEN
→ FEHLER ANGREIFEN
→ ROOT CAUSE
→ REPARIEREN
→ NEU TESTEN
→ CI
→ RED TEAM
→ STAFFELLAUF
→ ENDABNAHME
→ MERGE, WENN FREIGEGEBEN
→ MERGE VERIFIZIEREN
→ BEI MEHREREN FREIGEGEBENEN BLÖCKEN SOFORT WEITER
```

**STATUSMELDUNG ≠ STOPP. GRÜN ≠ AUTOMATISCH FERTIG. ERST DIE DEFINITION OF DONE BEENDET DEN BLOCK.**

---

**Pflegeprinzip:** Neue dauerhaft relevante Fehlerklassen, Arbeitsregeln und Schutzmechanismen werden in dieser Datei ergänzt, damit sie unabhängig von einzelnen Chats und Handovers erhalten bleiben.

## 14. FUNKTION VOR WERKZEUG – DAUERHAFTE BÜLENT-VISION (01.10.2026)

**HARTER KOSTEN-/LIZENZFILTER:** Neue Fallback-Maschinen müssen frei verfügbarer Open-Source-Code mit für unseren konkreten (ggf. kommerziellen) Einsatz erlaubter Lizenz und nachweislich kostenlosem Betrieb auf vorhandener/freigegebener Infrastruktur sein. Kein Kauf, Pflichtabo, kostenpflichtiger API-Key, Testguthaben als Schein-0-€-Lösung oder zusätzliche kostenpflichtige Hardware/Cloud ohne Bülents gesonderte Entscheidung. Proprietäre Freemium-Angebote und Kandidaten mit ungeklärter Software-/Modelllizenz oder Cloud-/GPU-Betriebskosten sind nur Archiv-/Rechercheeinträge, **keine automatischen Fallbacks**. GPL/AGPL ist nicht automatisch verboten, erfordert aber Prüfung der konkreten Weitergabe-/Netzwerk- und Modellpflichten. Bestehende bereits von Bülent freigegebene Dienste bleiben unberührt. Die verbindliche Prüfung und aktuelle Klassifizierung stehen in `docs/TOOL_INDEX.md` Abschnitt 0.

**Eine maßgebliche Werkzeug- und Alternativenliste:** `docs/TOOL_INDEX.md`. Vor jeder neuen technischen Werkzeugentscheidung, jedem Provider-Fallback und beim Wiederaufnehmen von `/BLOCKRUN` diesen Index zusammen mit dem aktuellen Projektstand lesen. `docs/IDEA_POOL.md`, `docs/FREE_TOOLS.md`, datierte Tool-Radare und `config/MEDIA_TOOLS.md` sind ausschließlich historische/vertiefende Quellen; keine konkurrierenden aktuellen Entscheidungen dort pflegen. Alle neuen Toolkandidaten und Statusänderungen zentral im Index ergänzen. 


**Verbindlicher Produktauftrag:** Bülent spricht natürlich mit der KI-Zentrale und/oder lädt eigene Bilder, Videos und andere Quellen hoch. Die Content-Fabrik übernimmt Aufnahme, Recherche mit belegbarer Herkunft, kreative Bearbeitung, Medienerstellung, technische/Fakten-QM und präsentiert fertige, tatsächlich überprüfbare Ergebnisse zur menschlichen Entscheidung. Bülent soll **keine Tools auswählen, starten oder Fehlversuche manuell dirigieren müssen**. Veröffentlichung bleibt ausschließlich an seine Human Authority nach Abschnitt 5 und 13 gebunden.

**Grundsatz: Die Nutzerfunktion ist fest, die ausführenden Maschinen und Provider sind austauschbar.** Keine Architektur darf unnötig an einen bestimmten Editor, Anbieter, Container oder Modellnamen gekettet werden. Ersatz hinter stabilen Adaptern wählen und nur nach echten Capability-/Qualitäts-/Sicherheits- und E2E-Nachweisen aktivieren. Der Betriebsleiter trifft die technische Routing-/Fallback-Entscheidung; Bülent gibt Ziele, Material und Veröffentlichungsentscheidungen vor.

**Proaktiver Blocker- und Ersatzprozess:**
1. Vor jedem neuen Toolversuch bestehende Adapter, lokal und auf der vorgesehenen Runtime tatsächlich verfügbare Open-Source-/Free-Werkzeuge und die gepflegte Ideen-/Toolliste prüfen. Keine kostenpflichtige Infrastruktur ohne separate Erlaubnis.
2. Einen konkreten Fehler mit Logs und Root Cause untersuchen. Nach höchstens zwei bis drei *sinnvoll unterschiedlichen*, begrenzten Versuchen mit gleichem externen Werkzeug bei weiterem externem Problem den funktionsfähigen Ersatzpfad priorisieren. Keine identischen Endlosläufe, keine Umgehung von QM oder Sicherheitsprüfungen. Ein sicherheitskritischer interner Fehler wird repariert und nicht durch Provider-Wechsel verdeckt.
3. Kann ein alternativer Stack das **gleiche zugesagte Nutzerergebnis** liefern, anhand eines echten vollständigen Staffellaufs samt Negativkontrollen abnehmen und im produktiven Routing bevorzugen. Fehlgeschlagene Kandidaten und Ursache dokumentieren, später separat etwa auf einem x86-VPS evaluieren; keine ungeprüfte Behauptung, ein VPS löse das Problem.
4. Statusmeldungen nennen erreichte **Funktionen und Nachweise**, nicht nur installierte Tools, grüne Einzeltests oder vermeintliche Autonomie. Scheitert ein Provider, darf nicht die gesamte Fabrik zum Stillstand kommen, wenn ein nachgewiesen sicherer Ersatz verfügbar ist.

**Block 6 – priorisierte Arbeitsrichtung ab 01.10.2026:** FFmpeg als bereits nachgewiesener unabhängiger Video-Render-/Audio-/Caption-Pfad, Remotion als mögliche ergänzende Animationsstufe. Clip-Erstellung funktional über tatsächlich überprüfte Kandidaten abdecken: Chopify als Kandidat prüfen; ggf. PySceneDetect/Auto-Editor und FFmpeg nach echten Tests. **Chopify ist nicht allein aufgrund der Nennung LIVE oder integriert.** OpenChatCut und SupoClip sind für den derzeitigen Abschluss *keine zwingenden Abhängigkeiten*, bleiben separate spätere Evaluierungskandidaten, gegebenenfalls auf VPS. Privates R2 ist dauerhafter **Objektspeicher**, kein Ausführungsserver; tatsächlichen FFmpeg-Produktionsstandort separat nachweisen. OmniRoute bleibt bis zu neuer Entscheidung zurückgestellt.

**Wiederaufnahme:** Diese Regel bei jedem neuen Chat, /BLOCKRUN, Projekt-Handover und vor neuer Werkzeugwahl zusammen mit dem jeweils **aktuellen** MASTER-SNAPSHOT lesen. Ältere Snapshots, Roadmaps und unverifizierte Toolnamen dürfen diese neuere Arbeitsentscheidung nicht überschreiben. Eine laufende Automation ersetzt keine dauerhafte interaktive Entwicklungs-/Rechnerausführung; tatsächlichen Status immer neu verifizieren.

## BLOCKRUN: Fehlerbudget und Werkzeug-Fallback (03.10.2026)

- Bei demselben reproduzierbaren technischen Fehler maximal **drei** gezielte Reparatur- und Testversuche; ein **vierter** nur bei einer neuen, durch Logs/Code belegten und dokumentierten Ursachenhypothese.
- Bleibt die Funktion defekt: Werkzeug **PAUSED**, Befunde dokumentieren, den **bereits verifizierten** Ersatz gemäß `docs/TOOL_INDEX.md` einsetzen und den beauftragten Block damit fortsetzen. Kein erneutes Experiment mit dem pausierten Tool ohne neue technische Erkenntnis; keine Kosten ohne Freigabe.
- Der Wechsel darf niemals Wahrheits-/Sicherheits-/Rechteprüfungen, R2-Privatsphäre, Revisionsbindung, Human Approval oder CI/Red-Team umgehen. Funktionslücken des Ersatzes bleiben explizit offen.
- Stand 03.10.: **Block 6 FFmpeg-first**, OpenChatCut **PAUSED**, SupoClip **PAUSED**. Block 8/9 auf vorhandenen FFmpeg-/R2-/Dashboard-Wegen abschließen; erfolgreiche Tests nicht erneut erfinden.

## Cloudflare-Container: bestehender Tarif und Freigabe (03.10.2026)

- Bülent bestätigt: bestehender Cloudflare Workers/Containers Paid-Tarif kostet **5 USD pro Monat** und Containerzugriff ist bereits freigeschaltet. Für die beauftragte private Whisper-Installation darf die bestehende bezahlte Container-Infrastruktur verwendet werden; keine erneute Grundsatzfreigabe für diesen bereits bezahlten Zugang verlangen.
- **Wichtig:** Die 5-USD-Grundgebühr belegt keine unbegrenzte Container-Laufzeit oder kostenfreie zusätzliche CPU-/RAM-Nutzung. Vor einem zusätzlichen Container/Rollout tatsächliche Kapazität, Abrechnungsmodell und mögliche Mehrkosten prüfen. Keine neuen kostenpflichtigen Ressourcen oder Tariferhöhungen ohne ausdrückliche Freigabe.
- Bei Installations-Gates die bestehende Tarif-Freigabe von der separaten Prüfung möglicher Mehrkosten unterscheiden. Zugangsdaten niemals in Repository, Logs oder CI-Artefakte schreiben. Cloudflare-Deployment und erfolgreicher Live-Test separat nachweisen.

### Verifizierte Tarifabgrenzung (Cloudflare-Dokumentation, 03.10.2026)

- Workers Paid: 5 USD/Monat Grundgebühr, inkl. 25 GiB-h RAM, 375 vCPU-min aktive CPU, 200 GB-h Container-Disk, EU-Netzwerkausgang 1 TB; danach nutzungsabhängige Gebühren. Offizielle Quelle: https://developers.cloudflare.com/containers/platform/pricing/
- Konfiguriertes Whisper `standard-2`: 1 vCPU, 6 GiB RAM, 12 GB temporäre Container-Disk; bei ununterbrochenem Betrieb wären bereits nach ca. 4 h 10 min die 25 GiB-h RAM-Inklusivmenge ausgeschöpft. **Kein 24/7-Betrieb** im Grundpreis; `sleepAfter=5m` nutzen, echte monatliche Gesamtnutzung aller Container kontrollieren.
- Contabo Cloud VPS 6 ist ein *separates, derzeit nicht als gekauft bestätigtes* Angebot mit 6 vCPU, 12 GB RAM, 200 GB SSD; keinesfalls mit Cloudflare-Workers-Paid verwechseln. https://contabo.com/de/pricing/
- `ASR_NO_EXTRA_COST_APPROVED` darf nur auf true gesetzt werden, wenn der konkrete Installations- und Testlauf anhand verfügbarer Inklusivkontingente/Abrechnung als ohne zusätzliche Kosten bestätigt ist. Die vorhandene 5-USD-Grundgebühr allein reicht dafür nicht aus.


## Container-Aufwecken vor Arbeitsaufträgen – verbindliche Architekturregel (03.10.2026)

- Jeder Dashboard-, Telegram- oder Agenten-Befehl, der **tatsächlich Containerarbeit** auslöst (z. B. privates Whisper-ASR oder FFmpeg), muss über eine gemeinsame, wiederverwendbare Container-Dispatch-/Readiness-Schicht laufen. Nicht für jeden Knopf separate Warm-up-Logik kopieren.
- Reihenfolge: **explizite Berechtigung/Einwilligung prüfen → denselben zuständigen Container adressieren und bei Bedarf wecken → echte Dienst- und Modellbereitschaft prüfen → Auftrag genau einmal übergeben → tatsächlichen Verarbeitungsstatus getrennt melden**. Bei Bereitschaftsfehler keine vorgetäuschte Annahme. Keine blinden Wiederholungen nicht-idempotenter POST-Aufträge; begrenzte Retries ausschließlich für sichere Readiness-Probes.
- **Nur lesende Aktionen** wie „Transkript abrufen“ (R2-GET) dürfen keinen Container aufwecken. „Einwilligen“ darf nach expliziter Freigabe die Bereitschaft prüfen und den privaten ASR-Auftrag starten. Ein grüner Deploy oder HTTP-/health-200 allein beweist noch keinen erfolgreichen Transkriptionslauf.
- Diagnose: sichere feste Fehlerstufe und numerischen HTTP-Status erfassen; **keine** Audiodaten, Transkripttexte, Owner-IDs, Tokens oder internen Upstream-Antwortkörper in Logs/CI. Private Medien niemals in GitHub-Runnern verarbeiten; für Ende-zu-Ende-Tests synthetische DE/TR-Dateien verwenden. Widerruf muss laufende und spätere Speicherung wirksam sperren.
- Vor Integration anderer Container-Tools diese Regel erneut anwenden. Kostenkontingente prüfen; kein dauerhaftes Warmhalten, keine neuen kostenpflichtigen Ressourcen ohne Freigabe. Ein Architekturprinzip ist erst **implementiert**, wenn zugehörige Laufzeitintegration und Tests tatsächlich nachgewiesen sind.
