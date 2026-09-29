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
