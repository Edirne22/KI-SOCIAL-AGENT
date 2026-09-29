# MASTER-VISION – AUTONOME MEDIA-/VIDEO-CONTENT-FABRIK

**Stand:** 2026-09-29
**Status:** verbindliches Zielbild vor Tool-Battle und Implementierung

## 1. Ziel
Die Content-Fabrik soll aus einer kurzen Anweisung und Ausgangsmaterial weitgehend selbstständig ein fertiges, prüfbares Social-Media-Video herstellen. Bülent gibt Idee, Quelle oder Material vor. Die Fabrik übernimmt technische Produktion und legt das Endprojekt zur menschlichen Freigabe vor.

## 2. Betriebsleiter-/Orchestrator-Prinzip
Ein zentraler Betriebsleiter-Agent nimmt den Produktionsauftrag entgegen, erstellt einen Job, zerlegt ihn in Teilaufgaben und verteilt diese an spezialisierte Agenten. Ergebnisse werden nicht isoliert erzeugt, sondern mit Quellen, Timestamps, Claims und Assets an die jeweils nächste Produktionsstufe weitergegeben.

Beispiel:
"Nimm das neue Tolga-Video, finde die drei bis fünf interessantesten Themen und mach daraus ein ca. 60-Sekunden-Video in meinem Stil."

## 3. Produktionskette
Quelle/Rohmaterial
→ Ingest
→ Audio/Transkript
→ Themen/Highlights
→ Quellen-/Faktenprüfung
→ Schreiben im Bülent-/Edirne-22-Stil
→ Storyboard/Regie
→ Visual-/Asset-Plan
→ Voice
→ Avatar/Animation
→ Captions
→ Schnitt/Rendering
→ End-QM
→ Vorschau
→ Bülent-Freigabe
→ Publisher.

## 4. Quellen und Urheberrecht
YouTube und andere öffentliche Quellen können der Recherche, Themenfindung und Faktengewinnung dienen. Das System soll nicht als Kopiermaschine für fremde Videos gebaut werden. Das neue Werk soll auf eigener Redaktion, eigener Formulierung, eigener Stimme/Avatar, eigenen oder legitim nutzbaren Visuals und eigenem Schnitt beruhen. Fremde Screenshots/Clips werden nur eingesetzt, wenn die konkrete Nutzung rechtlich und plattformseitig vertretbar ist.

## 5. Avatar
Langfristig entsteht eine wiedererkennbare Bülent-/Edirne-22-Comic-/3D-Figur.
Mögliche wiederverwendbare Aktionen:
- stehen / gehen
- zeigen
- Daumen hoch
- reagieren
- auf eingeblendete Elemente zeigen
- weitere Regieaktionen/Posen

Die Aktionen sollen möglichst als wiederverwendbare Bibliothek verfügbar sein, damit nicht jedes Video vollständig neu generiert werden muss.

## 6. Stimme
Stufenmodell:
1. geeignete künstliche Übergangsstimme
2. Voice-Cloning von Bülents Stimme
3. Voice + Avatar + Lippenbewegung/Emotion synchronisieren

Voice-Cloning darf den restlichen Fabrikbau nicht blockieren.

## 7. Captions sind Pflichtbestandteil
Das Gesprochene wird synchron als gut lesbarer Text eingeblendet. Videos sollen auch ohne Ton verständlich sein. Später können Hook, Schlüsselwörter und wichtige Aussagen gezielt hervorgehoben werden.

## 8. Reparatur statt Voll-Neugenerierung
Feedback soll gezielt an die zuständige Produktionsstufe zurücklaufen.
Beispiel:
"Bei Sekunde 23 anderes Bild. Sonst gut."
→ nur betroffenen Abschnitt/Asset reparieren
→ erneut rendern/prüfen
→ neue Vorschau.

Keine unnötige vollständige Neugenerierung.

## 9. Persistentes Production Job Package
Ein Job soll mehr als nur final.mp4 enthalten:
- Auftrag
- Quellen + URLs/IDs
- Timestamps
- Transkript
- ausgewählte Claims/Themen
- Faktenbelege
- finales Skript
- Storyboard/Schnittplan
- Asset-Liste
- Voice-Datei
- Captions
- Render-Ausgabe
- QM-Bericht
- Freigabestatus

