# OpenMontage über Telegram benutzen

## Was ist eingebunden?

OpenMontage liegt zur Laufzeit unter `integrations/openmontage/upstream`.
Die Quelle und feste Revision stehen in `integrations/openmontage/upstream.json`.
Der Workflow checkt diese Version aus und führt den Quick Start (`make setup`)
in einer lokalen Python-Umgebung aus. Keine zusätzliche Cloudflare-Runtime,
kein zweiter Telegram-Poller, kein VPS und keine globalen Paketinstallationen.

Die Anbindung bietet Installation/Diagnose, einen ausdrücklich gestarteten
synthetischen Demo-Render und Status/Downloadlinks. **Ein freier Telegram-Auftrag
wie „Erstelle meinen Geburtstagsfilm“ ist noch kein automatischer Produktionslauf.**
OpenMontage benötigt dafür einen Coding-Agenten, der seine Pipeline-Anleitungen,
Planung, Medienrechte, Freigaben und Qualitätsprüfungen ausführt. Diese Integration
ersetzt den Agenten nicht durch ein erfundenes `openmontage --prompt`-Kommando.

## Welche Befehle sende ich meinem bestehenden Bot?

| Befehl | Ergebnis |
|---|---|
| `/montage` | Hilfe und Link zu dieser FAQ |
| `/montage diagnose` | GitHub richtet OpenMontage ein und prüft Paketversionen sowie vorhandene Secret-Namen. Kein Film, keine Provider-Aufrufe. |
| `/montage test` | Beschreibt die Demo, startet nichts. |
| `/montage test starten` | Deine ausdrückliche Freigabe für die mitgelieferte Demo `code-to-screen`. |
| `/montage status` | Die letzten fünf tatsächlichen GitHub-Läufe mit Status und Link. |

Nur der bereits freigegebene `TELEGRAM_CHAT_ID` wird akzeptiert. Der vorhandene
GitHub-Poller verarbeitet die Befehle; GitHub-Zeitpläne können verspätet laufen.
Es wird keine sofortige oder durchgehende 24/7-Verfügbarkeit versprochen.

## Was zeigt der Testfilm?

Die unveränderte OpenMontage-Demo `code-to-screen` zeigt animierte Texte und
Diagramme aus der Projektvorlage. Keine privaten Bilder, keine Stimme, keine
Musik, keine Stockdownloads und keine kostenpflichtige Generierung. Es ist
**nicht** der vorgeschlagene 15-Sekunden-NASA-Film. Dieser bleibt ein separater,
noch freizugebender Produktionsauftrag mit Archivmaterial und Piper-Stimme.
Piper wird installiert; ein Sprachmodell wird noch nicht heruntergeladen.

## Wo finde ich das Ergebnis?

Der Workflow meldet seinen Abschluss im bestehenden Telegram-Chat. Öffne den
mitgesendeten Actions-Link und lade unten unter **Artifacts** die Datei
`openmontage-<Laufnummer>` herunter. Sie enthält die Diagnose oder das Demo-MP4.
Die Aufbewahrung beträgt sieben Tage. Es werden keine privaten Medien als
Actions-Artefakte angenommen. Ein Actions-Erfolg beim Modus `diagnose` beweist
keinen Video-Render und keine funktionierende Provider-Verbindung.

## Welche GitHub Secrets werden erkannt?

Die Zuordnung steht im Diagnose-Schritt von `.github/workflows/openmontage.yml`:

- Bilder/Video: `FAL_KEY`, `ATLASCLOUD_API_KEY`, `KLING_API_KEY`, `OPENAI_API_KEY`,
  `XAI_API_KEY`, `ARK_API_KEY`, `HEYGEN_API_KEY`, `RUNWAY_API_KEY`.
- Stock: `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY`.
- Stimme/Musik: `ELEVENLABS_API_KEY`, `SUNO_API_KEY` und Google.
- Google: `GOOGLE_API_KEY`; falls nicht hinterlegt, dein vorhandener
  `GEMINI_API_KEY` unter diesem Umgebungsvariablennamen.

