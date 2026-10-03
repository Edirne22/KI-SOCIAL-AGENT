# DE/TR Telegram + Dashboard: Befehls- und Mehrdeutigkeitsregel V1

Status: verbindliche Entwurfsregel; Integration und Live-Abnahme separat nach CI. Gilt für getippte Nachrichten, Browser-Diktat und private Whisper-Transkripte gleichermaßen.

## Nicht raten
- Nur explizit freigegebene, eindeutig einem Intent zugeordnete Alternativbegriffe verwenden. Keine phonetische oder semantische Vermutung als Ausführungsgrund.
- Bei unbekannten Begriffen, ähnlich klingenden Werkzeugnamen, unsicherem ASR-Text, mehreren passenden Intents, fehlendem Objekt oder fehlendem Ziel: **keine Aktion**, sondern genau eine konkrete Rückfrage mit den tatsächlich bekannten Alternativen und Option zur freien Korrektur.
- Nie eine vermeintliche Nutzerkorrektur still übernehmen; vor Ausführung die bestätigte Interpretation verwenden. Nicht bestätigte ASR-Transkripte sind Entwürfe.
- Niemals unbekannte Begriffe aus Gesprächen automatisch als verbindliche Synonyme lernen. Neue Varianten erst nach ausdrücklicher Bestätigung in den Katalog übernehmen; Herkunft und Datum dokumentieren.
- Keine automatischen Publikationen, Kosten, Deployments, Merges, Voice-Clones oder Weitergabe persönlicher Audios aus mehrdeutigen oder bloß transkribierten Befehlen. Je Social-Post separate explizite menschliche Freigabe.
- Private Audios verbleiben in privatem R2/privater Runtime; im Repository nur Textregeln und synthetische Testdaten.

## Bestätigte Intents (Beispiele, nicht als bereits implementiert ausgeben)
| Intent | DE eindeutig | TR eindeutig | Benötigtes Objekt |
|---|---|---|---|
| TRANSCRIBE | transkribieren; Transkript erstellen | yazıya dök; transkript oluştur | eindeutig ausgewählte private Aufnahme und ausdrückliche Einwilligung |
| STATUS | Status anzeigen; Auftragsstatus | durumu göster; görev durumu | ggf. Auftrags-ID |
| SHOW_RESULT | Ergebnis anzeigen; Ergebnis abrufen | sonucu göster; sonucu getir | Auftrags-ID |
| VIDEO_RENDER | Video rendern; Video neu rendern | videoyu işle; videoyu yeniden oluştur | eindeutige Video-/Revisions-ID; keine Veröffentlichung |
| HELP | Hilfe; Befehle anzeigen | yardım; komutları göster | keines |

Werkzeugnamen und Schreibvarianten (z. B. ähnlich klingende Videoeditoren) **nicht** automatisch gleichsetzen. Vorschläge sind nur Rückfragen, niemals Routing.

## Verarbeitung
1. Telegram: bestehender einzelner getUpdates-Router, zugelassene Chat-ID. Web: bestehende Dashboard-Authentifizierung.
2. Audio: erst sichere private Aufnahme + Einwilligung + lokales Whisper; Text nur als unbestätigter Entwurf.
3. Intent aus freigegebenem Katalog exakt zuordnen. Bei 0 oder >1 Treffern oder unklarem Ziel: Rückfrage; keine Seiteneffekte.
4. Erst nach bestätigtem Text und allen jeweiligen Sicherheits-/Freigabeprüfungen den bestehenden gemeinsamen Auftragseingang verwenden.
5. Negativtests: erfundene Synonyme, undeutliche Aussprache, gemischtes DE/TR, falsche Objekt-ID, fremde Chat-ID, widerrufene Einwilligung, Veröffentlichung ohne Einzelfreigabe.

## Ausbau
Weitere Alternativbegriffe und individuelle Formulierungen nur mit Nutzerbestätigung aufnehmen. Wortkatalog und Audio-Testkatalog getrennt halten: Audio ausschließlich synthetisch oder ausdrücklich einzeln autorisiert und niemals in CI.