Damit bleibt nachvollziehbar, warum ein bestimmter Abschnitt im Endvideo enthalten ist.

## 10. Human Authority
Die bestehende Human-Approval-Logik bleibt verbindlich:
Entwurf → Bülent prüft → ändern / nicht posten / posten.

Nach ausdrücklichem "posten" darf kein nachgelagerter KI-QM-Agent die menschliche Freigabe erneut kassieren. Vor der Freigabe dürfen Fakten-/Qualitätsprüfungen blockieren; nach der finalen Freigabe übernimmt die Publisher-Schicht die genehmigte Version.

## 11. Plattformen
YouTube ist sowohl mögliche Recherchequelle als auch zukünftiger eigener Ausgabekanal.

Zielplattformen:
- Instagram Reels
- Facebook Reels
- TikTok
- YouTube Shorts / später ggf. längere eigene Videos
- X je nach Content

Das veröffentlichte Material soll ein eigenes redaktionelles Werk der Content-Fabrik sein.

## 12. Produktionswerkzeug vs Publisher
Diese Rollen werden getrennt bewertet.

### Produktionshalle
Aktuelle Kandidaten:
- OpenCut-AI
- OpenChatCut
- FFmpeg/Remotion
- weitere Kandidaten aus IDEA_POOL

OpenCut-AI ist besonders interessant, weil mehrere benötigte Produktionsschritte in einem System gebündelt werden können. Das ist noch keine endgültige Architekturentscheidung.

### Versand-/Publisher-Schicht
Aktuelle Kandidaten:
- bestehender KI-SOCIAL-AGENT-Publisher
- Postiz
- Mixpost
- ggf. Hybrid

Postiz ist besonders interessant für Multi-Plattform-Publishing/API/Automation. Ein neues Tool ersetzt die bereits funktionierende Human-Approval-/Publisher-Kette nur dann, wenn der Tool-Battle einen klaren technischen Vorteil zeigt.

## 13. Tool-Battle
Vor Implementierung werden die Kandidaten anhand derselben Anforderungen verglichen:
- Self-hosting / 0-Euro-Ziel
- Windows/x86/VPS-Tauglichkeit
- API/CLI/MCP/Automatisierbarkeit
- Video-Editing
- Transkription
- Captions
- Voice/TTS/Voice-Cloning
- B-Roll/Assets
- Avatar-Integration
- Rendering
- reproduzierbare Jobs
- Fehler-/Retry-Verhalten
- Lizenz
- Wartbarkeit
- Ressourcenbedarf
- Integration in bestehende Python-Agenten
- Plattform-Publishing
- Human-Approval-Kompatibilität

Nicht das Tool mit den meisten Features gewinnt, sondern die kleinste belastbare Kombination, die unsere Anforderungen zuverlässig erfüllt.

## 14. Bauprinzip
Das Projekt wird schrittweise gebaut, nicht als ein riesiger Big-Bang-Commit.

Empfohlene Reihenfolge:
1. Tool-Battle und Architecture Decision Record
2. Production-Job-Schema + Ordner-/Statusmodell
3. Betriebsleiter-Orchestrator als MVP
4. Ingest + Transkription
5. Highlights + Fakten + Writing
6. Storyboard + Captions
7. Rendering-MVP ohne Avatar
8. Repo/Telegram-Vorschau + bestehende Human Approval
9. Publisher-Anbindung
10. Voice-Ausbau
11. Avatar/Animation
12. Multi-Plattform-Formate
13. Hardening, Regression, Red-Team und Live-E2E

Jede Stufe muss einzeln testbar und austauschbar bleiben.

## 15. Leitbild
Bülent liefert Material und Idee. Die Agentenfabrik übernimmt Recherche, Transkription, Redaktion, Faktenprüfung, Regie, Visuals, Stimme, Avatar, Untertitel, Rendering und Qualitätsprüfung. Bülent erhält das fertige Ergebnis auf dem goldenen Tablett und entscheidet, ob veröffentlicht wird.


## 16. Architekturfortschreibung 29.09.2026 – Fabrik über austauschbaren Maschinen

Die Master-Vision wird durch den laufenden Tool-Battle konkretisiert:

