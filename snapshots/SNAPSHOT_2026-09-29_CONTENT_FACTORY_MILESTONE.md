# PROJECT SNAPSHOT — 2026-09-29 — CONTENT FACTORY MILESTONE

## Zweck
Dieser Snapshot ist der verbindliche Übergabepunkt für einen neuen Chat oder eine spätere Wiederaufnahme des Projekts. Er dokumentiert den produktiven Stand nach Stabilisierung der Turkish-Rider-Human-Approval-/Publisher-Kette und den nächsten großen Ausbau: die autonome Media-/Video-Content-Fabrik.

## Wiederherstellung / Backup
- Repository: Edirne22/KI-SOCIAL-AGENT
- Gesicherter produktiver Commit vor diesem Snapshot: `301c7c3b41175026daf24dbd6cfe59e2b3a214a3`
- Vollständiger Sicherungs-Branch: `backup/2026-09-29-content-factory-milestone`
- Der Backup-Branch darf nicht für normale Entwicklung verwendet oder vorwärtsgeschoben werden. Er ist ein Wiederherstellungspunkt.

## Aktueller produktiver Meilenstein

### Turkish Rider / Human Authority
Die manuelle T-Auswahl ist als Human-Authority-Kette umgesetzt:
1. Bülent wählt T-Items.
2. Ein Editor-Durchlauf erzeugt die Vorschau.
3. Telegram zeigt die Vorschau.
4. Bülent entscheidet: posten / überarbeiten / nicht posten.
5. Nach `posten` darf kein nachgelagertes QM die menschliche Freigabe erneut blockieren.
6. Der exakt freigegebene Text wird in die Publishing-Kette gegeben.
7. Keine automatische Veröffentlichung ohne explizite Freigabe.

### Reihenfolge / Publisher
- Kommandos wie `T1,T3,T5 posten` werden erkannt.
- Die Freigabe-Reihenfolge wird bewahrt.
- Pro Publisher-Rundlauf wird genau ein geeigneter Block beansprucht.
- Instagram- und Facebook-Cadence bleiben getrennt und unverändert.
- Instagram benötigt für Human-Final-T-Posts keine zweite Bildfreigabe mehr.
- Persistente Medien liegen unter `assets/...`, nicht in flüchtigen `memory/...`-Pfaden.

### Live-Beweis 29.09.2026
Die Legacy-Migration für T1/T3/T5 wurde live ausgeführt:
- alte Instagram-Blöcke `BILD_GENERIERT` wurden ohne Duplikate auf `FREIGEGEBEN` migriert;
- persistente Asset-Pfade wurden eingetragen;
- der erste Instagram-Post wurde anschließend vom echten Publisher erfolgreich veröffentlicht.
Damit ist der Pfad Telegram-Freigabe → persistentes Asset → Queue/Claim → Instagram-Publisher → echter Post praktisch bestätigt.

### Wichtige PR-Meilensteine
- #219 Human Preview / kein QM-Veto nach manueller Auswahl
- #220 natürliche Turkish-Preview-Aktionen / exact saved preview
- #221 Reihenfolge + Publisher-Cadence
- #222 Router erkennt `T1,T3,T5 posten`
- #223 Human-Final direkt Instagram-publishable + persistenter Asset-Pfad
- #224 Legacy-Migration alter Turkish-Human-Instagram-Blöcke
- #225 Ideenpool konsolidiert: `docs/IDEA_POOL.md` ist wieder der einzige große gewachsene Ideenpool

## Bekannte kleine Nacharbeiten
Diese Punkte sind kein Blocker für den nächsten großen Ausbau:
- Telegram-Bestätigung kann nach Migration irreführend `0 Plattform-Blöcke vorbereitet` melden, obwohl bestehende Blöcke erfolgreich migriert/freigegeben wurden. Später kosmetisch auf Migrations-/Freigabezähler umstellen.
- Bei ungewöhnlichem altem Instagram-Verhalten `memory/PENDING_INSTAGRAM.json` auf stale Legacy-Einträge T1/T3/T5 prüfen und nur gezielt bereinigen.
- Nachfolgende T3/T5-Publisher-Rundläufe weiter als Live-E2E-Beobachtung nutzen.

# NÄCHSTER GROSSER BLOCK — MEDIA-/VIDEO-CONTENT-FABRIK

## Zielbild
Bülent liefert Rohmaterial (Fotos, Videos, ggf. Audio) und einen kurzen Auftrag. Die Fabrik erzeugt daraus möglichst selbstständig einen fertigen Social-Media-Entwurf.

Beispiel:
`Nimm diese Fotos und Clips und erstelle ein 35-Sekunden-Reel über die Tour, locker in meinem Stil.`

Gewünschte Kette:
Rohmaterial → Ingest/Analyse → Transkription → Story/Script → Schnittplanung → Voice/Audio → optional Avatar → B-Roll/Untertitel/Branding → Rendering → Fakten-/Qualitätsprüfung → Telegram/Repo-Vorschau → Bülent-Freigabe → bestehender Publisher → Instagram/Facebook/TikTok.

## Grundprinzip
Nicht ein einzelnes Modell soll alles erledigen. Ein Orchestrator verteilt Teilaufgaben an die jeweils geeigneten Werkzeuge/Modelle. Komponenten müssen austauschbar bleiben.

