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

---

**Pflegeprinzip:** Neue dauerhaft relevante Fehlerklassen, Arbeitsregeln und Schutzmechanismen werden in dieser Datei ergänzt, damit sie unabhängig von einzelnen Chats und Handovers erhalten bleiben.
