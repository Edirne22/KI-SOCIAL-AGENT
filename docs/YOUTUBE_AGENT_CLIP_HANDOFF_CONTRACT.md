# YouTube-Agent: verpflichtender Videoanalyse- und Clip-Handoff-Vertrag

Status: **Anforderung / nicht als LIVE nachgewiesen**. Gilt für die geplante Integration des YouTube-Agenten in das Nervensystem V1.

## Pflichtfähigkeiten

1. Eine Videoquelle und vorhandene Metadaten/Untertitel untersuchen; für echte visuelle Ereignisse Frames/Videoanalyse einsetzen. Niemals visuelle Treffer allein aus Untertiteln behaupten.
2. Geeignete, nachvollziehbar begründete Zeitfenster mit Start-/Endzeit, Konfidenz, Quelle und Szenenbeschreibung auswählen. Überlappungen und Duplikate erkennen.
3. **Automatische Clip-Extraktion ohne separate Schnitt-Einzelfreigabe** für eigenes, lizenziertes oder anderweitig zur Verarbeitung berechtigtes Quellmaterial. Downloads nur über zulässige Zugangswege; keine Umgehung von DRM, Zugangssperren oder Plattformschutz.
4. An den bestehenden FFmpeg-/OpenMontage-Eingang übergeben; keine zweite Schnitt-/Publisher-Orchestrierung und keine OpenChatCut-/SupoClip-Abhängigkeit.
5. Clip-Outputs mit Job-ID, Revision, SHA-256, Zeitfenstern, Quellen-URL, Lizenz-/Rechtebeleg und Tool-Evidence registrieren. Kein fremder Job, keine veraltete Revision, keine unbekannte Agentenrolle.
6. Unabhängiges Fakten-/Medien-/Rechte-QM vor jeder externen Veröffentlichung. Bei unklaren Rechten: keine Freigabe für Publikation, stattdessen belegte alternative Medien oder Platzhalter.
7. Private Telegram-Vorschau vor dem bestehenden menschlichen Veröffentlichungs-Gate. Automatisches Schneiden bedeutet **keine** automatische Veröffentlichung.

## Maschinenlesbarer Clip-Vorschlag

```json
{
  "schema": "youtube-clip-proposal-v1",
  "job_id": "<canonical-job-id>",
  "revision": 1,
  "agent_role_id": "youtube_video_analyst",
  "source": {
    "url": "<video-url>",
    "source_media_id": "<authorized-media-id>",
    "rights_status": "verified",
    "rights_evidence_ref": "<evidence-id>"
  },
  "clips": [
    {
      "clip_id": "clip-01",
      "start_ms": 260000,
      "end_ms": 278000,
      "reason": "Visuell belegter Schlüsselmoment",
      "confidence": 0.9
    }
  ],
  "destination": "ffmpeg-openmontage",
  "publish_approval": "required"
}
```

Beispielwerte sind **keine** echten erkannten Szenen. Der neue Rollenname ist reserviert, bis ein eindeutiger Registry-Eintrag mit konkreter Capability-Allowlist und Laufzeitnachweis eingerichtet ist.

## Abnahmebedingungen

- Test: visuell identifizierte Szene erzeugt korrektes Clip-Zeitfenster und einen überprüfbaren FFmpeg-Output.
- Test: nicht belegte/fehlerhafte Zeitstempel, unberechtigte Quellen und falsche Job-/Revision-/Rollenkennungen werden fail-closed abgewiesen.
- Test: Clip wird OpenMontage zugeordnet, nicht OpenChatCut/SupoClip.
- Test: keine automatische Veröffentlichung ohne explizite menschliche Freigabe.
- Externer YouTube-Agent wird vor Integration auf Code, Lizenz, Netz-/Dateizugriffe, Kosten und tatsächliche Funktionen geprüft.

Die vom Auftraggeber erteilte Freigabe zur **automatischen technischen Clipauswahl und -bearbeitung** gilt innerhalb dieser Grenzen und ersetzt weder Plattform-/Urheberrechte noch die gesonderte Veröffentlichungsfreigabe.
