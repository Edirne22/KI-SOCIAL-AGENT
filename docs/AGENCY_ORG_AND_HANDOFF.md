# Edirne 22 – verbindliche Organisations- und Übergabearchitektur

**Status 02.10.2026:** Dieses Dokument ordnet die bereits vorhandenen Rollen, Module und geplanten Verbindungen. Ein dokumentierter Ablauf ist kein Beleg für bereits produktive automatische Ausführung. `PROJECT_GUARDRAILS.md` und tatsächlicher Code/CI/LIVE-Test gehen vor.

## Hierarchie und Verantwortlichkeit
| Ebene | Verantwortlicher | Entscheidung / Übergabe | Was diese Rolle nicht darf |
| --- | --- | --- | --- |
| Geschäftsführung | Bülent | Ziel, externe Publikation pro Beitrag, neue Ausgaben, Verträge, private Mediennutzung und wesentliche Regeländerungen | Keine implizite Freigabe durch KI-Vorschläge |
| Zentrale Auftragsannahme | Bestehendes Dashboard, Telegram und validiertes R2-Inbox-Schema | Nutzeridentität, Task-ID/Revision, Berechtigungen, gewünschte Einzel-KI, Prüfgates, privates Ursprungsmaterial | Rohtexte/Modelloutput als Autorisierung behandeln |
| Betriebsleitung | **Produktionsleiter** (vollständige zentralisierte Laufzeit erst nach Test) | DAG, Verantwortlicher, Priorität, Übergaben, Deadlines, Fehlerzustand, Retry/Resume und Abschlussbericht; vor Maschinenstart Vollständigkeit des Creative-Maschinenvertrags prüfen | Freigaben, Faktenbeweise oder Kostenentscheidungen ersetzen; unvollständige Creative-Prosa als produktionsbereit markieren |
| Technische Kapazität | **Deterministischer Ressourcenmanager** (gemeinsamer Dienst noch ausstehend) | Nachgewiesene API-Quoten, CPU/GPU/RAM/Container-Readiness, Storage-Limits, Lease-/Queue-Zustand und Kostenlimits | Aus fehlenden Messdaten vermeintliche Kapazität ableiten |
| Redaktion und Facharbeit | Content-Strategie, Research/Newsroom, Creative/Bülent Writing, Formatagenten, Tour-Agent, Media-/AV-Maschinen | Revisionsgebundene evidenzbasierte Ergebnisse und klare Next-Hop-Übergaben | Fremde Fakten erfinden, eigene finale Publikationsautorität beanspruchen |
| Technische Entwicklung | Maschinen-Scout (20), Research/Lizenz/Security, KI-Integrationsingenieur (19) | Maschinenfund → unabhängige Bewertung → isolierter Build/PR → kontrollierter Werkzeugindex | Funde eigenständig installieren, kostenpflichtig buchen oder Sicherheitsgates abschalten |
| Unabhängige Kontrollinstanzen | Fakten-/Quellen-QM, Rechte-QM, technische Security-/CI-/Red-Team-Gates, finales Media-QM | Exakte negative/positive Kontrollen und prüfbaren Freigabezustand dokumentieren | Auf Zuruf „grün“ melden; Agent 09 System-Quality allein ist kein Fakten-QM |
| Menschliche Endkontrolle | Goldenes Tablett → Bülent | Entscheidet genau auf gezeigter Job-/Revision-/Asset-Hash-Basis: ändern, verwerfen oder posten | Alte Versionen stillschweigend durch neue ersetzen |
| Außenwirkung | Bestehender Publisher/Engagement-Reply-Adapter | Nur konkret und revisionsrichtig genehmigte Aktion plus atomare Publisher-ID/Receipt | Selbstständiges Social Publishing, automatische Neuversuche bei mehrdeutigen Versandfehlern |
| Nachbereitung | Memory Curator (14) und Betriebs-/Qualitätsbericht | Evidenzgebundene Fehler, Tests, Nutzerkorrekturen, Kosten-/Werkzeugmessungen an zuständige Teams zurückgeben | Unbewiesene Trends zu sicheren Fakten oder Schutzregelüberschreibungen erklären |

**Organisationsprinzip:** Pro Auftrag genau eine verantwortliche Betriebsleitung, pro konkretem Arbeitsschritt genau ein verantwortlicher Ausführender; weitere Modelle dürfen nur begrenzt als fachlicher Challenger/Reviewer hinzugezogen werden. Sicherheitsgates bleiben unabhängig und sind niemals nachträglich durch einen Text-Agenten aufhebbar.

