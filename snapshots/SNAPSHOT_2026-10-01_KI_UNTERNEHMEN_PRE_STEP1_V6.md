# V6 SNAPSHOT – KI-UNTERNEHMEN / VOR SCHRITT 1
**01.10.2026, ca. 20:18 CEST.** Verifizierter Ausgangs-`main`: `e1ebc471f22b8ad1512ac42dd30080478590413c`. Git-Wiederherstellungsbranch: `backup/2026-10-01-ai-central-vision-pre-stage2-v6`. Es handelt sich um einen Zeitpunkt und NICHT um einen unveränderlich geschützten Git-Tag.

## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN
Vor Arbeiten vollständig `PROJECT_GUARDRAILS.md` lesen; daneben `AGENTS.md`, `MASTER-SNAPSHOT.md`, V6-Vollübergabe und offenen V5-Handover-Kopie auf dem V6-Branch (Original-PR #286 offen). Kein Merge/Deploy/Publisher/kostenpflichtiger Dienst ohne autorisierte Freigabe; keine künstlichen PASS-Ergebnisse und keine simulierten Funktionen als LIVE ausgeben.

## Tatsächlicher Stand zum Sicherungszeitpunkt
- PR #287 19 Commits nach Bülents Zustimmung gemergt, Merge `9786362319b72b1361da73415bd2d43af455bc24`. Hauptproduktionspfad bleibt unverändert `--free-only`; Opt-in `--free-team` ist in Code vorhanden und bisher nur als synthetischer manueller API-Test erprobt.
- Manueller Lauf #36903543954: Offline-SUCCESS; Nemotron Research ANSWER; Kimi Diagnosis ANSWER; OpenRouter Challenge UNAVAILABLE. Gesamtworkflow FAILURE ausschließlich wegen separatem OmniRoute-Serverstart; keine falsche 3/3-Abnahme. OmniRoute auf Bülents Wunsch vorerst pausiert.
- Vorheriges reales Dashboard/R2-Nutzer-E2E #36891798853 2/2 OpenRouter-Free-Rollen ANSWER. Anderer realer Auftrag #36892856318 nur 1/2 ANSWER. Telegram-Poller #36903933368 SUCCESS; echter `/zentrale ergebnis ID`-E2E noch zu verifizieren.
- Factory Blocks 1–9, R2, ImageRouter→R2 und Agnes Video→R2 historisch nachgewiesen. OpenChatCut Block 6 bleibt live unvollständig; #271 readiness und gestapelter #278 interner Container-Loopback offen. Gesundheit des Workers beweist kein gesundes MCP.
- V5-Handover, V5-Snapshot und V5-Backup-Protokoll auf diesem V6-Branch mit archiviert; historischer separater PR #286 ist offen, V5 noch nicht main. Dieses V6-Dokument entsteht ebenfalls ungemergt in eigenem Doku-PR. Automatische laufende GitHub-Reporter können main jederzeit weiterschieben; aktuellen HEAD erneut prüfen.

## Bülents freigegebene nächste Reihenfolge
1. **JETZT** direkte NVIDIA Nemotron/Kimi als KI-Mannschaft behalten, kostenverifiziert Gemini und Groq ergänzen, gemeinsames Team im bestehenden R2-Dashboard und Telegram mit echten unabhängigen Antworten und Human Review verbinden. Keine OmniRoute-Bremse. Kein Ersatz der bestehenden produktiven Free-Route vor E2E-PASS.
2. Produktionsleiter und deterministischen Ressourcenmanager auf vorhandene Factory-Verträge setzen. Shared Job/Revision/Artefakt-Provenienz, zeitbegrenzte Wiederaufnahme, Auslastungs- und API-Quota-Grenzen; Container gezielt via Cloudflare Worker wecken.
3. Block 6: OpenChatCut #271/#278 diagnostisch auswerten, FFmpeg/Remotion bei Bedarf vergleichen und echten Video/Render/R2/Hash/ffprobe-Live-Staffellauf abschließen.
4. Mehragenten-Deep-Research, dauerhaft parallele Content-Fabrik plus spontane KI-Werkstatt, geschütztes Goldenes Tablett und Publisher nur nach Bülents ausdrücklicher Freigabe.

## Quellen und Wiederaufnahme
Haupttext: `docs/PROJEKT_UEBERGABE_6_2026-10-01_KI_UNTERNEHMEN.md`; Sicherungsgrenzen `docs/BACKUP_PROTOKOLL_2026-10-01_V6.md`; weitere Historie V5 PR #286 und ältere Snapshots. Inhaltliche V6-Zusätze: universelles KI-Unternehmen mit Produktionsleiter, Ressourcenmanager, Teamleitern, Auftragsübergabe, Deep Research und 24/7 zwei Geschäftsbereiche. Dies ist neue Vision und NICHT Behauptung, all diese Funktionen existierten bereits.
