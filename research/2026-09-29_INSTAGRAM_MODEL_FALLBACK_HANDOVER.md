# ÜBERGABE AN CHATGPT – KI-MODELLE AUS INSTAGRAM-KARUSSELL

**Datum:** 2026-09-29
**Quelle:** Instagram @tech_hacks.ai – Karussell „No need to pay..." (170+ Modelle)
**Zweck:** Prüfung, ob eines dieser Modelle für die Racing-Pipeline im KI-SOCIAL-AGENT genutzt werden kann

---

## 1. Kontext

Projekt: **KI-SOCIAL-AGENT** (Repo: Edirne22/KI-SOCIAL-AGENT)
Aktuelle Racing-LLM-Kette: **Agnes → Gemini → NVIDIA (Nemotron 3.5 Lightning)**
Problem: Agnes hat Free-Tier-Rate-Limits (HTTP 429), daher bereits Cooldown + Fallback eingebaut.

**Bedarf:** Zusätzliche oder bessere API-zugängliche Modelle als Fallback oder Primärquelle.

---

## 2. Die 5 Modelle aus dem Karussell

### Modell 1: GLM-5.3-Flash
- Anbieter: Zhipu AI
- Multimodal: Coding, Reasoning, Agent-Processing, Bildverständnis
- 320 Mrd. Parameter total, 18 Mrd. aktiv pro Task (MoE)
- Vorteil laut Post: schnell, kostengünstig, weniger Rechenressourcen

### Modell 2: Qwen Studio
- Anbieter: Alibaba
- Schreiben, Research, Programmieren, Dateianalyse, Bildgenerierung
- Enthält laut Post „Qwen 3.8 MAX" – 100 % kostenlos
- Plattform mit verschiedenen Qwen-Modellen

### Modell 3: StepFun 3.5
- Anbieter: StepFun
- Fokus: Programmierung, Agenten, komplexe mehrstufige Aufgaben
- 256K Context
- Open Source, lokal nutzbar auf ausreichend starker Hardware

### Modell 4: Xiaomi MiMo-V2.5-Pro
- Anbieter: Xiaomi
- Reasoning, Programmierung, Agenten
- 1,02 Billionen Parameter, 42 Mrd. aktiv pro Token
- 1 Mio. Context-Tokens
- Explizit für lang laufende Tasks + tausende Tool-Calls entwickelt

### Modell 5: Kimi
- Anbieter: Moonshot AI
- Lange Dokumente, Research, große Datenmengen
- Erstellt Präsentationen, Webpages, Reports
- Ersetzt laut Post mehrere Tools

---

## 3. Offene Fragen an ChatGPT

1. **API-Zugang:** Welche dieser Modelle sind über eine **OpenAI-kompatible API** erreichbar (base_url + API-Key)?
2. **Free Tier:** Welche haben einen echten kostenlosen Tier mit ausreichenden Rate-Limits für unsere Pipeline (50–100 Requests pro Lauf)?
3. **Tool-Calling:** Welche unterstützen **strukturiertes Tool-Calling** und/oder JSON-Mode? (Voraussetzung für unsere Racing-QM-Pipeline mit strukturierten Outputs)
4. **Kontext-Fenster:** Reicht das jeweilige Context-Fenster für unsere typischen Artikel-Prompts (ca. 3.000–8.000 Tokens)?
5. **Deutsch/Türkisch:** Wie gut sind die Modelle für **deutsche und türkische Texte**? (Wir erzeugen deutsche Redakteurstexte aus türkischen/englischen Quellen)
6. **Empfehlung:** Welches Modell würdet ihr als **vierten Fallback** nach Agnes/Gemini/NVIDIA einsetzen? Welches ist für unser 0-€-Ziel am besten geeignet?

---

## 4. Wichtige Rahmenbedingungen

- **0-€-Philosophie:** Nur kostenlose oder Free-Tier-Modelle
- **Rate-Limit-Historie:** Agnes Free-Tier ist zu klein → Cooldown + Fallback nötig
- **Provider-Kette:** Muss über `config/model_router.json` und `llm_client.py` einbindbar sein
- **Keine China-spezifische Anmeldung:** Falls Modell nur mit chinesischer Handynummer registrierbar ist, ist es für uns unbrauchbar
- **Keine Privacy-Risiken:** Keine sensiblen Daten (Secrets, Tokens) an neue Provider geben

---

## 5. Was NICHT gefragt ist

- Keine Migration der kompletten Pipeline auf ein neues Modell
- Keine Architektur-Änderung
- Nur: **Erweiterung der Fallback-Kette um ein weiteres Modell**

---

**Ende Übergabe an ChatGPT**
