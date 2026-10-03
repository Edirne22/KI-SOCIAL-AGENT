# BLOCKRUN – 24/7-Produktion, Ressourcensteuerung und Telegram-Text, 2026-10-03

Status: HANDOVER / nicht als abgeschlossen markieren. Keine privaten Audiodaten in GitHub oder CI. Keine automatischen Social-Veröffentlichungen.

## Priorisierte Abnahme
1. PR #365: Textglossar und saisonbezogene Fahrerlisten, synthetische DE/TR-Textfixtures und Offline-Vergleichsprogramm. tests/test_asr_compare.py wurde ergänzt. CI/Red-Team und echter synthetischer Audiovergleich stehen noch aus; daher nicht ungeprüft mergen. Keine Produktiv-Glossaraktivierung.
2. Telegram-TEXTeingang: Nutzer diktiert mit der Telegram-/Handy-Tastatur; Telegram sendet bereits transkribierten normalen Text. KEIN Telegram-Voice-Download, KEIN zusätzlicher Whisper-Schritt. Bestehenden authentifizierten Telegram-Text-Webhook und /ki-Ingress verwenden; natürliche DE/TR-Aufträge verstehen (Thema/Fahrer, Zeitfenster, Reel/Clip/Post/Karussell, Plattformen); mehrdeutige oder publikationsrelevante Anweisungen bestätigen; Jobstatus, private Vorschau und Dashboard-Player-Link an Telegram zurückgeben. Bestehende Textkommandos und Approval-Regeln unverändert. Whisper nur für Quellvideo-Audiospuren im Recherche-/Medienworkflow.
3. Block 8: kontrollierter idempotenter Neurender nach fehlgeschlagenem Job, Retry-Limit und sichtbarem Dashboard-Status, Player und private Vorschau prüfen.
4. Block 6: bestehende freigegebene News-Quellen verwenden, Source-Fact-Contract und Series-Lock beibehalten, 3–4 redaktionelle Kandidaten erzeugen, rechtmäßig nutzbare Medien/Alternativgrafiken, privates Preview und Telegram-Approval. Keine Veröffentlichung ohne Nutzerfreigabe.

## 24/7-Betriebsmodell (verbindliche Zielarchitektur, noch nicht E2E bestätigt)
- Kontinuierlich recherchieren, neue Funde persistent erfassen, deduplizieren und redaktionell vorprüfen. Nicht auf einen einzigen Morgen-Batch warten.
- Der Resource Manager ist derzeit `content_factory_local_resource_manager.py` und ausdrücklich LOCAL_EPHEMERAL_ONLY. Vor 24/7-LIVE ist eine durable, atomare Jobwarteschlange mit Leasing, Heartbeats, Timeout-Recovery und idempotenten Task-IDs nötig. Keine behauptete verteilte Produktionssteuerung ohne Implementierung und Lasttest.
- Ampel: GRÜN erlaubt normale Parallelrecherche, GELB hält neue schwere ASR/Render-Jobs zurück, ROT blockiert neue schwere Jobs und alarmiert bei dauerhaftem Rückstau. Schwellen anhand realer Container- und API-Telemetrie kalibrieren.
- Anfangs konservativ maximal ein schwerer Renderjob gleichzeitig und keine zweite schwere ASR-Arbeit parallel, bis Messungen mehr Kapazität bestätigen; Recherche und redaktionelle Arbeiten dürfen innerhalb eigener Limits weiterlaufen. Ein dedizierter Produktionsleiter priorisiert Nutzereingaben, zeitkritische Nachrichten, bereits angefangene Jobs und Ressourcen.
- Nutzereingabe über Telegram ist NORMALER TEXT aus Handy-/Telegram-Diktat, nicht Telegram-Audio. Natürliche Nachfrage „Habt ihr etwas Neues zum Posten?“ gibt sofort den aktuellen Bestand und den Status laufender Arbeiten zurück. Individueller Textauftrag wird eingereiht und bestätigt; private Vorschau/Player-Link nach Fertigstellung; kein Auto-Publish.
- Morgenübersicht ungefähr 07:00–08:00 Europe/Berlin ist eine zusätzliche Zusammenfassung des bis dahin vorhandenen Stands, keine Sperre für Zwischenabfragen und kein Beweis für 24/7-LIVE.
- Telegram-Bot-Rückmeldungen: Eingang/Job-ID, QUEUED/RUNNING/READY/FAILED, aktuelle wartende Aufgaben und Ampel; keine geheimen R2-URLs ohne Authentifizierung.
- Ausfall-/Restart-/Duplikat-/Lasttests sowie Quoten- und Kostenlimits vor Freigabe.

