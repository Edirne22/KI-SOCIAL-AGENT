# Dünya – Level 12: Maschinenabnahme vor privatem Produktionsstart

## Originalauftrag (aus Dashboard-Screenshots, kein privater R2-Prompt im Git)
Privater emotionaler Geburtstagsfilm; Material aus vorhandenem privatem R2, kein erneuter Upload. Hochformat 9:16. Ungefähr fünf Minuten als Orientierung, keine exakt erzwungenen 300 Sekunden. Bestes Material selbst auswählen; Ankunft, Trampolinpark-Action, Höhepunkte, ruhigere Momente und emotionales Finale dramaturgisch montieren. Foto-Motion, sinnvolle Videoschnitte, moderne weiche echte Übergänge, verteilte Titel, passende Musik und optional erhaltener guter Originalton. Keine Veröffentlichung. R2/Telegram/Dashboard nur privat.

## Verantwortlichkeiten / Fehlervermeidung
- Produktionsleiter: Originalbrief vollständig, Format, Privatsphäre, ungefähre statt fixe Dauer und Stop-Gate an alle Rollen weitergeben. Keine stillen Defaults.
- Creative Director: Bilder/Videos inhaltlich klassifizieren; relevante Momente erkennen; Dubletten und schwache Aufnahmen aussortieren; individuellen Schnitt mit Story-Beats, variablen Dauern und Audio-Cues vorgeben. Nicht bloß sechs fixe Zeitblöcke ausgeben.
- Media/Story: pro Asset content_verified, asset_role, story_beat, importance, sequence_position, keep/drop_reason, crop-safe region, gewünschte Motion und konkrete Übergangsentscheidung dokumentieren. Dateireihenfolge allein genügt nicht.
- Music/Audio: Musik nach Stimmung und Szenen wechseln/steuern; Originalton erhaltenswerter Videos nicht pauschal entfernen; Mischung/Ducking und Fade-Cues angeben.
- FFmpeg/Renderer: echten Motion- und Übergangsadapter mit Frame-übergreifenden Transitionen verwenden, nicht ausschließlich fade-in/fade-out zu Schwarz. Maschinenbefehle aus freigegebenem Szenenplan ableiten. Tatsächliche Ist-Evidence erzeugen.
- QM: erwartete vs. ausgeführte Befehle pro Asset, Szene, Transition, Text und Audio vergleichen; zusätzlich Story- und visuelle Stichprobe. Drei verschiedene Übergangsnamen bei gleicher Schwarzblende sind FAIL.
- Agent 21: Code-, Test-, Adapterfehler reparieren. Agent 11: ausschließlich Runtime-Wiederanlauf, kein Ersatz für kreative Prüfung.

## Gate und Abnahmeszenarien
1. Vor der Maschine muss ein maschinenlesbarer vollständiger Creative-Vertrag mit realer Inhaltsklassifikation vorliegen. Fehlt er, NOT_READY_FOR_MEDIA.
2. Negative Probe: 60 ungeprüfte Bilder, fixe 300 Sekunden, zyklische Effekte, Fade nach Schwarz, pauschale Musik: muss blockieren.
3. Positive synthetische Probe: klassifizierte Medien, wechselnde sinnvolle Dauern, echte unterschiedliche Übergänge, Audio-/Text-Cues, per-Asset Ist-Evidence: muss bestehen.
4. Renderer-Funktionstest ausschließlich mit synthetischen Testmedien; kein privater Produktionsstart als Test.
5. PR/CI, Tests, tatsächliche Machine-Contract-Diff und nachvollziehbarer Vorstartbericht vorlegen.
6. Erst danach gesonderte Freigabe zum erneuten privaten Dünya-Produktionslauf.

## Ist-Stand 2026-10-08
Die vorhandene Runtime hat keine nachgewiesene semantische Bildanalyse. Der bestehende Renderpfad nutzt Fade zu Schwarz, entfernt Video-Originalton mittels -an, setzt feste Text-Zeitpunkte und skaliert Slots auf 300 Sekunden. Diese Defizite sind nicht durch eine Stellenbeschreibung allein behoben. Der erste technische Preflight ist ein bewusst strenges Stop-Gate, keine kreative Endlösung. Produktionsstart nicht freigegeben.
