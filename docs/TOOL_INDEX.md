# TOOL_INDEX – EINE verbindliche Werkzeug- und Alternativenliste

**Stand: 01.10.2026.** Dies ist der **einzige zentrale Einstieg** für Auswahl, Fallback und Wiederaufnahme unserer KI-Fabrik. Sortiert wird nach **Nutzerfunktion**, nicht nach Instagram-Beiträgen oder Lieblingswerkzeugen. Ältere Listen sind Quellen und Archiv, keine konkurrierende aktuelle Prioritätenliste.

**Aktive Zulassungsregel:** Nur nachgewiesen kostenfrei betreibbare, für den Einsatzzweck zulässige Open-Source-Alternativen aus Abschnitt 0. Ältere/kommerzielle Marken im historischen Register sind ausdrücklich **keine** Einsatzempfehlungen.

**Zuerst lesen:** `PROJECT_GUARDRAILS.md` §§12–14, `MASTER-SNAPSHOT.md`, danach **diese Datei** vor jeder neuen Toolentscheidung und bei technischem Ausfall.

**Statusschlüssel:** `LIVE_E2E` = konkreter realer Test für exakt genannten Weg; `LOCAL_TESTED` = begrenzt technisch getestet, keine Freigabe für alle Umgebungen; `EXISTING/VERIFY` = im Projekt erwähnt/vorhanden, tatsächliche aktuelle Betriebsfähigkeit bei Bedarf neu prüfen; `RESEARCH_ONLY` = Idee, keinerlei Integration behauptet; `PAUSED` = derzeit bewusst zurückgestellt; `REJECT/NO_AUTO_USE` = nicht ohne grundlegend neue Entscheidung einsetzen. Kostenloser Quellcode bedeutet NICHT kostenlosen Modellbetrieb oder lizenzfreie Modellgewichte.

## 0. HARTE 0-€- UND OPEN-SOURCE-VORAUSWAHL – BÜLENTS VORGABE

**Nur frei nutzbare Open-Source-Lösungen als neue ausführende Werkzeuge/Alternativen zulassen**, sofern die tatsächlich verwendeten Komponenten und Modelle für unseren beabsichtigten Einsatz einschließlich kommerzieller Content-Nutzung rechtlich erlaubt sind und **kein Kauf, Pflichtabo, kostenpflichtiger API-Key, verpflichtender Cloud-Service oder neuer kostenpflichtiger Server** für den geplanten Test oder Einsatz nötig ist. Bestehende, von Bülent bereits eingerichtete Infrastruktur und explizit freigegebene Dienste dürfen unverändert weiterlaufen; diese Regel ist kein Auftrag, sie auszubauen oder Geld auszugeben.

**Reihenfolge:** 1) bereits getestetes und derzeit kostenlos betreibbares Open-Source-Werkzeug; 2) quelloffener kostenfreier Ersatz auf vorhandener Hardware/Runtime, nach isoliertem E2E-Test; 3) nur als Archiv notierte Alternativen mit ungeklärten Kosten/Lizenzen. Für die aktive Fallback-Suche **ausschließlich Stufen 1 und 2** verwenden. Ist für eine Funktion aktuell kein nachweislich kostenfrei betreibbarer zulässiger Kandidat vorhanden, ehrlich melden; keinen bezahlten Ersatz einsetzen oder als „kostenlos“ verkaufen.

