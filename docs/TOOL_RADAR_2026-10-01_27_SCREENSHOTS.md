**HINWEIS – ZENTRALE AUSWAHL:** [docs/TOOL_INDEX.md](TOOL_INDEX.md) ist die **einzige maßgebliche Werkzeug- und Alternativenliste**, nach Nutzerfunktionen sortiert. Diese Datei bleibt als historische Quelle bzw. Detailsammlung erhalten; bei Ausfall/Neuintegration zuerst den Index prüfen und nur ihn als aktuellen Auswahlstatus pflegen.

# Sichtung: 27 Instagram-Screenshots – Werkzeug-Radar (01.10.2026)
 
**Status:** Recherche und Ideenablage, NICHT Installation, Live-Integration, Kostenfreigabe oder Herstellerempfehlung. Quelle: Bülents 27 Screenshots aus drei Nachrichten am 01.10.2026; Instagram-Angaben (Sterne, „100 % kostenlos“, Leistungsversprechen) sind Werbeaussagen, keine Abnahmebelege. Bei neuen Erkenntnissen aktuelle Original-Repos erneut prüfen.

## Verbindlicher Projektrahmen

Zuerst `PROJECT_GUARDRAILS.md` §14 und `MASTER-SNAPSHOT.md` lesen: **Funktion vor Werkzeug**. Sprachauftrag/Upload → vorhandene KI-Fabrik → überprüftes Ergebnis → privater Preview → Bülent als letzte Veröffentlichungsautorität. FFmpeg→Factory→privates R2 hat einen grünen post-Merge-main-Live-Workflow (#299) mit `factory-offline` und `factory-live-private-r2` gemäß Bülents GitHub-Screenshot; kompletter Nutzer-/Telegram-Preview-Staffellauf ist davon NICHT bewiesen. OpenChatCut/SupoClip und OmniRoute blockieren Block 6 nicht. Keine zusätzliche externe Plattformbeschaffung, keine fremde Infrastruktur und keine kostenpflichtigen APIs ohne ausdrückliche Erlaubnis.

## FUNKTIONSBEZOGENE FALLBACK-MATRIX – VOR JEDEM NEUEN TOOL-VERSUCH LESEN

**Regel:** Nicht vom kaputten Produktnamen ausgehen, sondern von der gewünschten Nutzerfunktion. Im Fehlerfall die Kandidaten dieser Tabelle gegen die vorhandene Runtime und die zum jeweiligen Zeitpunkt neu geprüften Lizenzen/Abhängigkeiten abgleichen. Status niemals hochstufen ohne eigenen Beleg.

| Nutzerfunktion / Ausfall | Sofort einsetzbarer bzw. bereits bewiesener Ansatz | Nächster Kandidat (erst isoliert testen) | Zusätzlicher Ersatz/Notiz |
| --- | --- | --- | --- |
| Video aus vorhandenem Material, Schneiden, Text, Ton, Export; **OpenChatCut fällt aus** | **FFmpeg über unabhängigen Factory-Adapter → privates R2**; echter post-Merge-main 15-s-Caption-/Audio-Live-Workflow nachgewiesen. Für unbekannte Editing-Anforderungen Funktion gesondert testen. | Vorhandenes **kinocut/claudeclip** bzw. **Remotion** auf die konkrete zusätzliche Funktion und die jeweilige Runtime prüfen; **Pixelle-Video** für komplette Script→Video-Aufträge als isolierten Kandidaten | OpenMontage nur Architektur-Referenz bis AGPL-/Runtime-Prüfung; OpenChatCut später ggf. VPS, nicht Block-6-Voraussetzung. |
| Relevante Ausschnitte aus langen Videos ermitteln; **SupoClip fällt aus** | **FFmpeg** für nachweisbar vorgegebene Zeitsegmente. Keine Behauptung, FFmpeg allein finde redaktionell interessante Szenen autonom. | **Chopify**: erst kanonisches Projekt, Lizenz, tatsächlichen CLI-/API-Betrieb und Longform→Clip-E2E bestätigen. Alternativ **PySceneDetect** (Schnitt-/Szenenkandidaten) + Transkript-/Rider-/Quellen-QM + FFmpeg | **Auto-Editor** für regelbasierte Audio-/Pausenschnitte; Featureparität nur nach einzelnem E2E und menschlich überprüfbaren Clips. |
| Neue Artikel/Quellen extrahieren; Parser/Crawler fällt aus | Bestehende **offizielle Datenquelle/RSS** und validierte quellgebundene Parser bevorzugen | **Crawl4AI** für zulässige öffentliche Seiten mit Markdown/Metadaten; kleiner bekannter HTML-Fall: **AutoScraper** | **Agent-Reach** nur als geprüfter Router für Unterwerkzeuge/YouTube; Scrapling nur als spätere Reserve, keine Anti-Bot-Umgehung. |
| Tool für YouTube-Transkript/Video-Discovery fehlt | Bestehende **yt-dlp/Transkriptionsroute**, wo rechtlich/technisch verfügbar; vorhandenes Whisper-/ASR-Konzept | **Agent-Reach** für unterstützte Plattformzugriffe nach Einzelprüfung | Keine Garantie für Plattform-Verfügbarkeit und keine Umgehung von Zugriffsbeschränkungen. |
| Lokale Coding-KI verliert Repo-Kontext | Projektdateien **MASTER-SNAPSHOT / GUARDRAILS / git / gezielte Repo-Suche** | **Codebase-Memory-MCP** nur isoliert, lesebeschränkt, ohne Secret-Zugriff | Keine behaupteten „99 % Einsparung“ ohne eigenes Benchmark. |
| Voice/Transkript für Videos fehlt | Vorhandene ASR-/Voice-Contracts; separaten zugelassenen Provider je Funktion verifizieren | Whisper/faster-whisper/whisper.cpp und Piper zuerst je CPU-/Sprachtest; **VoiceStudio** nur nach AGPL-/Modellrechte-/Einwilligungsprüfung | Keine Sprachklonung ohne berechtigte Einwilligung. |
| Externer Modellrouter/Proxy instabil | Direkte bekannte **NVIDIA/Gemini/Groq**-Adapter nur bei belegter Berechtigung/Quota; OmniRoute **pausiert** | Bei echtem Bedarf zuerst eigene begrenzte Provider-Auswahl/Failover messen | **Free Claude Code/DS2API** kein produktiver Schnell-Fallback; keine unautorisierten Webchat-API-Wrapper. |

**Ablauf nach 2–3 sinnvoll unterschiedlichen erfolglosen Versuchen mit einem externen Tool:** Fehlersignatur + konkrete Nutzerfunktion dokumentieren → obige funktionsbezogene Alternativen sichten → kleinsten bereits nachgewiesenen Ersatz wählen → Feature-Gap offen benennen → Negativ-/Positivkontrollen + relevanten End-to-End-Staffellauf inkl. Hash/Provenienz/Approval durchführen → erst dann produktiv umschalten. Für Kandidaten ohne Beleg bleibt der Status **RESEARCH_ONLY**, nicht `LIVE`. Sicherheitskritische Root-Cause-Probleme niemals durch bloßen Toolwechsel verdecken.

## Konkret in Arbeitsprüfung aufnehmen

| Tool / Originalprojekt | Möglicher Nutzen und enge Probe | Vorher prüfen |
|---|---|---|
| **[Pixelle-Video](https://github.com/ATH-MaaS/Pixelle-Video)** (Screenshot nennt früher AIDC-AI) | Sehr passender **separater** Evaluierungskandidat für Thema/eigene Bilder → Skript/Bilder/Voice/Video. Eigene Materialien werden laut README unterstützt. Als mögliche Ergänzung oder austauschbare Video-Komponente testen, **nicht** Factory/Fact-QM ersetzen. | Apache-2.0-Projekt, aber wählbare externe Modelle/ComfyUI und deren eigene Schlüssel, Modellrechte, Kosten, CPU/GPU; gemessene Qualität, Quellenbindung, Speicher-/Freigabe-Adapter. Die Instagrambehauptung „lokal und kostenlos“ ist keine Betriebsgarantie. |
| **[Agent-Reach](https://github.com/Panniantong/Agent-Reach)** | Als vorhandenen früher notierten Kandidaten für YouTube-/öffentliche Quellen-Discovery und Diagnose eines vorhandenen yt-dlp/RSS-Pfads abgleichen. Lieber zunächst read-only unter kontrollierter Runtime. | MIT laut Upstream; Plattformfähigkeiten abhängig von Unterwerkzeugen, Logins/Cookies und Änderungen; „alle Plattformen ohne API-Gebühren“ nicht garantieren. Kein Social-Login-/Cookie-Scraping für Meta-Engagement, keine Umgehung von Sperren, robots/AGB/Zugriffsrechten respektieren. |
| **[Crawl4AI](https://github.com/unclecode/crawl4ai)** | Ergänzende HTML→strukturierte/Markdown-Extraktion für **zulässige öffentliche Artikel** nur dort, wo RSS/offizielle API und heutige Discovery versagen. | Apache 2.0 laut Originalprojekt, Browser-/CPU-Last, robots/AGB, Render-Kompatibilität, belegbare Quell-URL/Fakten. Doppelimplementierung vermeiden. |
| **[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)** | Optionaler lokaler, schreibgeschützt eingegrenzter Repo-Index für lange KI-Coding-Sitzungen, nicht das redaktionelle Story-/Quellen-Memory. | MIT laut Upstream. Tool greift tief auf Dateisystem/Agent-Konfiguration zu und startet Prozesse; nur isoliert, vorab Sicherheitsprüfung, keinerlei Zugang zu Secrets. Screenshot-„99 % Token sparen“ nicht als eigenen Benchmark ausgeben. |
| **[OpenMontage](https://github.com/calesthio/OpenMontage)** | **Architektur-/Funktionsreferenz** für Schnitt-/Video-Pipeline und FFmpeg/Remotion, insbesondere gezielte wiederverwendbare Ideen statt zweites autonomes Gesamtsystem. | AGPL-3.0 laut Originalprojekt; keine Übernahme von Code/Runtime in bestehenden Stack ohne explizite Lizenz-/Architekturprüfung. Nicht als Abhängigkeit von Block 6 einführen. |

## Auf späteren eigenen, isolierten Prüfstand

| Kandidat | Warum später / Grenzen |
|---|---|
| **[VoiceStudio](https://github.com/debpalash/VoiceStudio)** | Lokale TTS, eigenes autorisiertes Voice-Cloning, Dubbing/Transkript. Anwendung **AGPL-3.0**, Modellgewichte separat und zum Teil nicht für kommerzielle Nutzung lizenziert; eigener sauberer Consent. Für gegenwärtiges Voice-/Caption-Contract und FFmpeg nicht Voraussetzung. |
| **[AutoScraper](https://github.com/alirezamika/autoscraper)** | Schlanker Python-Extraktor für **einzelne bekannte** Websites; erst bei belegtem Bedarf, da RSS/aktuelle Quellenadapter vorgehen. Screenshot verallgemeinert unzulässig zu „jede Seite/No selectors/Cloud“. MIT laut Originalprojekt. |
| **Scrapling** (Screenshot nennt `scrapling/scrapling`; kanonisches aktuelles Repo/Lizenz erst bestätigen) | Ein weiterer Scraping-Kandidat mit Funktionsüberschneidung zu Crawl4AI/AutoScraper; keine parallelen Scraper-Farmen. Umgehung von Anti-Bot-Maßnahmen ist keine Projektanforderung. |
| **[Open-Sora](https://github.com/hpcaitech/Open-Sora), [Wan](https://github.com/Wan-Video), [CogVideoX](https://github.com/THUDM/CogVideo), [HunyuanVideo](https://github.com/Tencent/HunyuanVideo), [Open-Sora-Plan](https://github.com/PKU-YuanGroup/Open-Sora-Plan), [AnimateDiff](https://github.com/guoyww/AnimateDiff)**; in zweiten Collagen auch **LTX-Video** | Optionale Modell-/GPU-Recherche; „Repo kostenlos“ ≠ Betrieb/Modell/Cloud kostenlos. Keine großen Gewichte auf kleine Cloudflare-CPU-Container; separat auf Hardware, Lizenz der Gewichte, Benchmarks und tatsächlichen Nutzwert gegenüber Agnes prüfen. |
| **[OpenScreen](https://github.com/siddharthvaddem/openscreen)** | Bildschirmaufnahme-/Demo-Editor, momentan keine Aufgabe für die Reels-Factory; für späteres Tutorial interessant, zunächst Projekt/Link erneut verifizieren. |
| **[DeepTutor](https://github.com/HKUDS/DeepTutor)** | Interaktive Lernhilfe aus Dokumenten; andere Produktfunktion, allenfalls universelle KI-Werkstatt später. |
| **[ML-Intern](https://github.com/huggingface/ml-intern)** | ML-Experiment-/Forschungsagent, kein Ersatz für unsere beleggebundene Motorrad-Redaktion. |
| **Mistral Vibe** | Externer Coding-/Agentenkandidat, keine akute Lücke; zunächst Anbieterbedingungen/Kosten prüfen, kein zweites Harness ohne Nutzenmessung. |

## Nicht als neue Kernmaschinen einbauen

- **[OpenMAIC](https://github.com/THU-MAIC/OpenMAIC)**: Das offizielle Projekt ist eine *Multi-Agent Interactive Classroom* / Lernumgebung, **kein allgemeiner autonomer KI-Firmen-Betriebsleiter**, entgegen Instagram-Beschreibung. MIT laut offizieller Lizenz; allenfalls als Designreferenz für spätere Lernfunktion.
- **[Orca](https://github.com/stablyai/orca)**: Produktversprechen „mehrere Coding-Agenten mobil/parallel“ aus Screenshot allein nicht verifiziert. Unser vorhandenes Orchestrator-/GitHub-/BLOCKRUN-Konzept nicht durch zweite Laufzeit ersetzen; erst echten repo/funktionalen Bedarf belegen.
- **[Free Claude Code](https://github.com/Alishahryar1/free-claude-code)**: Noch ein Provider-Proxy, Überschneidung mit zurückgestelltem OmniRoute. Marketing-Tokenversprechen, echte API-Berechtigungen, Kontokosten und Nutzungsbedingungen zuerst prüfen; kein erneutes Router-Experiment in Block 6.
- **[DS2API](https://github.com/CJackHwang/ds2api)**: DeepSeek-Webchat-zu-API-Wrapper; Screenshot zeigt AGPL-3.0. Cookie-/Account-Rotation und mögliche Anbieterbedingungen/Risiken sind keine zulässige 0-€-Abkürzung; **nicht** in unsere produktive Provider-Kette.
- **[curl-impersonate](https://github.com/lexiforest/curl-impersonate)**: Werkzeug für Browser-ähnliche HTTP-Anfragen; Screenshot wirbt ausdrücklich mit Blocker-/Bot-Schutz-Umgehung. Kein Bedarf als Standard-Racing-Collector, nicht in Produktivbetrieb übernehmen.
- **Firecrawl**: Mögliche externe/selbstgehostete Crawl-Plattform, aber vorhandene RSS/API-Pfade und Crawl4AI vergleichen. Selbsthosting/Cloud-Zusatzkosten, Abhängigkeiten und Lizenz beachten; offizielle Cloud-Free-Nutzung ist quotiert, nicht unbegrenzt.
- **OmniRoute**: Bereits bekannt und vorerst **pausiert**; wiederholtes Social-Media-Bild ist keine neue Erkenntnis.
- **Meta-/Instagram-/Facebook-Scraping**: keinen inoffiziellen Cookie-/Browser-Workaround für unsere Accounts als produktive Lösung; offizielle Meta-Schnittstellen bevorzugen.

## Screenshot-Kollagen: erfasst, aber kein neuer Installationsauftrag

- **„50 actually free“, „32 open-source AI tools“ und „20 GitHub repos“** überschneiden sich untereinander und mit `docs/FREE_TOOLS.md`/`docs/IDEA_POOL.md`: Ollama, llama.cpp, Jan, LocalAI, Open WebUI, AnythingLLM, vLLM; Cline, Continue, Aider, OpenHands, Tabby, Gemini CLI/Claude Code; ComfyUI, InvokeAI, AUTOMATIC1111, Diffusers, Stable Diffusion WebUI Forge, Upscayl; Whisper, whisper.cpp, faster-whisper, Piper, Coqui TTS, Bark, AudioCraft, Demucs, RVC, OpenVoice; LangChain/LangGraph/LlamaIndex/CrewAI/AutoGen/Dify/Flowise/RAGFlow/Haystack/Qdrant; Browser Use, GPT Researcher, Vane, PaperQA, local Deep Research, ACE-Step; n8n, Activepieces, TensorFlow, PyTorch, Transformers, DeepSeek-V3 u. a.
- **STEM-Software-Poster** ist für ein anderes Anwendungsfeld (z. B. NumPy, SciPy, Pandas, scikit-learn, Julia, KiCad, Blender etc.); für die aktuelle Content-Fabrik kein zusätzliches Coding- oder Medienwerkzeug ableiten.
- **„Business AI stack“ / „for coding“** sind subjektive Instagram-Balkengrafiken, keine belastbaren Messwerte. ChatGPT, Cursor, Claude, Lovable, Zapier, Perplexity, Higgsfield nicht auf Basis dieser Grafiken neu beschaffen.

## Konkrete Teststrategie ohne Block-6-Verzögerung

1. Zuerst bestehenden FFmpeg→Factory→privates R2-Nachweis behalten; **fehlende private abspielbare Telegram-/Dashboard-Vorschau sowie vollständigen Nutzerauftrag→QM→Human-Review-Handoff** abschließen, einschließlich Negativ-, Retry- und Resume-Prüfung.
2. Erst danach **Pixelle-Video** auf *einen* isolierten Testfall mit eigenem lizenziertem Quellmaterial, möglichst schon vorhandenen kostenfreien Modellen und gemessener CPU-/GPU-/API-Nutzung prüfen. Nicht den bestehenden R2- oder Quellen-/Human-Approval-Weg ersetzen.
3. Bei dokumentierter Recherche-Lücke **Crawl4AI** oder **Agent-Reach**, jeweils mit legalem read-only Probeumfang und RSS/API-Vergleich, testen. Bei wiederholtem externem Scheitern nach den neuen Guardrails auf nachgewiesenen Ersatz ausweichen.
4. **Codebase-Memory-MCP** nur in sauber isoliertem Code-Index-Profil evaluieren. **OpenMontage** als Muster lesen, nicht blind integrieren. VoiceStudio erst nach Modell-/Netzwerk-/Lizenz- und Einwilligungsprüfung.
5. Screenshots nur als **Entdeckungsquelle**, offizielle Dokumentation als Quelle technischer Fakten, und eigener Live-Staffellauf als Beweis tatsächlicher Projektintegration verwenden. Alle neuen Kandidaten bleiben bis dahin `RESEARCH_ONLY`.

## Geprüfte Originalbelege bei Erfassung

- Pixelle: https://github.com/ATH-MaaS/Pixelle-Video
- Agent-Reach: https://github.com/Panniantong/Agent-Reach
- Crawl4AI: https://github.com/unclecode/crawl4ai
- Codebase-Memory-MCP: https://github.com/DeusData/codebase-memory-mcp
- OpenMontage: https://github.com/calesthio/OpenMontage
- OpenMAIC: https://github.com/THU-MAIC/OpenMAIC
- VoiceStudio: https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md
- AutoScraper: https://github.com/alirezamika/autoscraper
- Firecrawl: https://github.com/firecrawl/firecrawl-docs/blob/main/billing.mdx
- Free Claude Code: https://github.com/Alishahryar1/free-claude-code

**Pflege:** Entscheidungen `RESEARCH_ONLY`, `TESTED_LOCAL`, `LIVE_E2E` und `REJECTED/DEFERRED` nicht vermischen. Neue Evidenz mit Datum, Hardware, Kosten, Lizenz, Provenienz, Job-/Run-Link und dauerhaftem Regressionstest protokollieren. Keine fremden Codebestandteile ohne entsprechende Lizenzprüfung übernehmen.
