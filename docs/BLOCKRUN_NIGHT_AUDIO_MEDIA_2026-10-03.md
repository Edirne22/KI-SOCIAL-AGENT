# BLOCKRUN – Nachtproduktion und Telegram-Audio, 2026-10-03

Status: HANDOVER / nicht als abgeschlossen markieren. Keine privaten Audiodaten in GitHub oder CI. Keine automatischen Social-Veröffentlichungen.

## Priorisierte Abnahme
1. PR #365: Textglossar und saisonbezogene Fahrerlisten, synthetische DE/TR-Textfixtures und Offline-Vergleichsprogramm. tests/test_asr_compare.py wurde ergänzt. CI/Red-Team und echter synthetischer Audiovergleich stehen noch aus; daher nicht ungeprüft mergen. Keine Produktiv-Glossaraktivierung.
2. Telegram-Audioeingang: authentifizierte Telegram-Voice/Audio-Updates erkennen; eindeutige Update-ID deduplizieren; Datei nur über privaten Pfad abrufen, Upload-/Dauer-/Formatgrenzen und Berechtigungen erzwingen; private R2-Inbox; Container vor ASR warm-up/readiness; DE/TR-Transkript mit Zeitstempeln; Befehlserkennung mit Unsicherheits- und Bestätigungsgate; Text und Fehlerstatus in Telegram und Dashboard zurückmelden. Bestehende Textkommandos und Approval-Regeln unverändert.
3. Block 8: kontrollierter idempotenter Neurender nach fehlgeschlagenem Job, Retry-Limit und sichtbarem Dashboard-Status, Player und private Vorschau prüfen.
4. Block 6: bestehende freigegebene News-Quellen verwenden, Source-Fact-Contract und Series-Lock beibehalten, 3–4 redaktionelle Kandidaten erzeugen, rechtmäßig nutzbare Medien/Alternativgrafiken, privates Preview und Telegram-Approval. Keine Veröffentlichung ohne Nutzerfreigabe.

## Nacht-Abnahme / goldener Teller
- Beweis je Stufe: Workflow-Run/Commit, privater Job-ID-Status, sichtbares Dashboard-Preview und Telegram-Nachricht; nicht aus grünem Workflow allein auf funktionierende End-to-End-Pipeline schließen.
- Positivkontrollen: gültiger DE/TR-Sprachbefehl, reguläre Textkommandos, ein lizenzfreier Testclip, erfolgreiche private Vorschau.
- Negativkontrollen: fremder Telegram-Absender, wiederholtes Update, große/ungültige Audiodatei, unverständlicher oder mehrdeutiger Sprachbefehl, Container schläft, Render-Timeout, ungesicherte Quelle und unerlaubtes Fremdvideo.
- Kosten: free-first, keine neue kostenpflichtige Infrastruktur ohne Freigabe.
- Zeitplan: morgendlichen bestehenden Workflow auf korrekte Zeit/Zeitzone prüfen; keine Lieferung zusagen, solange End-to-End-Test fehlt.