„Vorhanden“ bedeutet nur: GitHub hat einen nicht leeren Wert übergeben.
Gültigkeit, Berechtigungen, Region und Guthaben sind dadurch **nicht getestet**.
Andere Keys (z. B. NVIDIA, Groq oder Agnes) werden nicht blind als kompatible
OpenMontage-Provider behandelt. Bestehende Workflow-Zuordnungen bleiben erhalten.

Keys werden weder aus GitHub exportiert noch in `.env`, Git, Logs oder Artefakte
kopiert. Nur der eigene Diagnose-Code sieht die zugeordneten Werte und gibt
Boolesche Werte aus. Installation und Demo erhalten keine API-Keys. Eine spätere
konkrete Provider-Produktion muss ihre passenden Secrets separat und eng
begrenzt bekommen; diese Anbindung ruft noch keine generativen APIs auf.

## Was tun bei Fehlern oder doppelten Befehlen?

`/montage status` zeigt GitHubs wirklichen Zustand. HTTP 403 beim Start bedeutet
fehlende Actions-Berechtigung, HTTP 404 kann einen noch nicht auf `main`
verfügbaren Workflow bedeuten. Die Integration braucht zunächst einen Merge.

Jede Telegram-Update-ID wird lokal im bestehenden Poller-State erfasst. Auf dem
Runner reserviert zusätzlich ein atomarer Git-Tag `openmontage-requests/tg-<ID>`
den Auftrag dauerhaft. Das schützt auch bei verlorener Antwort oder Runner-
Neustart vor doppeltem Rendering. Der Token braucht dafür `contents: write`;
der Workflow schreibt weder auf `main` noch in Publisher-Dateien.

Ein erneutes Ausführen desselben Actions-Laufs ist absichtlich gesperrt. Nach
Prüfung eines fehlgeschlagenen Laufs bewusst einen **neuen** Telegram-Befehl
senden. Bei einer unklaren Dispatch-Antwort zuerst den Status prüfen: ein neuer
Befehl erzeugt eine neue ID und kann somit einen zweiten Auftrag starten.
Reservierungs-Tags enthalten keine Texte, Chat-IDs oder Keys.

## Kostet das etwas? Wird etwas veröffentlicht?

Kein neuer Dienst und kein API-Kauf. Die Demo verwendet keine bezahlten APIs.
GitHub-Actions-Nutzung richtet sich weiterhin nach den Bedingungen und
Kontingenten des vorhandenen Repositories. Laufzeit ist auf 30 Minuten begrenzt.
Es gibt keinen automatischen Social-Publisher-Aufruf.

OpenMontage wird unverändert aus seiner AGPL-3.0-Quelle geladen; Lizenz und
Quellverweis bleiben dort erhalten. Remotion hat eine eigene Lizenz mit einer
kostenlosen Nutzungskategorie für Einzelpersonen und Evaluierung; es wird nicht
als uneingeschränkt MIT-lizenziert ausgegeben. Quellen:
https://github.com/calesthio/OpenMontage/blob/c8066452325cb57c8fc1ba8c2a71b6e8842e6b65/LICENSE
und https://github.com/remotion-dev/remotion/blob/main/LICENSE.md.

## Abnahme und aktueller Umfang

| Kriterium | Nachweis |
|---|---|
| Exakter Upstream-Pin, nur manuell, nur main | Workflow-Vertragstest |
| Telegram-Berechtigung, alter Poller/Offset unverändert | Router-Regressionslauf |
| Hilfetext/Fehleingabe startet nichts | Negativ- und Positivkontrollen |
| Timeout, 403, Duplicate, Crash/Retry | Steuerungs- und Reservierungstests |
| Keine Secret-Werte, getrennte Schritte, keine Shell-Eingabe | Red-Team-Vertragstests |
| Setup auf GitHub und tatsächliche Secret-Präsenz | Erst nach Merge: `/montage diagnose` |
| Echter Video-Render/Download | Erst nach ausdrücklichem `/montage test starten` |
| Privater Upload, freie Promptproduktion, TTS/Archivfilm, Publishing | Nicht Teil dieser Diagnose-/Demo-Anbindung; kein LIVE-Nachweis |

Automatisierte Tests simulieren GitHub/Telegram-Antworten. Sie werden nicht als
Live-End-to-End-Test ausgegeben. Der Testworkflow startet keinen Film und
verwendet keine Repository-Secrets.