**Edirne 22 baut nicht jede technische Maschine selbst nach.** Der Betriebsleiter bleibt die übergeordnete Fabriksteuerung und delegiert klar abgegrenzte Aufgaben über Adapter an die jeweils beste verfügbare Maschine. Externe Werkzeuge dürfen weder ProductionJob noch Fakten-QM, Human Authority oder den finalen Approval State übernehmen.

Aktuell vorgesehene Maschinenrollen:
- SupoClip als primärer MVP-Kandidat für automatische Longform→Short-/Reel-Produktion, Segmentwahl, 9:16-Face-Crop, Hooks und Captions.
- OpenChatCut für editierbares Masterprojekt und gezielte Targeted Repairs.
- FFmpeg als stabile Low-Level-Media-/Render-Schicht und Fallback.
- Cloudflare R2 als bevorzugtes persistentes Medienlager hinter MediaStorageAdapter.
- weitere Werkzeuge nur hinter austauschbaren Adaptern.

Leitprinzip:
**Wir setzen unsere Fabrik über die besten verfügbaren Maschinen, statt jede Maschine unnötig selbst nachzubauen.**

## 17. YouTube und Social Media als Tool-/Ideen-Radar

YouTube, Instagram und ähnliche öffentliche Quellen dienen nicht nur als mögliche Themenquellen für spätere Posts. Sie werden zusätzlich als **Discovery-Radar für neue Werkzeuge, Modelle, Open-Source-Projekte und Produktionsmethoden** genutzt.

Ablauf bei einem Fund:
1. Bülent liefert Link, Screenshot oder Namen.
2. Die Fabrik/Entwicklungsprüfung extrahiert die interessante Behauptung oder das genannte Werkzeug.
3. Werbeversprechen werden nicht ungeprüft übernommen.
4. Originalquelle, offizielle Dokumentation und/oder Repository werden gegengeprüft.
5. Der Kandidat wird gegen die Edirne-22-Anforderungen bewertet.
6. Ergebnis: MVP / WATCH-LATER / verwerfen.
7. Geeignete Kandidaten werden einer klaren Maschinenrolle und einem Adapter zugeordnet.

Damit kann die Architektur von neuen Open-Source-Entwicklungen profitieren, ohne jedem Trend hinterherzulaufen oder den stabilen MVP ständig umzubauen.

## 18. GenerativeVideoAdapter – fehlende Szenen selbst erzeugen

Neben der Verarbeitung vorhandenen Quellmaterials benötigt die spätere Fabrik eine eigene Schnittstelle für **generativ erzeugte Video-/Visual-Szenen**.

Beispiel:
Storyboard verlangt eine Szene oder visuelle Erklärung, für die kein eigenes oder legitim nutzbares Asset vorhanden ist.
→ Betriebsleiter erzeugt einen Generative-Scene-Auftrag
→ GenerativeVideoAdapter erhält Prompt, gewünschtes Format, Dauer und optionale Referenz-Assets
→ Provider/Modell erzeugt das Asset
→ Ergebnis wird mit Herkunft/Provider/Prompt/Version im MediaStorage registriert
→ Video-/Reel-Maschine übernimmt das Asset
→ End-QM prüft die fertige Fassung.

Der ProductionJob kennt die Funktion, aber **nicht fest den Anbieter**. Dadurch können Modelle später ausgetauscht oder gegeneinander geroutet werden.

Aktuelle WATCH/LATER-Kandidaten:
- Luma Agents / Luma AI
- Seedance 2.5
- weitere zukünftige lokale oder gehostete Generative-Video-Modelle

Seedance 2.5 wurde über einen YouTube-Radar-Fund entdeckt. Insbesondere Text-/Bild-/Referenz-zu-Video macht es als späteren Kandidaten für generative Inserts, Szenen und Character-/Avatar-nahe Aufgaben interessant. Aussagen wie „free/unlimited“ werden ausdrücklich **nicht** als Architekturannahme übernommen; Preise, Limits, API, Rechte und Verfügbarkeit müssen zum Zeitpunkt eines PoC erneut verifiziert werden.

Luma und Seedance werden nicht vor SupoClip in den MVP gezogen. Sie gehören in eine spätere Generative-Video-/Avatar-Ausbaustufe.

