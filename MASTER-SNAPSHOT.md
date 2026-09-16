# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 16.09.2026, nach Live-Diagnostic #12  
**Version:** Gesamtarchitektur v6 / Racing-Debug V8.6 (Regression, nicht produktionsreif)  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`


## Aktueller Racing-Stand – verbindliche Übergabe

- Arbeitsbranch: `debug/motogp-pipeline-output`. Produktions-`main` nicht auf V8.6 umstellen.
- Funktionierende Vergleichsbasis V8.5.7: [b360a29c74970cf8ef29edb75410619354c9bac8](https://github.com/Edirne22/KI-SOCIAL-AGENT/commit/b360a29c74970cf8ef29edb75410619354c9bac8).
- Implementierter V8.6-Code: [03cc6c28b415246e26313719e6ed1f392942c18c](https://github.com/Edirne22/KI-SOCIAL-AGENT/commit/03cc6c28b415246e26313719e6ed1f392942c18c).
- V8.6 ist im Live-Test gegenüber V8.5.7 deutlich zurückgefallen. Ein grüner Workflow bestätigt die technische Durchführung, nicht die redaktionelle Qualität.
- Editor (`final_captions`) und Semantic-QM (`racing_semantic_qm`) verwenden in der getesteten Kette Agnes. Ein OpenAI-Modellwechsel ist keine durch diesen Lauf belegte Lösung.
- Dieser Snapshot-Stand dokumentiert Ergebnisse und offene Arbeiten; die unten beschriebenen nächsten Fixes sind noch nicht implementiert.

### Implementierte V8.6-Kette

```
Titel/Zusammenfassung + explizite Serien-/Feed-Metadaten
→ Canonical Fact Object (CFO) vor dem Editor
→ Editor
→ deterministischer Entity/Number/Series Guard + Whitelist
→ Racing-QM → Guards bei QM-Änderungen erneut
→ strenge Semantic-QM gegen Quelle + CFO
→ bei Fehler maximal zwei exakte Text-Patches
→ nach jedem Repair erneut Guards und QM
→ PASS / REJECT / TECHNICAL-DEFER
```

Das CFO enthält mindestens `series`, `event`, `session`, `riders`, `entities`,
`teams`, `manufacturers`, `locations`, `dates`, `positions`, `numbers`,
`relationships`, `claims`, `modality` und `forbidden_inferences`.
Quellenauszüge mit Positionen, Quellenhash und eine unabhängige Kopie sichern die Faktenbasis.
Keine ergänzten Vornamen, Klassenzuordnungen oder sonstigen Fakten aus Vorwissen.
Unbekannte Felder bleiben leer. Claims und Beziehungen sind konservativ als
Quellentext bzw. explizite Marker erfasst, noch kein vollständig aufgelöster Wissensgraph.

Repair-Format: `{"patches":[{"old":"exakte Textstelle","new":"Ersatz"}]}`.
Der deterministische Merge verwirft mehrdeutige, überlappende, zu große und ungültige
Patches atomar. Keine freie Komplett-Neugenerierung und keine erneute Recherche
als Repair-Fallback. Fahrer-Hashtags werden nicht mehr aus Vorwissen erweitert.
Semantic-QM bleibt zwingend; nur echte JSON-Boolean-Werte `true` gelten als PASS.

Die lexikalischen Guards sind keine universelle Entitäts-/Bedeutungserkennung.
Unbekannte Entitäten, ausgeschriebene Zahlen und komplexe Beziehungen können
weiterhin die unabhängige Semantic-QM benötigen. Konservative Regeln können auch
korrekte Formulierungen abweisen; das muss anhand der Diagnose geprüft werden.

Wichtige Dateien: `racing_cfo.py`, `racing_v855_hardening.py` (kompatibler Install-Einstieg),
`racing_semantic_qm.py`, `motogp_quality_manager.py`,
`motogp_pipeline_diagnose.py`, `racing_cfo_selftest.py`, `docs/RACING_V86.md`.
Die V8.6-Dokumentation wurde vor dem Live-Lauf geschrieben; dessen Ergebnisse
und die aktuelle Freigabeentscheidung stehen hier.

### Tests und Live-Ergebnisse

Lokale Kompilierung sowie fünf Offline-Suiten bestanden:
`racing_cfo_selftest.py` (23 Tests),
`racing_pipeline_selftest.py`, `racing_v85_selftest.py`,
`motogp_pipeline_audit_selftest.py`, `motogp_date_recovery_selftest.py`.
Abgesichert sind unter anderem Agius→Aras, Gonzalez→Gonzales,
WorldSBK→WorldSSP, San Marino→Mugello, P1→Meisterschaftsführung/Q1,
neue Zahlen, Hashtag-Umgehungen, Quellenmutation und ungültige Patches.
Diese Offline-Tests haben die reale Patch-Antwortqualität nicht ausreichend abgebildet.

| Version | Relevante Kandidaten | PASS | Reject | PASS-Quote | Laufzeit ungefähr |
|---|---:|---:|---:|---:|---:|
| V8.5.5 | 13 | 5 | 8 | 38 % | 11 Min. |
| V8.5.6 | 14 | 3 | 11 | 21 % | 15 Min. |
| V8.5.7 | 14 | 9 | 5 | 64 % | 11 Min. |
| V8.6 | 14 | 2 | 12 | 14 % | 9 Min. |

Frühere Vergleichswerte stammen aus dem dokumentierten Debug-Verlauf.
Nachrichten und Provider-Antworten können sich zwischen Läufen ändern;
das ist kein kontrollierter Benchmark mit identischen Eingaben.

[Diagnostic #12](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35126591173)
ist anhand des Job-Logs geprüft:
- Checkout tatsächlich `03cc6c28b415246e26313719e6ed1f392942c18c`.
- Workflow wurde über `main` gestartet, checkt dort aber ausdrücklich den Debug-Branch aus.
  Der in der Run-Metadatenansicht gezeigte main-SHA ist deshalb nicht der geprüfte Code-SHA.
- 204 nach Deduplizierung / 204 extrahiert → 14 frisch/relevant → 2 PASS, 12 Reject,
  0 technische Defer, 2 Top10-Kandidaten; Roster 22.
- Diagnose-Schritt inklusive Recherche: ca. 8 Min. 46 Sek.; Job insgesamt ca. 9 Min.
- PASS: Gonzalez-Rennbericht im ersten Versuch; WorldSBK-Regel-Roadmap im dritten Versuch.
- 18 protokollierte Patch-Ablehnungen: 15 JSONDecodeError,
  zweimal zu großer Patch-Umfang, einmal nicht eindeutig gefundene Originalstelle.
- Eine zusätzliche Editor-Antwort scheiterte an fehlender Hook/Body/Question-Struktur.
- WorldSBK erhielt erst bei der dritten Bewertung PASS, obwohl beide Patches
  abgelehnt wurden: unveränderter Text wurde erneut semantisch bewertet.
  Diese Wiederholungslogik darf keinen zufälligen späteren PASS ermöglichen.
- Die genaue Ursache der ungültigen JSON-Antworten (z. B. Formatierungsrahmen,
  sonstiger Text oder abgeschnittene Antwort) ist noch nicht abschließend bestimmt.
  JSONDecodeError allein beweist sie nicht.
- #12 führte die zwei bisherigen Audit-/Date-Recovery-Selftests aus.
  Die fünf auf dem Debug-Branch erweiterten Workflow-Tests wurden nicht automatisch
  Teil des von main geladenen Workflow-Plans. Die 23 CFO-Tests sind lokal belegt,
  nicht als ausgeführte Tests dieses GitHub-Laufs.

Alle fünf Diagnose-Dateien wurden hochgeladen:
`motogp-pipeline-audit.jsonl`, `motogp-stage-summary.json`,
`motogp-rejections.jsonl`, `motogp-qm-results.json`, `motogp-top10.json`.
[Artefakt #10459970950](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35126591173/artifacts/10459970950).
Die bisherigen Felder bleiben kompatibel; QM-Ergebnisse ergänzen CFO,
Guard-Fehler/-Historie und Repair-Historie.
Die obige Live-Auswertung basiert auf dem Job-Log; eine vollständige
inhaltliche Auswertung der heruntergeladenen ZIP-Dateien steht noch aus.

### Nächster konkreter Entwicklungsschritt – offen

1. Reale Repair-Antworten und Verarbeitungsfehler nachvollziehbar und ohne Secrets
   diagnostizieren; vorhandene Guard-/Repair-Artefakte pro Kandidat auswerten.
2. Strikte Patch-Verarbeitung robust gegen erlaubte Ausgabeformatierung machen.
   Nur vollständiges, schema-valides JSON akzeptieren; keine erfundenen Ergänzungen
   bei abgeschnittenen Antworten und kein Wechsel zur freien Neugenerierung.
3. Abgelehnte oder wirkungslose Patches dürfen bei identischem Text und gleicher
   Faktenbasis keine neue inhaltliche QM-Bewertung bis zum zufälligen PASS auslösen.
   Technische Provider-Retries davon getrennt behandeln.
4. Reale Antwortformen und den WorldSBK-Fall als deterministische Regressionstests ergänzen;
   Guard-Fehlalarme untersuchen, ohne die Semantic-QM abzuschwächen.
5. Danach erneut Diagnostic auf dem Debug-Branch starten, Checkout-SHA und ausgeführte
   Tests kontrollieren; Qualität, Repair-Erfolg und Laufzeit gegen V8.5.7 vergleichen.
6. Erst nach belastbarem Live-Nachweis über eine Produktionsübernahme entscheiden.

Kein Beleg aus #12 für den Memory Curator als Fehlerursache. Pauschale Versprechen
wie „80 % weniger Fehler durch Modellwechsel“ oder „Code beim ersten Versuch
fehlerfrei“ sind keine Projektbefunde. Quellenextraktion und Sprachstil bleiben
wichtige Themen, ersetzen aber die Reparatur der konkret gescheiterten Schnittstelle.

## Leitbild
Der KI-SOCIAL-AGENT recherchiert, prüft, formuliert, bereitet Medien vor, veröffentlicht nur nach persönlicher Freigabe und lernt anschließend aus Nutzerentscheidungen, eigenen Ergebnissen und technischen Fehlern. **Neu in v6: geschlossenes selbstlernendes Feedback-Memory mit Audit-Trail und Konfidenzregeln.**

## Gesamtarchitektur (v6-Leitbild)
```
Web / MotoGP / Trends
        ↓