**Zusätzliche Zulassungsprüfung für jeden Kandidaten:**
- Original-Repository, aktuelle **konkrete Lizenz** und Lizenzen von eingebauten Abhängigkeiten/Modellgewichten prüfen. **Open Source heißt nicht lizenzfrei**: MIT/Apache/BSD sind z. B. echte Lizenzen; AGPL/GPL können Pflichten auslösen und sind nicht automatisch verboten, dürfen aber **nicht ohne vorherige Prüfung des Einsatzes** integriert werden.
- Quellcodekosten **und** tatsächliche API-/Modell-, GPU-/CPU-, Hosting-, Speicher-, Traffic- und Testkosten unterscheiden. „Free Tier“/Testguthaben/wasserzeichenbehaftetes Webprodukt ist **keine** nachgewiesene dauerhafte 0-€-Produktionsalternative.
- Neue Software darf nur auf vorhandener/ausdrücklich freigegebener Runtime laufen; R2 bleibt privater Speicher, keine Render-CPU. Testbeleg, Runtime, Lizenz und 0-€-Betriebsart für den jeweiligen Anwendungsfall dokumentieren.
- Geschlossene SaaS-Produkte, Pflichtkauf, kostenpflichtige Erweiterungen, und ungesicherte „gratis API“-Marketingangebote bleiben **ARCHIVE_ONLY / NICHT IM FALLBACK**. Bereits vorhandene, ausdrücklich genehmigte Dienste nicht ohne Grund abschalten.
- Ein Tool mit noch ungeklärter freier Lizenz oder Betriebsart hat `LICENSE_COST_UNVERIFIED` und **darf nicht aktiv als Ersatz vorgeschlagen/integriert werden**, bis diese Felder anhand der Originalquelle und einer realen Probe geklärt sind.

**Aktuell als quelloffene 0-€-Softwarekandidaten vormerken, aber vor Integration Runtime/Abhängigkeiten prüfen:** FFmpeg (bereits getesteter Pfad, Lizenz/Build beachten), Remotion (Core-SDK-Lizenz und Einsatzbedingungen des konkreten Setups prüfen), PySceneDetect, Auto-Editor, Whisper/faster-whisper, Piper, yt-dlp, Crawl4AI, AutoScraper, Agent-Reach und Codebase-Memory-MCP. **Chopify = LICENSE_COST_UNVERIFIED** bis exaktes Originalprojekt geprüft. Pixelle-Video ist als Quellcode-Kandidat interessant, die gewählten Generierungsmodelle/Cloud-Zugänge müssen aber **separat** nachweislich 0 € und zulässig sein. **OpenMontage/VoiceStudio = LICENSE_REVIEW_ONLY** (AGPL/Modellrechte), nicht automatische Integration.

**Aus der AKTIVEN kostenfreien Alternativenliste aussortieren und nur im historischen Register belassen:** Hailuo, Sora-Webdienst, Kling AI, Artflow, Adobe Firefly, Canva AI, Suno, proprietäre Angebote und externe Anbieter mit möglichen Abo-/API-Kosten; ebenso GPU-intensive Modellprojekte, solange der Betrieb auf vorhandener Hardware ohne Kauf nicht nachgewiesen ist. Auch geschlossene „kostenlose“ Angebote sind keine Open-Source-Alternative. Bestehender Agnes-/ImageRouter-/Provider-Betrieb wird als separate vorhandene Infrastruktur dokumentiert, **nicht** fälschlich als allgemein freie Open-Source-Alternative eingestuft.

## 1. Schnelle Fallback-Matrix – vor jedem erneuten Fehlerlauf