## Laufende Abnahme / goldener Teller
- Beweis je Stufe: Workflow-Run/Commit, privater Job-ID-Status, sichtbares Dashboard-Preview und Telegram-Nachricht; nicht aus grünem Workflow allein auf funktionierende End-to-End-Pipeline schließen.
- Positivkontrollen: gültiger diktierter DE/TR-Textauftrag, reguläre Textkommandos, ein lizenzfreier Testclip, erfolgreiche private Vorschau.
- Negativkontrollen: fremder Telegram-Absender, wiederholtes Update, unverständlicher oder mehrdeutiger Textauftrag, Quellvideo-ASR-Container schläft, Render-Timeout, ungesicherte Quelle und unerlaubtes Fremdvideo.
- Kosten: free-first, keine neue kostenpflichtige Infrastruktur ohne Freigabe.
- Zeitplan: kontinuierliche Recherche und bedarfsgerechte Auslieferung plus morgendlicher Überblick 07:00–08:00 Europe/Berlin; bestehende Trigger prüfen, keine Lieferung oder 24/7-LIVE zusagen, solange E2E- und Lasttests fehlen.

## Bedienkonzept: Telegram-first, Dashboard als ergänzendes Studio
- Zielverteilung der Bedienung: ca. 90 % Telegram, 10 % Web-Dashboard. Das ist eine UX-Vorgabe, kein gemessener Ist-Wert.
- Nutzer diktiert mit dem Telefon, versendet normalen Telegram-TEXT; natürliche DE/TR-Aufträge ohne starre Befehlsform. Sofortige Eingangsbestätigung mit Job-ID, Status und bei Bedarf geschätzter Warteschlangenposition (keine erfundenen Fertigzeiten).
- Ergebnislieferung primär als Telegram-Vorschau (soweit Telegram-Dateigrenzen, Rechte und Privatsphäre das zulassen), andernfalls als geschützter mobilfreundlicher Dashboard-Deep-Link mit eingebettetem Player.
- Deep-Link öffnet einen authentifizierten Preview-Kontext (kein öffentliches R2-Objekt und kein langfristiges Geheimtoken in Telegram). Dort: Freigeben / Überarbeiten / Ablehnen. Telegram kann dieselben drei Aktionen über authentifizierte Callback-Buttons anbieten.
- Beide Oberflächen nutzen EINEN revisionsgebundenen, unveränderlichen Freigabevorgang. Doppelklick, alte Revision, fremder Absender, abgelaufener Link und widersprüchliche Entscheidungen fail-closed behandeln; alle Entscheidungen auditieren. 'Überarbeiten' erfasst Änderungswunsch und erzeugt eine neue private Vorschau, keine automatische Publikation.
- On-demand-Abfrage in Telegram liefert jederzeit READY-Entwürfe und aktuelle QUEUED/RUNNING-Status. Morgendliche Zusammenfassung ist zusätzlich, nicht exklusiv.
- Implementierung erst nach Vergleich mit bestehendem Telegram-Approval und Dashboard-Preview; keine redundante zweite Freigabe-Logik bauen. Private Ende-zu-Ende-Abnahme auf echtem Mobilgerät erforderlich.
