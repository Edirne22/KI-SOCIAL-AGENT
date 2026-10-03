# Entwicklungsagent – Grundwissen V1

## Vor jedem Auftrag
1. PROJECT_GUARDRAILS.md und MASTER-SNAPSHOT.md im aktuellen HEAD lesen.
2. Aktuellen main, offene PRs und vorhandene Tests prüfen. Vorhandene Arbeit weiterverwenden; keine konkurrierenden Branches oder Doppelimplementierungen.
3. Nur explizit freigegebene Issue- und Dateipfade bearbeiten. Unklare Anforderungen: gesperrten Status ausgeben, nicht raten.
4. Niemals persönliche Telegram-Medien, R2-Originale, Zugangsdaten oder vollständige private KI-Ausgaben in GitHub-Artefakte, Logs oder Modell-Prompts kopieren.

## Auftrag #369: Telegram-Alben
- Telegram sendet Album-Elemente als einzelne Updates. Nur das erste Element kann die Beschriftung `/privat` tragen.
- Ein Projekt muss mindestens Besitzer/Chat und `media_group_id` unterscheiden. Ein Zeitstempel allein ist keine Identität.
- Nicht freigegebene oder noch nicht eindeutig zugeordnete Elemente dürfen niemals in die alte Vision- oder Social-Pipeline gelangen.
- Originaldateien bleiben unveränderlich und privat in R2. SHA-256 nach dem Upload durch erneutes Lesen überprüfen.
- Manifest-Änderungen gegen gleichzeitige Updates absichern; wiederholte Telegram-Updates dürfen keine doppelten Medien erzeugen.
- Unterbrochene Uploads müssen wiederaufnehmbar sein. Unvollständige Alben nicht als fertig melden.
- Nachträgliche Ergänzungen referenzieren eine eindeutige Projekt-ID. Neurendern erzeugt eine neue Revision, niemals eine stille Überschreibung.
- Keine automatische Veröffentlichung und keine private externe KI-Inferenz ohne gesonderte Freigabe.

## Arbeitsfolge und Stoppschilder
ANALYSE → MINIMALER PATCH → SYNTHETISCHE REGRESSION → SICHERHEITSTEST → CI → REVIEW → BEWACHTER MERGE/DEPLOY → NACHWEIS.
- Tests: 10 synthetische Fotos, 5 synthetische Videos, gemischte und verspätete Ankünfte, Dubletten, konkurrierende Updates, Neustart, getrennte Chats, fehlende Beschriftung bei Folgeelementen, kein Vision-/Social-Leck.
- Fehler erzeugen permanente Regressionstests. Nicht grünfärben oder fehlerhafte Prüfungen abschalten.
- Bestehende R2-/Telegram-Schnittstellen wiederverwenden, keine zweite Entwicklungsumgebung oder neuen bezahlten Anbieter anlegen.
- CI-Erfolg ist kein Beweis für einen Telegram-End-to-End-Test. Erfolg nur mit echtem Laufbeleg melden.

## Kontext- und Token-Effizienz
Zuerst Dateiliste und Schnittstellen prüfen, dann nur relevante Funktionen und Tests lesen. Kleine, überprüfbare Patches statt vollständiger Neugenerierung. Testergebnisse und Fehlermeldungen präzise festhalten. Keine unnötigen parallelen Agenten oder Provider-Aufrufe.

Diese Datei ist ein überprüfbares Arbeitsbriefing, kein Ersatz für die verbindlichen Guardrails und keine automatische Codefreigabe.
