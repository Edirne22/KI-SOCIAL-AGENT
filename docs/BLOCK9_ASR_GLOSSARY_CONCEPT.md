# Block 9 – DE/TR-ASR-Wörterbuch: Umsetzungskonzept

Status: KONZEPT + SYNTHETISCHE FIXTURES. Keine produktive Aktivierung ohne Benchmark und Freigabe.

## Ziel
Offline faster-whisper bei gesprochenem Deutsch/Türkisch und Motorrad-/Rennsport-Eigennamen messbar verbessern. Das Audio bleibt privat; kein Cloud-ASR, kein automatisches Umschreiben erkannter Wörter.

## Datenfluss
1. Quellen aus `tests/fixtures/asr_motorcycle_glossary.json.research_source_registry` einzeln prüfen (Erreichbarkeit, Lizenz, aktuelle Terminologie). Nur kurze, eigenständig kuratierte Wörter/Namen mit Quellen-URL, Sprache, Kategorie und Prüfstatus erfassen; keine Artikel oder Wörterbuchdefinitionen kopieren.
2. Normalisieren: UTF-8, türkische Zeichen (ı/i, İ/I, ğ, ş, ç, ö, ü), Dubletten und Varianten getrennt behandeln; offizielle Schreibweise von Fahrern/Teams/Modellen mit offiziellen Quellen abgleichen. Eigennamen, Technik, Rennsport und Umgangssprache getrennt pflegen.
3. Statische, versionierte JSON-Quelle statt harter Laufzeit-Liste. Review vor Aufnahme. Änderungen an Quellen dürfen keine automatischen Produktionsprompts erzeugen.
4. Für einen Transkriptionsauftrag nur einen kleinen, passenden `initial_prompt` wählen (Sprache, Motorrad- oder Rennsportkontext); harte Längenbegrenzung, deterministische Auswahl, Fallback auf die bisherige bewährte Vier-Begriffe-Liste. `initial_prompt` ist ein Hinweis, keine garantierte Worterkennung.
5. Qualität: synthetische, lizenzierte DE/TR-Audios mit Referenztranskript getrennt von Text-Fixtures erstellen; alte gegen neue Erkennung auf exakt denselben Aufnahmen vergleichen (WER/CER, Eigennamen, falsch eingefügte Wörter, DE/TR-Mischsätze). Niemals persönliche Aufnahmen in GitHub/CI.
6. Gate: Regression, Unicode, Injection-Resistenz bei Quellenimport, Offline-/Consent-/R2-Grenzen, Image-Preflight und positive Kontrolle; nur bei messbarem Nutzen in den Container integrieren. Dockerfile und Deploy-Staging müssen die freigegebene JSON-Datei explizit mitliefern.
7. Rollout: zunächst Testcontainer, dann explizite Freigabe für produktives Deployment. Keine Zusatzkosten oder externen Sprachdienste.

## Quellenpriorität
- Türkische Motorradlexika: Motorcular, Motosiklet Defteri (nur einzelne unabhängig formulierte Term-Paare).
- Türkische Fachpresse: Motoetkinlik, TMF, Motoron, Motorsport Türkiye, TRMotoSports, TRF1; F1TR als unbestätigter Kandidat.
- Schreibweisen: offizielle MotoGP-/WorldSBK-/TMF-Profile.
- Deutsche Gegenbegriffe: Motorsport Magazin und ServusTV; Übersetzungen fachlich prüfen.
- Mozilla Common Voice ausschließlich als gesondert lizenzierter möglicher Testdatensatz, nicht als kopiertes Wörterbuch.

## Abnahmekriterien
- Quellen- und Lizenzstatus pro neuem Begriff nachvollziehbar.
- Kein regressiver WER/CER-Trend gegenüber der bisherigen Version auf DE und TR; Eigennamen separat ausweisen.
- Keine halluzinierten Namen durch zu aggressive Prompts.
- Bestehender privater Produktionscontainer bleibt bis zur Freigabe unverändert.
