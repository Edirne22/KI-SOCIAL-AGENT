# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 16.09.2026, Abendübergabe  
**Snapshot-Version:** v4 (Dokumentrevision; Gesamtarchitektur v6, Produktion Racing V8.5.5, separater V8.6-Debug)  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`


## Racing – Abendstand und Branch-Grenzen

Diese v4-Dokumentrevision wurde aus dem im Repository vorhandenen MASTER-SNAPSHOT
(Gesamtarchitektur v6 vom 15.09.) und den verifizierten Abendbefunden aufgebaut.
Eine als v3 oder v4 bezeichnete Datei war bei der Prüfung weder auf main noch im
Debug-Branch vorhanden. Der Debug-Snapshot dokumentierte noch Lauf #12.

- **main:** gezielter Final-Guard-Fix, keine Übernahme des V8.6-Debug-Codes.
- **debug/motogp-pipeline-output:** ausschließlich gelesen; manuelle Änderungen
  des Nutzers weder überschrieben noch erweitert.
- Backup vor dem main-Fix: `backup/main-before-final-guard-2026-09-16`,
  Ausgangscommit `7de0fd20b65167ec45687d841fdc6d07bb7b9b34`.
- Final-Guard-Fix: [942171f8ff816b21a5031a05e82cfa365a199e42](https://github.com/Edirne22/KI-SOCIAL-AGENT/commit/942171f8ff816b21a5031a05e82cfa365a199e42).
- Acht deterministische Final-Guard-Regressionstests und Kompilierung bestanden.
  Die Tests sind zusätzlich im Agency-Workflow-Preflight eingehängt.
  Ein neuer produktiver Live-Lauf mit dem Fix wurde hier nicht gestartet.

### Final-Guard-Bug auf main: Ursache und gezielter Fix

`racing_final_guard.py::expected_series()` nutzt eigene Regex-/Namenslisten,
nicht `racing_cfo.series_mentions()`. Vor dem Fix wurde „Agius“ der Moto2 zugeordnet,
bevor das spätere MotoGP-Matching greifen konnte. Dadurch blockierte der Chief-QM
selbst korrekte MotoGP-Debüt- und Profil-Posts.

Jetzt hat eine eindeutige explizite Seriennennung im Titel Vorrang vor Summary,
Feed-Metadaten und Fahrerhistorie. Bei mehreren Klassen im Titel wird keine neue
pauschale MotoGP-Zuordnung geraten; die bisherige Fallback-Logik bleibt bestehen.
Insbesondere bestehen am Final-Guard:
- „Tech3 signs Agius for MotoGP debut from 2027“ mit korrektem MotoGP-Metadatum/Hashtag.
- „Who is Senna Agius? Meet Australia's new MotoGP star“.

Das ist ein PASS dieses Guards, keine Garantie für einen PASS aller übrigen
inhaltlichen, sprachlichen, Medien- und Chief-QM-Prüfungen. Falsche Hashtags,
Promo-Inhalte und andere bestehende Schutzprüfungen bleiben blockiert.

Der vor dem Fix gestartete [Agency-Lauf #42](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35151695745)
belegt dieselbe Fehlzuordnung für beide Agius-Titel. Er endete mit
`current_q=4, fallback_q=0, final=2, status=BLOCKED`.
Die Übergabe erwähnt einen früheren Lauf mit fünf qualifizierten Kandidaten;
diese Zahl wird nicht mit dem separat geprüften Lauf #42 gleichgesetzt.

### Warum final=2 trotz Copy-QM und Bildern BLOCKED bleibt

`motogp_content_agency_v2.py::run_v8()` erstellt Session und Telegram-Vorschläge
nur bei `len(picks)==5`. Copy-QM-PASS bedeutet lediglich, dass ein Kandidat
in den Auswahlpool darf. `select_and_finish()` prüft danach noch Serienmix,
Duplikate, Batch-QM und `finish_item()`; dort kommen Medien und Chief-QM hinzu.

`finish_item()` erzeugt das Bild **vor** dem Chief-QM. Deshalb können bereits
Bilder entstanden sein, obwohl die betreffenden Pakete anschließend ausscheiden.
Bei weniger als fünf Endpaketen wird die Freigabe-Session ausdrücklich auf
`QM: FAIL / Approval-Status: BLOCKED` gesetzt. Der Run Controller übernimmt
diesen Status. Es gibt dann keine Freigabe-Vorschläge, aber der Code sieht eine
Statusnachricht über die zu geringe Anzahl vor (mit Benachrichtigungsbegrenzung).

**Entscheidung unverändert:** Nach aktueller Fünfer-Batch-Regel ist BLOCKED bei
final=2 korrekt. Zwei qualifizierte Pakete dennoch anzubieten wäre eine Änderung
des Produktverhaltens und bedarf Bülents Entscheidung. Keine Schwelle geändert.

### Debug: Provider-Variabilität als bekannte Einschränkung

Der beste dokumentierte Abendwert ist **9/14 PASS** in
[Diagnostic #21](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35147500872),
Diagnose-ID `motogp-2026-09-16-a88cf39ab8`,
Checkout `1b284a28f34e41e4d9a4f536ff98ca91c0d0e107`.
9/14 ist ein Spitzenwert, keine stabil reproduzierte Freigabequote.

Besonders aussagekräftig sind zwei Läufe mit demselben Checkout
`bafdf6cf47733c10fc9e5cb91d9dad553c54276e`:
- [#19](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35144939679):
  Diagnose-ID `cb85f4e77b`, **5/14 PASS**.
- [#20](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35146716708):
  Diagnose-ID `d78d92ecdd`, **9/14 PASS**, andere PASS-Kandidaten.

Das zeigt Variabilität trotz identischem Code. Agnes-Modellantworten und
QM-Bewertungen sind nicht als deterministisch zu behandeln. Die Live-Quellen
wurden jedoch nicht als identischer eingefrorener Datensatz nachgewiesen;
Provider-Zufall ist deshalb nicht als alleinige Ursache quantifiziert.
Zusätzlicher älterer Befund aus #12: identischer Caption konnte nach abgelehnten
Patches bei erneuter Semantic-QM-Bewertung später PASS erhalten.

Spätere geprüfte Läufe:
- [#22](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35149313500):
  Checkout `48255aeb7354e744017a3a4d96a4a236b81d01bb`, **6/14 PASS**.
- [#23](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/35150391122):
  Checkout `b8b0f393582d86691ec8359b717467a3b57bcc89`, **6/14 PASS**.

Die Run-Metadaten zeigen hier main, der Workflow checkt jedoch explizit den
Debug-Branch aus. Maßgeblich ist der im Job-Log dokumentierte Checkout-SHA.
Alle genannten Ergebniszahlen stammen aus Job-Logs; keine vollständige neue
inhaltliche Artefaktanalyse wird behauptet.

### Sechs strukturelle Problemklassen im Debug

1. `patch too broad`: Reparatur überschreitet erlaubten Umfang.
2. `invalid or no-op replacement`: ungültige oder wirkungslose Ersetzung.
3. `old span must occur exactly once`: Originalstelle fehlt oder ist mehrdeutig.
4. `Hashtag-Anzahl nicht 4–7`: Formatprüfung verwirft Kandidaten.
5. Erfundenes oder verschärftes Faktenwissen trotz CFO.
6. Grammatik- und Tippfehler im Editor-Output.

Die ersten vier Klassen sind in den geprüften Abendlogs direkt sichtbar.
Die letzten beiden bleiben als Befunde der übergebenen Tagesanalyse dokumentiert;
ihre genaue Häufigkeit/Einzelfälle wurden in dieser Abendprüfung nicht neu aus
den Artefakten bestimmt. Semantic-QM bleibt streng.

Laut Nutzerübergabe wurden tagsüber Fixes 1/3/4/6 eingebaut und Fix 5 zurückgenommen.
Die Fix-Nummerierung und die Formulierung „6 Fixes“ sind kein hier neu verifiziertes
Commit-Inventar. Hashtag-Whitelist, Nationalitäten-Anpassung und weitere manuelle
Debug-Änderungen wurden nicht verändert. Kein Debug-Fixversuch in diesem Auftrag.

### Weitere Statusprüfungen

- **Race-Calendar:** `race/race_calendar.py` enthält weiterhin Diagnose-Ausgaben
  für fehlenden API-Key, Modellversuch, HTTP-Status, Exception-Typ und fehlende
  Antwort sowie begrenzte Ausgabe nicht parsebarer Antworten. Keine Änderung.
  HTTP 429/Quota ist die in der Übergabe gemeldete Diagnose; ein neuer Provider-Test
  wurde nicht ausgelöst. JSON-/Architektur-Umbau bleibt ein späterer Auftrag.
- **eBay:** Vorhandensein von `EBAY_CLIENT_ID` und `EBAY_CLIENT_SECRET` konnte
  nicht verifiziert werden. Der verfügbare GitHub-Connector unterstützt keine
  Secrets-Metadaten-Abfrage; der Browserzugriff scheiterte technisch beim Start.
  „Ungeprüft“ bedeutet weder „gesetzt“ noch „fehlend“. Keine Werte gelesen oder
  geloggt; keine Integration gebaut. Die Exemption ist laut Übergabe weiter offen.
- Freigabe-Check, Doppelpost-Schutz, Locking, Apify-Fallbacks und Publisher wurden
  nicht verändert.

## Leitbild
Der KI-SOCIAL-AGENT recherchiert, prüft, formuliert, bereitet Medien vor, veröffentlicht nur nach persönlicher Freigabe und lernt anschließend aus Nutzerentscheidungen, eigenen Ergebnissen und technischen Fehlern. **Neu in v6: geschlossenes selbstlernendes Feedback-Memory mit Audit-Trail und Konfidenzregeln.**

## Architektur
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

Der frühere v6-Stand sah drei Vorschläge vor. Der aktuelle Produktionspfad verlangt fünf vollständig qualifizierte Pakete; siehe Racing-Abendstand oben.

## Rechte-/Quellen-Gate
Keine routinemäßige zweite Nutzerabfrage. Fakten eigenständig formulieren; fremde Rennmedien nicht ungeprüft übernehmen. Facebook nutzt bevorzugt offiziellen Link/Link-Preview; Instagram eigenes/zulässiges Medium. Unklare Medienrechte → sichere Alternative.

## Telegram / Publisher
Die aktuelle Freigabe-Session nennt `motogp 1` bis `motogp 5`, Kombinationen, `motogp alle` und `motogp nein`. Nach Freigabe entstehen getrennte Instagram-/Facebook-Blöcke `FREIGEGEBEN`. Bestehende Publisher bleiben an Freigabe + Publication-Claims gebunden. Erfolgreiche Veröffentlichungen werden mit Plattform-ID dokumentiert.

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

## Weiterer Backlog aus dem bisherigen Snapshot
Die folgenden älteren Punkte werden durch diese Abendprüfung nicht als neu geprüft oder erledigt erklärt. Aktuell zuerst den gezielten main-Guard-Fix im nächsten regulären Lauf beobachten; keine Debug-Umbauten und keine Änderung der Fünfer-Schwelle ohne Entscheidung.

1. Closed-Loop Memory ersten echten Workflow-Lauf prüfen und Event-/Regel-/Context-Ausgabe gegen Quellen validieren.
2. Zweiten MotoGP-Agency-Test nach Redaktions- und Memory-Update durchführen.
3. Eigene Analytics-Daten stabil befüllen; erst dann Performance-Hypothesen automatisch befördern.
4. Telegram-Ablehnungen künftig noch feiner als explizite Feedback-Events mit Grund erfassen, sofern Nutzer einen Grund mitsendet.
5. Facebook-Link-Preview im Real-Post prüfen.
6. `content/PUBLISHED.md`-Historie separat verlustfrei reparieren.
7. Follow-Analyse-Anbieterfehler stabilisieren.

## Leitbild
> **„Bülent entscheidet. Das System merkt sich belegte Entscheidungen und Ergebnisse, lernt kontrolliert daraus und nutzt dieses Wissen beim nächsten Lauf – ohne Sicherheits- oder Freigaberegeln selbst abzuschwächen.“**