## Tool-Battle vor Implementierung
Bevor wir uns festlegen, werden die Kandidaten technisch gegeneinander geprüft und das Beste je Aufgabe gewählt.

### Video / Editing / Rendering
Zu prüfen:
- OpenCut-AI
- OpenChatCut
- bestehendes FFmpeg
- Remotion

Bewertung:
- automatisierbar/API/CLI/MCP
- Windows lokal und später VPS-tauglich
- Timeline/Schnitt
- Captions
- B-Roll
- Script-to-Video
- Rendering-Stabilität
- Ressourcenbedarf
- Lizenz/Kosten
- Integration in GitHub-/Telegram-Workflow

### Audio / Transkription / Voice
Zu prüfen bzw. kombinieren:
- Whisper / OpenWhispr für Transkription
- Pipecat für Audio-/Agenten-Pipeline, falls sinnvoll
- geeignete TTS-/Voice-Cloning-Komponente, z. B. XTTS oder bessere aktuelle Alternative

Ziel:
- Originalaudio verstehen
- relevante Stellen/Zitate erkennen
- Voice-over generieren
- später optional Bülents Stimme als freigegebenes Voice-Profil verwenden

### Avatar / Edirne-22-Figur
Spätere Ausbaustufe:
- wiedererkennbare Comic-/3D-/Avatar-Figur von Bülent
- spricht generiertes Script mit freigegebener synthetischer Stimme
- kann mit Motorrad-/Racing-B-Roll kombiniert werden
- Originalvideos bleiben ebenfalls nutzbar; Avatar ist optional, nicht Zwang

### Discovery / Quellen
Späterer Ausbau aus Ideenpool:
- offizielle APIs/RSS zuerst
- Telegram-Racing-Quellen evaluieren
- X/Twitter nur optionale Discovery-Schicht
- strukturierte Live-/Timing-Daten prüfen
- Racer Registry ausbauen
- keine experimentelle Social-Quelle als Single Point of Failure

## MVP — zuerst bauen
Noch nicht mit Avatar/Voice-Cloning beginnen. Zuerst einen robusten End-to-End-MVP:

1. Rohmaterial in definierten Repo-/Upload-Eingang legen.
2. Auftrag per Telegram oder definierter Job-Datei.
3. Video-/Audio-Material automatisch inventarisieren.
4. Audio transkribieren.
5. Inhalt/Highlights erkennen.
6. Script + Schnittplan erzeugen.
7. Mit FFmpeg/Remotion bzw. Gewinner des Tool-Battles ein Reel rendern.
8. MP4 + Caption + verwendete Quellen/Assets persistent im Repo/Artifact ablegen.
9. Vorschau an Bülent.
10. Erst nach explizitem `posten` an bestehenden Publisher übergeben.

## Danach
Ausbaustufen nach stabilem MVP:
1. Voice-over
2. Voice-Cloning mit Bülents ausdrücklicher Freigabe/Voice-Profil
3. Avatar/Comic-Figur
4. automatische B-Roll-Auswahl
5. mehrere Formatvarianten 9:16 / 1:1 / ggf. 16:9
6. TikTok-Integration
7. VPS-Dauerbetrieb
8. Webhooks statt Polling, wo sinnvoll
9. Memory/Analytics: Welche Hooks, Längen, Formate und Themen funktionieren?

## Infrastruktur
Aktuell/Präferenz:
- Windows-11-Laptop für lokale Entwicklung
- OmniRoute + Provider-Fallbacks
- FFmpeg vorhanden
- später x86-VPS bevorzugt; Contabo als positiver Kandidat
- rechenintensive Transkription/Video-Aufgaben müssen nicht permanent laufen; bedarfsgesteuert ist akzeptabel

## Architekturregel für die Zukunft
Die bereits funktionierende Human-Approval-/Publisher-Schiene wird NICHT neu erfunden. Die Media-Fabrik produziert einen freigabefähigen Content-Entwurf und hängt ihn anschließend an dieselbe bewährte Logik:
`Entwurf → Bülent prüft → posten → Queue → Publisher`.

## Projektregeln bleiben bindend
- Keine Tests umgehen oder künstliche PASS erzeugen.
- Keine Sicherheits-/QM-Prüfung still deaktivieren.
- Automatisch erzeugter Content wird nicht ohne Bülents Freigabe veröffentlicht.
- Für Faktencontent Quellen-/Fact-Contract erhalten.
- Bei Änderungen: Regression/CI/Red-Team gemäß PROJECT_GUARDRAILS.
- Merge erst nach ausdrücklicher Freigabe von Bülent.

## Einstieg im nächsten Chat
Wenn dieser Snapshot zur Übergabe dient, zuerst:
1. aktuellen `main` gegen diesen Snapshot prüfen;
2. `docs/IDEA_POOL.md` lesen;
3. vorhandene Media-/Video-/Audio-Dateien und Abhängigkeiten im Repo inventarisieren;
4. Tool-Battle OpenCut-AI vs OpenChatCut vs FFmpeg/Remotion sowie Audio/Voice-Kandidaten mit aktuellen technischen Fakten durchführen;
5. daraus eine konkrete MVP-Architektur und den ersten kleinen PR ableiten.

**Leitsatz:** Bülent liefert Material und Idee. Die Agentenfabrik übernimmt die technische Produktion. Bülent bekommt den fertigen Entwurf auf dem goldenen Tablett und entscheidet, ob veröffentlicht wird.