## Content-Fabrik: verbindlicher Ziel-Staffellauf
```
gültiger Auftrag / zulässiger Discovery-Kandidat
 -> eindeutige kanonische ProductionJob-ID / Revision / Provenienz
 -> Planner + Kapazitäts- und Berechtigungsreservierung
 -> Source Ingest / Transkript je tatsächlich vorhandener Fähigkeit
 -> Research / FACT PACKAGE / unabhängige Quellprüfung
 -> Creative Director + Bülent Writing
 -> verbindlicher Maschinenvertrag: Szenen + Timing/Pacing + Asset-Slots + Effekt-/Motion-IDs + Transition-IDs/-Dauer + Overlay-/Audio-Regeln + Soll-Evidence
 -> Media/Story bindet autorisierte Assets an den Maschinenvertrag
 -> nur nötige Plattform- und Video-/Musik-/Tour-Ausführung
 -> Media/Audio/Avatar-Adapter nur soweit isoliert technisch nachgewiesen
 -> Media-Manifest (R2 private, Hash, MIME, Revision)
 -> unabhängige finale Fact-/Media-/Rights-/Technical-QM
 -> revisionsgebundenes privates Goldenes Tablett
 -> Bülent: ändern / verwerfen / posten
     ändern: idempotente neue Revision → gezielte Bearbeitung → erneutes QM → neues privates Preview
     verwerfen: keine externe Ausgabe
     posten: exakter Approval-Hash → durable atomare Publisher-Reservierung → echter Receipt
 -> belegbare Analytics/Korrekturen ins evidenzgebundene Memory
```
Im aktuellen Stand ist der echte revidierte Creative-Render nach gültigem CHANGE noch offen (Issue #326). Block9 benötigt echte sichere Publisher-E2E-Abnahme; **Tests mit synthetischen Daten dürfen niemals Plattformposts auslösen**.

## Verbindlicher Format-/Stil-Preflight für Medienrollen
Alle Rollen, die Medien konzipieren, formatieren, schneiden, vertonen, auswählen oder für eine Render-Maschine vorbereiten, müssen **vor Arbeitsbeginn** Zielmedium/Plattform, Format, Seitenverhältnis, Zieldauer, Stil/Tonalität, Creative-Revision sowie relevante Szenen-, Overlay- und Audio-Regeln aus dem aktuellen Auftrag prüfen. Widerspruch/Fehlen => `NOT_READY_FOR_MEDIA`; keine stillen Defaults und kein Maschinenstart. Diese Metadaten werden revisionsgebunden durch jede Übergabe mitgeführt.

## Verbindliche Creative→Maschine-Schnittstelle
Die Stellenbeschreibung [Creative Director / Kreativmanager](../agents/CREATIVE_DIRECTOR.md) ist für alle Medienproduktionen verbindlich. Kreative Prosa ist nur Briefing. Der Creative Director muss sie in einen revisionsgebundenen ausführbaren Maschinenvertrag übersetzen. Der Produktionsleiter darf den Maschinenstart erst freigeben, wenn dieser Vertrag vollständig ist. Renderer geben Ist-Evidence zurück; finales Media-QM vergleicht Soll gegen Ist und schlägt bei fehlenden Pflichtfeldern fehl.

## Universelle KI-Werkstatt
Ein Auftrag aus demselben Dashboard/Telegram-Eingang benötigt eigene Job-ID/Revision, Ressourcen- und Datengrenzen. Abhängig von benötigter Fähigkeit wählt der derzeit nur teilweise vorhandene Skill-/Provider-Router belegbar verfügbare Bild-/Voice-/Dokument-/Coding-/Recherche-Lanes. `forced_provider` oder ausdrückliche Toolwahl ist ein harter Lock ohne heimlichen Ersatz. Ein Katalogeintrag ist kein realer Berechtigungs- oder Kostenbeleg. Werkstatt und Content-Fabrik dürfen keine Job-/R2-Identitäten vermischen; selbst bei Ressourcenknappheit müssen Steuerung und menschliche Freigaben erreichbar bleiben.

## Forschung und Technik: gegenseitiger Arbeits-Loop
```
Produktionsfehler / Kapazitätsmangel / neue Funktionslücke / neue Releases
 -> Scout 20 (nur wirklich neue, deduplizierte Kandidaten und Angebote)
 -> Research 05 und unabhängige Lizenz-/Kosten-/Security-Prüfung
 -> Produktionsleiter erstellt begrenzten technischen Testauftrag
 -> KI-Integrationsingenieur 19 plant minimalen Adapter und führt isolierten Build
 -> unabhängige positive / negative / CI / Red-Team / Regression / tatsächliche E2E-Abnahme
 -> je Berechtigung kontrollierter PR-/Merge-/Deploy-Schritt
 -> genau eine aktive Auswahlliste docs/TOOL_INDEX.md + datierter Radar + evidenzgebundenes Memory
 -> Scout bekommt gemessene Schwachstellen und sucht gezielt weiter
```
Maschinen-Scout in der Bibliothek ist eine **Rollenbeschreibung** und sein eigener GitHub-24/7-Prozess bleibt bis nachgewiesener Aktivierung `ROLE_ONLY`. Der separat eingerichtete stündliche Preisradar ist kein Beleg für den gesamten Scout.

## Klare Grenzen und ältere Konflikte
- Strategischer Social-Agent 04 entscheidet Thema und Plattform, **nicht** Cloud-Runner-Auslastung, Docker-Betrieb oder GitHub-PR-Merges.
- Research 05 sammelt/belegt; `content_factory_newsroom.py` ist die deterministische überprüfte Wahrheitsschnittstelle; Creative produziert daraus keine neuen vermeintlichen Fakten.
- Video Optimization 07 erstellt Schnittkonzepte, Media-Adapter führen technisch aus, Final-QM prüft – keiner publiziert selbstständig.
- Agent 09 liefert System-/Betriebsstatus, darf Fakten- und Produktions-QM weder ersetzen noch „grün“ nachbuchen.
- Agent 11 startet ausschließlich explizit zugelassene Wartungs-/Analyseflows und niemals gesperrte Telegram-/Publisher-/Medien-Lanes.
- Agent 14 lernt nachweislich; Memory hat niemals höhere Autorität als Hard-Safety-/Human-Approval-Gates.
- Ältere Doku nennt Facebook Engagement „Agent 18“, heute bezeichnet `18_tour_ride_story_agent.md` Tour Ride Story; dieser Konflikt muss bei alten Befehlen über eindeutigen Rollennamen oder eine später getestete Alias-Migration aufgelöst werden. **Niemals allein anhand „18“ ausführen.**
- `AGENTS.md` ist historisch teilweise überholt (OmniRoute-first, generelles Merge-/Fix-Verbot); bei Widersprüchen gelten aktuelle `PROJECT_GUARDRAILS.md`, belegte aktuelle Beschlüsse und sichere konkrete Bereichsfreigaben. OmniRoute bleibt PAUSED.

## Nachweismatrix (nicht pauschal auf „LIVE“ hochstufen)
- Revisions- und Job-Handoff: Contract-Code vorhanden, Tests separat bestätigen.
- Content Core, newsroom, Creative, FFmpeg→privates R2, technischer Dashboard-Preview: isolierte Nachweise vorhanden.
- Persönlicher neuer Videostudio-UI-Test, komplettes CHANGE→Re-Render→Neues QM/Preview/Benachrichtigung: nicht voll abgenommen.
- DE/TR synthetische CPU-ASR/TTS: auf GitHub-Runner nachgewiesen; keine private reale Stimm-/Avatar-Produktionskette.
- Coding-Routing: einzelne geprüfte Live-Modellantworten und begrenzte Probeläufe, **kein** pauschal autonomer Schreib-/PR-Agent.
- Social-Engagement und scheduled Analytics: tatsächlicher Job-Status und Berechtigung pro Run prüfen.
- Vollständiger übergreifender deterministischer Produktionsleiter + Ressourcenmanager + Parallel-Content/Werkstatt-E2E: **OPEN**.

## Nächste Abnahmereihenfolge
1. Rollenindex und Sicherheits-Handoff statisch testen; keine doppelte ID oder unbelegte LIVE-Markierung. Alte Archiv-/Agentenbezeichnungen nur mit expliziter Alias-Regel.
2. Bestehende Tasks/R2-/Factory-Verträge für deterministischen zentralen Planner und Ressourcen-Reservierungen **wiederverwenden** statt zweiten Controller neu bauen. Unabhängig offline testen.
3. Zwei gleichzeitige unterschiedliche Aufträge simulieren: ein Content-Job und ein Werkstatt-Job; künstliche Quota-/Containerfehler, stale revision, duplizierte Events, Retry nach Crash, harte Freigabesperre prüfen; dann erst echten isolierten Cloud-Staffellauf.
4. Offenen Revision-Render (#326) und echte Block9-Sicherheitsabnahme separat vollständig nachweisen. Block7 privates Material erst nach Eigentümer-Upload/Einwilligung.
5. Berichte und ausgewertete Engpässe an Memory und Scout zurückführen, ohne Produktions- oder Nutzer-Freigaben selbstständig zu ändern.

Keine 100-%-Effizienz ohne gemessene Baseline und Lasttests behaupten. Erfolg bedeutet reproduzierbares Routing und nachgewiesene Fähigkeit, Kosten/Kapazität/Recoveries belastbar zu messen.


## Einheitlicher Medien-Maschinenvertrag – Laufzeitregel
Für alle Medienproduktionen gilt: Eine ungefähre Nutzerlaufzeit ist ohne ausdrückliches `EXACT` eine Obergrenze. Beispiel „ca. 5 Minuten“ => `duration_policy=MAXIMUM`, `max_duration_seconds=300`; 3:00, 4:00 oder 4:30 sind zulässig, wenn der Creative Director dies aus Material, Dramaturgie, Effekten und Audio begründet. Produktionsleiter, Media/Story, Audio, Renderer und QM verwenden dieselbe Contract-Revision und dieselben Zeit-/Szenenfelder. QM prüft die Vertragsgrenze und kreative/technische Evidence, nicht eine erfundene Mindestlänge. Der Creative Director verteilt Zeit eigenständig zwischen Assets und Szenen; lokale Überlänge wird durch kreative Neuverteilung gelöst und ist kein Produktionsabbruchgrund.