| Benötigte Funktion | Erste Route und Belegstatus | Zweite Route: erst Fähigkeit/Lizenz/Runtime prüfen | Weitere Reserve oder Ausschluss |
| --- | --- | --- | --- |
| **Video aus vorhandenem Material schneiden, Caption/Ton, Export** | **FFmpeg → Factory → privates R2: LIVE_E2E** für konkret getesteten 15-s-Caption-/Audio-Staffellauf (post-Merge PR #299 GitHub-main-Screenshot); FFmpeg-7/15/30-s-Synthetic→R2 separat geprüft | Remotion (grafische Einblendungen; Runtime/konkrete Funktion neu testen); vorhandene kinocut/claudeclip (lokale MCP-Werkzeuge: aktuelle Verfügbarkeit prüfen) | Pixelle-Video für andersartige Text-/Bild→Video-Aufträge zuerst isoliert testen; **OpenChatCut PAUSED**, optional später VPS |
| **Automatisch interessante Clips aus langen Videos finden** | Bereits vorhandene Redaktion/Transkript/Ridererkennung plus **FFmpeg** für konkret bekannte Zeitmarken – keine unbelegte automatische Relevanzerkennung behaupten | **Chopify LICENSE_COST_UNVERIFIED:** exakte Quelle/CLI, Lizenz und Longform→Clip real bestätigen; **PySceneDetect + Transcript + FFmpeg** | Auto-Editor (regelbasierte Schnitte), später SupoClip `PAUSED` |
| **Generatives Video/Bild aus eigener Vorgabe** | Agnes→Factory→privates R2 und ImageRouter→R2: jeweils ältere separate **LIVE_E2E**-Nachweise, Stand erneut prüfen | Pixelle-Video `RESEARCH_ONLY` für Skript→Visuals→Voice→Video; ggf. ComfyUI je Modell/Hardware | Wan/Open-Sora/CogVideoX/Hunyuan/AnimateDiff/LTX nur Hardware-/Gewichte-/Kostenprüfung; kein automatisch kostenloser CPU-Betrieb |
| **Audiotranskription, TTS und autorisierte Stimmen** | Bestehende Audio-/Speech-Contracts und vorhandene Provider separat anhand einer echten Probe prüfen | Whisper/faster-whisper/whisper.cpp für ASR; Piper für TTS `RESEARCH_ONLY` je Runtime | VoiceStudio nur nach AGPL-/Modellgewichte-/Consent-Prüfung; Coqui TTS, Bark, OpenVoice, RVC, Demucs separat bei Bedarf |
| **Öffentliche Racing-Quellen lesen** | Vorhandener **RSS-/offizielle-API-first**-Weg, bestehende Quellenparser und harte Source-Fact-Contract-Prüfung | Crawl4AI nur bei nachgewiesener HTML-/JS-Lücke; AutoScraper nur für einen bekannten zulässigen HTML-Fall | Agent-Reach für einzelne legal unterstützte Quellen/yt-dlp; Scrapling Reserve; Firecrawl erst Kosten/Hosting prüfen |
| **YouTube-Material recherchieren** | Vorhandenes yt-dlp-/Whisper-Konzept, soweit legal verfügbar; Quellenlink, Rechte und Transkript belegen | Agent-Reach als Installer/Router `RESEARCH_ONLY`, statt zusätzlich erfundene Plattform-Zugriffe anzunehmen | yt-analysis-mcp aus IDEA_POOL als weiterer Forschungskandidat; **kein Anti-Bot-/Login-Schutz-Umgehungssystem** |
| **Entwicklung/Repo-Kontext/Sitzungsübergabe** | `MASTER-SNAPSHOT.md`, `PROJECT_GUARDRAILS.md`, GitHub-Commits und gezielte Repo-Suche (**SOURCE OF TRUTH**) | Codebase-Memory-MCP nur isoliert/read-only/no-secrets testen; OpenViking und vorhandene Agent-Memory-Recherche später | Context-Engineering-/Planning-with-Files-Skills; niemals undokumentierte angebliche Tokenersparnis |
| **Mehrere KI-Rollen/Modell-Ausfall** | Vorhandene direkte NVIDIA-/Gemini-/Groq-Adapter nur soweit API, Quoten, Bezahlung und tatsächliche Modellantwort je Route geprüft; bestehender Job-/Produktionsleiter bleibt maßgeblich | Bereits dokumentierte direkte Alternativprovider, begrenzter Retry und sichere Teilresultatkennzeichnung | `OmniRoute PAUSED`; Free Claude Code/DS2API `REJECT/NO_AUTO_USE` als Ersatz; OpenMAIC/LangChain/CrewAI kein zweiter Fabrikkern |
| **Sicherer Medien-Preview / menschliche Freigabe** | Bestehende private R2-Medienrefs + vorhandenes Golden-Tablet-/Approval-Contract: **gesamte abspielbare Telegram-/Dashboard-Live-Strecke NOCH OFFEN** | Bestehende Telegram-/Dashboard-/Worker-Komponenten gezielt verbinden und testen | **Kein** öffentlich geschalteter R2-Bucket, keine ungenehmigte Veröffentlichung, keine Toolinstallation als Ersatz für diese fehlende Schnittstelle |

**Aktueller Fokus:** zuerst privater abspielbarer Video-Preview in Telegram/Dashboard inklusive Auftrag→Provenienz/technische-/Fakten-QM→Golden Tablet→Human Authority und Crash/Retry/Resume-Abnahme. Kein anderes Werkzeug darf Block 6 erneut zum Stillstand bringen.

## 2. Gesamtes dedupliziertes Werkzeugregister aus bisherigen Listen

Die Einträge hier führen alles Bekannte zusammen. Die Namen aus alten Instagram-Kollagen sind überwiegend **Entdeckungs- und keine Live-Nachweise**.

| Bereich | Bekannt / früher aufgelistet | Neue Kandidaten / spätere Reserven | Einordnung |
| --- | --- | --- | --- |
| Video/Schnitt/Render | **FFmpeg**, kinocut, claudeclip, Remotion, OpenChatCut, SupoClip, CutAI, Kaestral | **Chopify [nur nach Lizenz-/0-€-Prüfung]**, PySceneDetect, Auto-Editor, Pixelle-Video, OpenMontage, OpenScreen | OpenChatCut/SupoClip/OmniRoute bewusst pausiert; OpenMontage AGPL als Referenz; Pixelle getrennt testen |
| Videoerzeugung | Agnes, Hailuo, Sora, Wan 2.5/2.6, Kling AI, Artflow, SadTalker, Cosmos-/video-router-Idee | Open-Sora, Open-Sora-Plan, Wan 2.1, CogVideo/X, HunyuanVideo, AnimateDiff, LTX-Video | Riesige GPU-/Modelllizenz-Unterschiede; **nur** konkret nachgewiesene Agnes→R2-Strecke `LIVE_E2E` |
| Bilder/Design | ImageRouter, Pollinations, Cloudflare/Together/NVIDIA, NanoBanana, Stable Diffusion, Copilot, Gemini, Canva AI, Ideogram, Adobe Firefly | ComfyUI, InvokeAI, AUTOMATIC1111/Stable Diffusion WebUI Forge, Diffusers, Upscayl, Krita AI Diffusion, Fooocus, SD.Next, Real-ESRGAN | ImageRouter→R2 als spezifischer separater Live-Weg geprüft; sonst Lizenz/Hardware/Quoten je Kandidat |
| Sprach-/Musikwerkzeuge | Nemotron-ASR/Magpie-TTS-Konzept, MiniMax, Suno, yt-dlp, Whisper, Demucs | faster-whisper, whisper.cpp, Piper, Coqui TTS, Bark, AudioCraft, RVC, OpenVoice, ACE-Step, VoiceStudio | Eigene Sprach-/Persönlichkeitsrechte und Modellgewichte vor jeder Voice-Nutzung prüfen |
| Recherche/Extraktion | RSS, vorhandene Racing-Scanner und Parser, offizielle APIs, Browser Use, yt-analysis-mcp, SearXNG (nach VPS), YouMind, PromptCreek, AIXploria, AlternativeTo | **Agent-Reach**, Crawl4AI, AutoScraper, Scrapling, Firecrawl, GPT Researcher, Vane, PaperQA, Local Deep Research | RSS/API vor Scraping; keine unzulässige Konto-/Bot-Schutz-Umgehung |
| Modellbetrieb/KI-Routing | Direkte NVIDIA, Gemini, Groq, OpenRouter je konkret verifizierter Route, Claude Code, Gemini CLI, Pollinations, OmniRoute | Ollama, llama.cpp, GPT4All, Jan, LocalAI, Open WebUI, AnythingLLM, text-generation-webui, vLLM, MLC LLM, LibreChat, Khoj, DeepSeek-V3 | OmniRoute pausiert; lokal `free source` ≠ GPU-/API-kostenfrei |
| Coding/Agenten | Bestehender GitHub-Prozess, Claude Code, Cline, Continue, planning-with-files und Sprach-Skills; vorhandene Multi-Modell-Cross-Check-Ideen | Aider, OpenCode, Kilo Code, Goose, Tabby, OpenHands, mini-SWE-agent, SWE-agent, Gemini CLI, Mistral Vibe, Orca, ML-Intern, codebase-memory-mcp, claude-link/ai-relay/clipboard-/cross-review | Kein zweiter Coding-Orchestrator ohne Nachweis, dass er etwas **fehlendes** besser erledigt |
| Agenten/RAG/Memory | Eigene Factory-Orchestrierung, eigene Verified-Facts-/Simulation-Grenze, Agent-Memory, OpenViking, Kontext-Skills | LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen, Dify, Flowise, RAGFlow, Haystack, Qdrant, OpenMAIC | OpenMAIC ist primär Lernumgebung, **kein** belegter Fabrik-Betriebsleiter; neue Frameworks nicht blind einbauen |
| Automation/Hosting | GitHub Actions, Cloudflare Worker/Container/R2; n8n, Render/Railway/Fly/Deno/Vercel/Netlify/Replit usw. als Ideen | Activepieces, Sim, weitere leichte Host-Alternativen | R2 ist nur Speicher; VPS-Kauf/Hosting-Ausgaben nur nach Freigabe |
| Andere Anwendungsfelder | Excel/Word-/Dokument-/Lern-/STEM-Werkzeuge und DeepTutor | NumPy/Pandas/SciPy, KiCad, Blender, OpenFOAM etc. aus STEM-Poster | Kein akuter Block-6-Bedarf; bei echten separaten Nutzeraufträgen recherchieren |

## 3. Konkrete Quellen und chronologische Altlisten

| Datei | Künftige Rolle |
| --- | --- |
| [IDEA_POOL.md](IDEA_POOL.md) | Zeitliche Projektideen, Features, bestehende Aufgaben und alte Screenshots. **Keine zweite aktuelle Werkzeugentscheidungsliste**. |
| [FREE_TOOLS.md](FREE_TOOLS.md) | Historische Links, 0-€-Wünsche und spätere Kostenrecherche. Preise/Free-Tier können sich ändern: **nicht** automatisch aktueller Freigabestatus. |
| [TOOL_RADAR_2026-10-01_27_SCREENSHOTS.md](TOOL_RADAR_2026-10-01_27_SCREENSHOTS.md) | Quellenbelege, genauere Lizenz-/Risikoanalyse und Originalprojekt-Links für die 27 Bilder vom 01.10.2026. |
| [../config/MEDIA_TOOLS.md](../config/MEDIA_TOOLS.md) | Historische lokale Windows-Pfade/CLI-Ausstattung. Bei Container/VPS nichts davon als vorinstalliert annehmen. |
| [../PROJECT_GUARDRAILS.md](../PROJECT_GUARDRAILS.md) | Verbindliche Qualitäts-, autonomes Fallback-, menschliche Veröffentlichungs- und Merge-Regeln. **Immer vorrangig**. |

## 4. Pflege-/Automatikregel

1. Neue Screenshots oder Repos: **zuerst hier** einen vorhandenen Funktionsbereich suchen; Kandidaten ergänzen statt neue konkurrierende Liste bauen. Hintergrundbelege in datiertem Radar/IDEA_POOL nur bei Bedarf.
2. Vor neuer Abhängigkeit oder nach spätestens 2–3 unterschiedlichen vergeblichen Versuchen: Matrix prüfen; kleinsten belegten Ersatz zuerst, sonst `RESEARCH_ONLY`-Alternative isoliert und kosten-/lizenz-/sicherheitsbewusst evaluieren. Kein kostenpflichtiger Account/Kauf ohne Bülent.
3. Für echten Statuswechsel `RESEARCH_ONLY → LOCAL_TESTED → LIVE_E2E`: Testumfang, GitHub-Run/Commit, Runtime, Betriebskosten, Modelllizenzen, Hash/Provenienz, Negativ-/Positivkontrollen und End-to-End-Nachweis dokumentieren. Nicht allein aufgrund grünem Contract-Test hochstufen.
4. Funktion der bestehenden Fabrik und Bülents `Ändern / Verwerfen / Posten` immer unverändert schützen; keine Veröffentlichung ohne gültige eigene Freigabe.
5. Nach neuen Werkzeugentscheidungen **nur diesen Index als Auswahlwahrheit** aktualisieren. Historische Listen/Details bleiben als rückverfolgbare Quellen; den Eintrag im `MASTER-SNAPSHOT.md` aktuell halten. Neue Chats beginnen stets hier.