Quellenprüfung + Roster
        ↓
MEMORY_CONTEXT + Creator / Strategist / MotoGP Agency
        ↓
Profilformat + Quality + Rechte-Gate
        ↓
Telegram-Vorschau → EINE Freigabe
        ↓
PUBLISHED.md = FREIGEGEBEN → Publisher
        ↓
Plattform-ID + Analytics + Quality + Fehler/Duplikate
        ↓
Agent 14 Memory Curator
        ↓
MEMORY_EVENTS → LEARNED_RULES → MEMORY_CONTEXT
        └──────────────────────────────► nächster Content-Lauf
```

## Agent 14 – Closed-Loop Memory Curator
Dateien: `agents/14_memory_curator.md`, `memory_engine.py`, `.github/workflows/memory-learning.yml`.

### Vier Memory-Schichten
- `memory/MEMORY_EVENTS.jsonl`: append-only Audit-Ereignisse (Nutzerkorrekturen, Publishing, Performance, Fehler, Wiederholungen).
- `memory/LEARNED_RULES.md`: kuratierte Regeln mit Evidenz/Konfidenz.
- `memory/MEMORY_CONTEXT.md`: kompaktes aktives Kontextpaket, das Content-Agenten vor der Erstellung lesen.
- `memory/MEMORY_HEALTH.md`: Datenlage, Regel-/Eventstatus und Schutzprüfung.

Bestehende Spezial-Memories wie `PERFORMANCE`, `POST_HISTORY`, `VIRAL_PATTERNS`, `HOOKS_THAT_WORK`, `USER_PREFERENCES`, `QUALITY_*`, `EXPERIMENTS` bleiben erhalten und dienen als Evidenzquellen.

### Evidenz-/Lernregeln
- Direkte Nutzerkorrektur und harte Sicherheits-/Freigaberegel: hohe Konfidenz, sofort nutzbar.
- Eindeutig dokumentierter technischer Fehler/Duplikat: präventive Workflow-Regel.
- Eigene Performance: nur mit echter Reichweite und mehreren vergleichbaren Datensätzen; Korrelation bleibt Hypothese, keine Kausalitätsbehauptung.
- Externe Trends/Engagement: Inspiration, niemals automatisch persönliche Präferenz.
- Fehlende Daten werden nicht geschätzt.
- Konflikte werden nicht still überschrieben; Safety/Brand/Freigabe haben Vorrang.
- Memory darf niemals `FREIGEGEBEN` setzen oder Publisher starten.

### Aktuelle Bootstrap-Learnings
Der erste MotoGP-Agency-Test vom 15.09.2026 hat bereits als direkte Nutzerkorrektur gelernt: Quelle ist Faktenbasis, nie Textvorlage; englische Rohtexte/Web-Metadaten entfernen; Social-Text komplett neu/natürlich auf Deutsch; keine Standard-Hook-/CTA-Dauerschablone. Zusätzlich wurden dokumentierte Textduplikate und wiederholte Hooks als präventive Regeln übernommen.

## Content Creator / Strategist
`generate_ideas.py` und `weekly_plan.py` lesen jetzt das Closed-Loop `MEMORY_CONTEXT`. Tagesideen lesen zusätzlich `memory/MOTOGP_DAILY_CONTENT.md`. Priorität: Safety/Brand/Quellen > Nutzerkorrektur > eigene kuratierte Performance > externe Inspiration. Wiederholte Hooks und Themen werden gegen POST_HISTORY geprüft; Performance wird nicht erfunden.

## MotoGP-Roster
- `motogp_roster_updater.py` prüft den aktiven 2026-Roster gegen offizielle MotoGP-Seiten plus Crosscheck.
- Erfolgreicher Real-Lauf 15.09.2026: 22 Stammfahrer verifiziert; `content/MOTOGP_ROSTER.md` erzeugt.
- `MOTOGP_ROSTER_NEXT.md` bleibt separate Zukunftsvorschau; unvollständig ersetzt nie den aktiven Roster.
- Gerüchte/Wildcards/Test-/Ersatzfahrer werden nicht als reguläre Stammfahrer übernommen.

## Agent 13 – MotoGP Content Agency (historischer v6-Stand)
Die Agency liest jetzt `MEMORY_CONTEXT`, berücksichtigt jüngste Fahrer-/Themenhäufigkeit als Rotationssignal und besitzt ein zusätzliches Text-Qualitäts-Gate. Aktualität kann Rotation überstimmen. Quelle bleibt Faktenbasis; fertige Telegram-Texte müssen eigenständig deutsch sein.

Der frühere v6-Ablauf sah bis zu 12 Themen und drei Vorschläge vor. Die weiterentwickelte Racing-Kette zielt auf fünf qualifizierte Vorschläge aus MotoGP, Moto2, Moto3, WorldSBK, WorldSSP und gegebenenfalls WorldSSP300. Der aktuelle Debug-Diagnostic endet nach Copy-QM und Ranking, ohne Telegram, Media-Publishing oder Freigabeänderungen. Aktueller Implementierungs- und Fehlerstand: siehe Racing-Übergabe oben.

## Rechte-/Quellen-Gate
Keine routinemäßige zweite Nutzerabfrage. Fakten eigenständig formulieren; fremde Rennmedien nicht ungeprüft übernehmen. Facebook nutzt bevorzugt offiziellen Link/Link-Preview; Instagram eigenes/zulässiges Medium. Unklare Medienrechte → sichere Alternative.

## Telegram / Publisher
MotoGP: `motogp 1`, `motogp 2`, `motogp 3`, `motogp alle`, `motogp nein`. Nach Freigabe entstehen getrennte Instagram-/Facebook-Blöcke `FREIGEGEBEN`. Bestehende Publisher bleiben an Freigabe + Publication-Claims gebunden. Erfolgreiche Veröffentlichungen werden mit Plattform-ID dokumentiert.

## Content-Regeln
- Ride With Me max. 1x/Kalenderwoche.
- MotoGP-Fahrer einzeln fokussieren und Roster rotieren.
- Locker, menschlich, per Du; Deutsch als Basis, Türkisch gezielt.
- Keine Nachrichtenagentur-/KI-Schablonensprache.
- Professionelle relevante Hashtags; kein Spam.
- Keine erfundenen Fakten, Ergebnisse, Transfers, Zitate, Trends oder Quellen.

## Automatisches Learning-Timing
`Closed Loop Memory Learning` läuft täglich um 17:45 UTC nach den vorgesehenen Analytics-/Viral-Reports und ist zusätzlich manuell startbar. Er verändert ausschließlich Memory-Dateien, nicht Freigaben oder Publisher.

## Sicherheitsnetz
Keine selbstmodifizierenden Safety-Regeln. Keine Secrets/private Chats im Learning-Memory. Keine automatische Veröffentlichung aus einem Lernsignal. Keine Käufe/Buchungen/Anmeldungen durch Recherche-Agenten. Externe Inhalte werden nicht kopiert.

## Weiterer Backlog aus v6 (Status hier nicht erneut verifiziert)
Die Racing-Reparatur und deren Live-Nachweis haben aktuell Vorrang. Folgende ältere Punkte bleiben als Backlog erhalten; sie werden durch diesen Snapshot nicht als neu geprüft oder erledigt erklärt.

1. Closed-Loop Memory ersten echten Workflow-Lauf prüfen und Event-/Regel-/Context-Ausgabe gegen Quellen validieren.
2. Zweiten MotoGP-Agency-Test nach Redaktions- und Memory-Update durchführen.
3. Eigene Analytics-Daten stabil befüllen; erst dann Performance-Hypothesen automatisch befördern.
4. Telegram-Ablehnungen künftig noch feiner als explizite Feedback-Events mit Grund erfassen, sofern Nutzer einen Grund mitsendet.
5. Facebook-Link-Preview im Real-Post prüfen.
6. `content/PUBLISHED.md`-Historie separat verlustfrei reparieren.
7. Follow-Analyse-Anbieterfehler stabilisieren.

## Leitbild
> **„Bülent entscheidet. Das System merkt sich belegte Entscheidungen und Ergebnisse, lernt kontrolliert daraus und nutzt dieses Wissen beim nächsten Lauf – ohne Sicherheits- oder Freigaberegeln selbst abzuschwächen.“**