## 19. Tool-Radar bleibt dauerhaft offen

Neue Werkzeuge dürfen während des gesamten Projekts eingebracht werden. Jeder Kandidat wird mindestens auf folgende Punkte geprüft:
- konkrete Maschinenrolle
- ersparte Eigenentwicklung
- Open Source / Self-hosting / API / MCP
- Lizenz und Nutzungsrechte
- Kosten
- Infrastrukturbedarf
- Reifegrad und Wartbarkeit
- Fehler-/Recovery-Verhalten
- Adapterfähigkeit
- Datenschutz/Prompt-Datenfluss
- Auswirkungen auf Fakten-QM und Human Authority.

Ein neuer Kandidat ersetzt einen funktionierenden Baustein nur nach nachvollziehbarem technischen Vorteil und einem isolierten PoC. Die Fabrik soll dadurch **lernfähig und austauschbar** bleiben, ohne ihre eigene Architekturhoheit zu verlieren.


## 20. Pollo MCP/CLI – GenerativeMedia-Maschine

Pollo wird als geplanter Kandidat für die generative Medienmaschine in die Fabrik aufgenommen.

Rollenverteilung:

- **SupoClip**: vorhandenes Longform-/Quellmaterial analysieren und daraus Shorts/Reels erzeugen.
- **Pollo MCP/CLI**: neue generative Medienbausteine erzeugen, insbesondere fehlende Szenen, B-Roll, Bilder und Video; Voice-/Audio-Funktionen werden separat auf Qualität, Rechte und Kosten geprüft.
- **OpenChatCut**: editierbares Masterprojekt und gezielte Reparaturen.
- **FFmpeg**: stabiler Low-Level-Render-/Transcode-/Fallback.

Pollo wird hinter dem generischen `GenerativeMediaAdapter` angebunden. Der ProductionJob kennt nicht Pollo als feste Abhängigkeit, sondern nur den benötigten Medienauftrag.

Geplanter Handoff:

```text
Bülents Befehl
→ Job API
→ Betriebsleiter
→ Storyboard / Asset Request
→ GenerativeMediaAdapter
→ Pollo MCP/CLI
→ erzeugtes Asset
→ MediaStorageAdapter / R2
→ SHA-256 + Provenienz + Revision
→ SupoClip oder OpenChatCut / nächste Maschine
→ End-QM
→ Preview
→ Bülent
```

Pollo darf niemals System of Record für ProductionJob, Fakten-QM, Human Authority oder finalen Approval-State werden.

Vor produktiver Bindung ist ein isolierter PoC Pflicht. Zu prüfen sind mindestens: Auth/API/MCP/CLI, Modellwahl, Kosten vor Jobstart soweit verfügbar, Jobstatus/Timeout/Retry, lokale Datei vs. URL/R2-Handoff, Ergebnisdownload, Hash/Provenienz, DE/TR-Ausgaben, Nutzungs-/Output-Rechte, Fehler-/Resume-Verhalten und Austauschbarkeit gegen einen anderen Provider.

Die Aufnahme von Pollo ändert nicht die MVP-Priorität von SupoClip. Beide Maschinen ergänzen sich.


## 21. Block 7 – VoiceAdapter / Bülent-Stimme / DE-TR

Die Voice-Stufe wird als austauschbare Maschinenrolle hinter einem `VoiceAdapter` gebaut. Kein einzelner TTS-/Voice-Cloning-Anbieter wird fest in den ProductionJob verdrahtet.

Geplanter Handoff:

```text
ProductionJob + finales Skript
→ VoiceAdapter
→ ausgewählte Voice-Maschine
→ Audio-Asset
→ MediaStorageAdapter / R2
→ SHA-256 + Provenienz + Revision
→ Captions / Schnitt / End-QM
→ Preview
→ Bülent
```

Aktuelle Kandidaten aus dem Tool-Radar:

