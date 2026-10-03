# Edirne 22 – Medienfabrik: ASR als Teil der End-to-End-Pipeline

Status: Architekturkonzept, kein Produktions-Deployment.

## Zielbild
Freigegebene YouTube-/Web-Quellen entdecken → Medien und verfügbare Untertitel rechtmäßig auswerten → offline DE/TR-ASR mit Zeitstempeln → Themen und Fakten mit Quellen prüfen → 3–4 interessante Geschichten auswählen → geeignete, rechtmäßig nutzbare Videoausschnitte/Screenshots oder eigene Grafiken erstellen → Editor/Chief-QM → Telegram und Dashboard-Vorschau („goldenes Tablett“) → ausschließlich nach Bülents Freigabe veröffentlichen.

## ASR und Wörterbuch
- Fachwortlisten für Motorradtechnik, MotoGP, Moto2, Moto3, WorldSBK, WorldSSP, türkische und deutsche Umgangssprache sowie Namen von Fahrern, Teams, Strecken und Modellen getrennt versionieren.
- Die Quelle jeder neuen Bezeichnung dokumentieren; Namen und Schreibweisen mit offiziellen Profilen abgleichen.
- Glossar als begrenzten, kontextabhängigen Hinweis für das Modell verwenden, nie als erzwungene Textersetzung. Längere allgemeine Wortlisten helfen nicht automatisch und können Halluzinationen fördern.
- Transkripte mit Segment-/Wortzeitstempeln, Sprache, Confidence soweit zuverlässig verfügbar, Quell-URL und Medien-Zeitbasis speichern. Sprecherwechsel und DE/TR-Code-Switching gesondert testen.
- Bei Untertiteln: Lizenz/Verfügbarkeit prüfen und Originaluntertitel mit ASR vergleichen, statt sie blind als Wahrheit zu behandeln.

## Automatisierte Auswahl
- Discovery bewertet Aktualität, Relevanz und Quellenqualität, trennt dokumentierte Fakten von Spekulation und Duplikaten.
- Pro Geschichte: belegte Aussage, Quelllinks, Zeitfenster, Lizenzstatus, verwendete Ausschnitte, offene Unsicherheiten und editorische Begründung.
- Cutter erhält exakte Zeitbereiche und nur freigegebene Medien; ansonsten eigenes Bildmaterial, neutrale Grafiken oder Link-/Zitat-Vorschläge. Ein öffentliches Video ist keine automatische Reupload-Erlaubnis.
- Ressourcenmanager startet Container vor zeitkritischen Transkript-/Renderjobs, wartet auf Readiness, begrenzt parallele Jobs und behandelt Timeout/Retry idempotent.
- Freigabe-Gate bleibt Pflicht; kein autonomes Veröffentlichen.

## Nächste messbare Meilensteine
1. Glossar aus bereits registrierten Fachquellen fortlaufend erweitern und bereinigen.
2. Offline-Vergleichsskript und synthetische lizenzierte DE/TR-Testaudios erstellen; WER/CER, Eigennamen, unbegründete Einfügungen und Code-Switching messen.
3. Testcontainer mit selektiven Glossar-Prompts und zeitgestempelten Segmenten abnehmen; produktiven Container unverändert lassen.
4. Ende-zu-Ende-Test mit rechtmäßig nutzbarem Testvideo: Quelle → Audio → Transkript → Zeitfenster → drei redaktionelle Kandidaten → Vorschaurender → privates Dashboard/Telegram, ohne Veröffentlichung.

Keine privaten Sprachdaten in GitHub/CI, keine neuen Kosten ohne Freigabe, kein ungeprüftes Kopieren fremder Inhalte.
