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


## Voice-first acceptance requirements (owner expects ~90–95% Telegram audio)
- Telegram voice notes (`voice`) and supported audio documents must be detected by the existing **single** Telegram router, never by a second getUpdates consumer.
- **Do not download personal Telegram audio in GitHub Actions.** Existing scheduled router currently runs on GitHub Actions every 5 minutes, 06:00–21:59 UTC; audio needs a separately authenticated, private Telegram intake/relay and private R2 upload. Until that private route is verified, respond with an honest unsupported status rather than silently discarding audio. Do not claim 24/7 responsiveness from this schedule.
- In private runtime: validate authorized chat, Telegram file size/MIME, file origin, private R2 canonical metadata, fresh consent, SHA256, language DE/TR; decode with ffmpeg and local faster-whisper. Avoid external browser speech providers by default.
- A long voice note can contain multiple independent requests. Produce a numbered **draft** of the recognized transcript and proposed tasks. Do not split uncertain conjunctions into unintended actions. Request correction on uncertain words/targets and confirmation before any consequential action.
- Allow simple corrections in DE/TR (e.g. 'Nein, ich meinte …' / 'Hayır, … demek istedim'), referencing one pending draft ticket. Do not auto-learn corrections as global synonyms.
- Return status and final results to the same authorized Telegram chat and the shared dashboard using one deduplicated R2 ticket. No raw personal voice, transcript text, Telegram token or chat ID in CI logs, public previews or repository.
- Spoken 'poste' is a request to **prepare a private preview**, not a publication authorization. The exact reviewed item needs its own explicit publication confirmation, tied to immutable item/revision identity. Ambiguous 'poste dies und das' must trigger clarification.
- Run tests: Telegram voice, audio document, DE/TR/mixed language, background noise, long message, duplicate update, unauthorized chat, consent missing/revoked, malformed file, ambiguous tool name, transcript correction, multi-intent, item-specific publication approval and non-publish negatives. CI only synthetic audio; real owner's audio tested only in private runtime after existing consent.
- Report actual word recognition quality based on measured DE/TR samples; no unsupported claim of 100% recognition. Never turn ASR confidence alone into authorization.