- **Chatterbox Multilingual – PoC-Priorität:** erster lokaler Kandidat für Bülents spätere DE/TR-Stimme; insbesondere Natürlichkeit, Emotion, deutsche/türkische Aussprache und Voice-Cloning prüfen.
- **GPT-SoVITS – Vergleichskandidat:** lokaler Few-Shot-/Voice-Cloning-Kandidat mit hoher Kontrolle; gegen Chatterbox mit denselben Referenzaufnahmen und Testtexten messen.
- **OpenVoice V2 – Vergleich/Fallback:** Voice-Cloning und Style-Control interessant; DE/TR-Unterstützung vor Einsatz praktisch verifizieren und nicht aus Social-Media-Werbeaussagen ableiten.
- **F5-TTS – WATCH/Lizenzprüfung:** technisch interessanter lokaler Kandidat; Modell-/Gewichts-Lizenz und kommerzielle Nutzbarkeit müssen vor produktiver Verwendung separat geprüft werden.
- **Bark – WATCH/LATER:** für expressive generative Sprache interessant, aber nicht als primärer Bülent-Voice-Cloning-Kandidat einplanen.
- **PlayHT – Cloud-Benchmark:** nur als gehosteter Qualitäts-/Kostenvergleich; keine feste Architekturabhängigkeit.
- **Kokoro – bestehender Übergangskandidat:** bleibt für eine künstliche Übergangsstimme im Vergleich, solange Bülent-Voice-Cloning noch nicht produktionsreif ist.

Der PoC darf nicht nach einer Social-Media-Rangliste entschieden werden. Alle ernsthaften Kandidaten erhalten denselben Testkorpus:
- identische autorisierte Referenzaufnahmen von Bülent,
- identische deutsche und türkische Texte,
- Racing-Namen und Diakritika wie Toprak Razgatlıoğlu, Can Öncü und Kenan Sofuoğlu,
- neutrale, begeisterte und erklärende Sprechweise,
- Messung von Natürlichkeit, Aussprache, Stimmähnlichkeit, Emotionskontrolle, Latenz, CPU/GPU/RAM, Stabilität und Kosten,
- Prüfung von Code-, Modell-, Trainingsdaten-/Output-Lizenz und kommerzieller Nutzbarkeit.

Nur Bülents ausdrücklich autorisierte eigene Stimme darf als persönlicher Voice-Clone für die Fabrik verwendet werden. Die erzeugte Audiodatei wird wie jedes andere Produktionsasset mit Provider/Modell, Version, Hash und Provenienz im MediaStorage registriert.

Block 7 ist nachgelagert und darf Block 1 nicht aufhalten. Die VoiceAdapter-Grenze wird so ausgelegt, dass Kandidaten später ohne Änderung an Human Authority, Fakten-QM, ProductionJob oder Publisher ausgetauscht werden können.


### 21.1 AvatarAdapter und MotionAdapter

Block 7 umfasst neben Voice auch eine optionale visuelle Sprecherstufe. Voice und Avatar bleiben getrennte Maschinen.

Produktionsmodi:
- `VOICE_ONLY`: Stimme über Racing-, Motorrad- und B-Roll-Visuals.
- `REALISTIC_BULENT`: von Bülent freigegebener persönlicher Avatar für Moderation, News und Erklärstücke.
- `BRAND_AVATAR`: Edirne-22-/Comic-/3D-Figur für stärker inszenierte Inhalte.

Ablauf: finales Skript → VoiceAdapter → Audio → optional AvatarAdapter → MotionAdapter/Gesten → Lip-Sync → MediaStorage/R2 → Captions → Rendering → End-QM → Preview → Bülent.

HeyGen wird als Cloud-PoC-/Benchmark-Kandidat für `REALISTIC_BULENT` aufgenommen und nicht fest in die Architektur eingebaut. Lokale Alternativen wie MuseTalk werden später über dieselbe Adaptergrenze verglichen.

Der MotionAdapter soll wiederverwendbare Bewegungsprofile unterstützen: neutral erklären, begeistert reagieren, zeigen, Daumen hoch und auf eingeblendete Elemente zeigen.

Vor produktiver Nutzung werden Rechte, Datenschutz, Referenzmaterial-Speicherung, Output-Rechte, API/Automation, Kosten, Wasserzeichen, DE/TR-Lip-Sync, Gestenqualität, Retry/Resume und Austauschbarkeit geprüft. Wasserzeichenentfernung ist keine Produktionsstrategie.

Targeted Repair gilt auch hier: Änderungen an Stimme, Geste oder Avatarsequenz sollen nur den betroffenen Abschnitt neu erzeugen.
