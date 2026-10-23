# Codeprüfung Racing / Turkish Rider / Instagram / Daily Content

Basis: acbee54cedf22cca02a002e135f661aed2fd9870 (PR 664, 666, 667 zusammengeführt).

Scope: geänderte Datenpfade und direkte Übergaben, nicht die gesamte KI-Fabrik. Nutzer verlangt keine CI-/Regressionstestläufe. Deshalb statische Prüfung, Syntax-/Konfigurationsparser und Shell-Syntax, keine Funktions-/API-Tests. Keine Veröffentlichung.

## Befunde und Korrekturen

1. telegram_router._publish_instagram_pending rief Meta auf, bevor ein passender PUBLISHED.md-Block gesucht wurde. Jetzt vor jeder API-Anfrage genau einen passenden unmarkierten Instagram-Block verlangen; Batch, Auswahl, Status, Titel, Bild und Caption müssen passen. Bereits reservierte Blöcke bleiben dem Publisher vorbehalten. Fehlender, widersprüchlicher oder doppelter Eintrag: keine Veröffentlichung, Pending bleibt erhalten.
2. Daily Ideas akzeptierte nichtleere, aber unvollständige Antworten. Vor Speicherung müssen exakt Beiträge 1–3 mit den angeforderten ausgefüllten Feldern vorhanden sein. Fehler verändern weder Plan noch Historie. Der Router verwirft für daily_ideas Antworten mit finish_reason=length und versucht den nächsten vorhandenen Provider.
3. MotoGP bestätigte die gesamte Auswahl als freigegebene Pakete, selbst wenn die Duplikatprüfung alle verworfen hatte. Rückmeldung benennt jetzt die verarbeitete Auswahl und die tatsächliche Anzahl neuer Plattform-Blöcke.

## Endliche Prüfmatrix

| Bereich | Nachweis / Ergebnis |
|---|---|
| Zusammenführung | Aktuelles main gelesen; Quellbild-Weitergabe, FREIGEGEBEN-Status, Sieben-Tage-Fenster und vollständiger Abruf vorhanden |
| Python-Syntax | 12 beteiligte Module mit ast.parse gelesen; keine Imports oder Tests |
| Konfiguration | 5 Workflow-YAMLs und Provider-JSON erfolgreich geparst; keine GitHub-Schemavalidierung behauptet |
| Persistenzskript | bash -n erfolgreich; keine Git-Kommandos des Skripts ausgeführt |
| Turkish | sichtbare fünf gespeichert; explizite Liste merkt Reserve; Quell-/Datums-/Dedupe-Gates bleiben bestehen |
| Termine | Daily und Racing 08:00 Europe/Berlin; Racing-Nachmittagsstarts nicht gesperrt; Scheduler-Pünktlichkeit offen |
| Instagram | statische Vorprüfung vor API; kompletter Live-Publish nicht ausgeführt |
| Daily-Ausfall | Fehler werden vor Dateischreiben propagiert; Schema- und Längenprüfung ergänzt |
| CI / Regression / Live | NICHT AUSGEFÜHRT, ausdrücklich vom Nutzer ausgeschlossen |
| Kosten / neue Dienste / private Medien | N/A: keine Änderung |

## Offene Betriebsrisiken und Grenzen

- GitHub-Schedule kann verspätet auslösen; Codeprüfung garantiert keine 08:00-Zustellung.
- Direkter Telegram-Publisher und regulärer Publisher haben keine gemeinsame atomare Transaktion mit Meta. Ein Absturz nach Meta-Erfolg vor dauerhaftem Git-Status kann Wiederholungsrisiken hinterlassen. Die Vorprüfung verkleinert dieses Risiko, beseitigt es nicht vollständig.
- Racing-Telegram-Text wird nach Git-Persistenz versendet; Turkish-Fotos werden im Agency-Prozess bereits vorher geschickt. Ein Persistenzfehler kann deshalb bereits sichtbare Fotos ohne dauerhafte Session hinterlassen.
- Community-Fallbacks tragen in write_session Semantic-Fakten-QM N/A; parse_session verlangt PASS. Diese bestehenden Community-Einträge sind somit nicht über diese Racing-Freigabe auswählbar. Keine automatische Lockerung der Fakten-Gates in diesem Patch.
- Daily-Generator kann Racing-Ideen erzeugen; telegram_morning filtert diese bewusst aus der allgemeinen Freigabe. Ein vollständiger Plan bedeutet daher nicht zwingend drei allgemeine Telegram-Angebote.
- Frühere fälschlich als angeboten markierte Reserve wird nicht pauschal aus der Historie gelöscht; das könnte echte Wiederholungen erlauben.

Kein 100%-Freigabevermerk: statisch geprüfter Teilumfang mit den oben benannten verbleibenden Laufzeit-/Architekturlücken.
