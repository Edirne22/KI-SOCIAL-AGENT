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
