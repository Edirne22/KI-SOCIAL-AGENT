# Agenten-Bibliothek – Edirne 22

Die Agenten sind Teil **einer** KI-Zentrale mit Content-Fabrik und universeller KI-Werkstatt. [Verbindliche Hierarchie und Übergaben](../docs/AGENCY_ORG_AND_HANDOFF.md). Eine Rollenbeschreibung ist keine nachgewiesene laufende Agenteninstanz; technische Laufzeit-, Zugangs- und Freigabestatus müssen pro Workflow aktuell überprüft werden.

## Rollenverzeichnis

| Datei | Fachrolle | Auftrag und Grenze |
| --- | --- | --- |
| [01_content_creator.md](01_content_creator.md) | Content Creator | Inhalte und Hooks aus belegten Fakten; niemals eigenständig veröffentlichen |
| [02_instagram_curator.md](02_instagram_curator.md) | Instagram Curator | Format-/Plattformanpassung nach Redaktion |
| [03_tiktok_strategist.md](03_tiktok_strategist.md) | TikTok Strategist | TikTok-/Shorts-Konzepte und plattformspezifische Varianten |
| [04_social_media_strategist.md](04_social_media_strategist.md) | Social Media Strategist | Themen, Wochenplanung und Plattformmix; **keine** Rechen-/Job-Runtime-Steuerung |
| [05_research_synthesist.md](05_research_synthesist.md) | Research Synthesist | Quellen recherchieren und verifizieren; Factory-Newsroom-Faktenvertrag verbindlich |
| [06_reddit_community_builder.md](06_reddit_community_builder.md) | Reddit Community Builder | Community-Antwortentwürfe; keine automatische externe Kommunikation |
| [07_video_optimization.md](07_video_optimization.md) | Video Optimization | Redaktioneller Schnitt-/Caption-Plan; rendert/publiziert nicht eigenmächtig |
| [08_paid_social_strategist.md](08_paid_social_strategist.md) | Paid Social Strategist | Nur Kampagnenentwürfe, keine finanziellen Verpflichtungen |
| [09_quality_agent.md](09_quality_agent.md) | Quality Agent | Workflow-/Systemstatus und Hinweise; ersetzt nie verpflichtende Source-Fact-/Final-/Security-Gates |
| [10_follow_analysis_agent.md](10_follow_analysis_agent.md) | Follow Analysis | Nur zulässige öffentliche Format- und Community-Muster analysieren |
| [11_system_restart_agent.md](11_system_restart_agent.md) | System Restart | Nur fest freigegebene wartende Analyse-/Wartungsflows, niemals Publisher oder Außenwirkung |
| [12_music_agent.md](12_music_agent.md) | Music Agent | Nur autorisierte Musik und bereits freigegebene Medien nach Lizenzprüfung |
| [14_memory_curator.md](14_memory_curator.md) | Memory Curator | Evidenzgebundenes Lernen und Regression; keine autonomen neuen Freigaben |
| [15_finance_planner.md](15_finance_planner.md) | Finance Planner | Analyse/Planung; Geldentscheidungen bei Bülent |
| [17_instagram_engagement_agent.md](17_instagram_engagement_agent.md) | Instagram Engagement | Klassifikation und Antwortvorschläge; echter Versand nur mit Einzelfreigabe |
| [18_tour_ride_story_agent.md](18_tour_ride_story_agent.md) | Tour Ride Story | Aus eigenen Tourdaten privates, belegbares Story-Paket ohne Veröffentlichung |
| [19_ki_integrationsingenieur.md](19_ki_integrationsingenieur.md) | KI-Integrationsingenieur | Geprüfte Maschinen über bestehende KI-/GitHub-Routen integrieren; isolierte Tests und unabhängige technische Abnahme |
| [20_maschinen_scout.md](20_maschinen_scout.md) | Maschinen-Scout | Öffentliche Repos, Skills, APIs und Storage-/CPU-/GPU-Alternativen entdecken; vor Integration Research und Security |
| [21_instandhaltungsagent.md](21_instandhaltungsagent.md) | **Instandhaltungsagent** | Zentraler technischer Reparaturagent; darf über den kontrollierten OpenCode/Claude-Code-Weg selbstständig Code/Patches erzeugen, ändern und testen; Repair-Logging und Funktionsnachweis verpflichtend |

**Agent 21 ist der Instandhaltungsagent.** Es existiert kein zweiter separater Instandhaltungsagent. Agent 11 bleibt unverändert der System-Restart-Agent.

**Weitere tatsächliche Komponenten:** `facebook_engagement.py` ist eine separate historische Facebook-Engagement-Implementierung und gegenwärtig nicht als neu nummerierter Agent aktiv. `content_factory_newsroom.py`, `content_factory_creative.py`, `content_factory_media_production.py` und Human/Publisher-Verträge sind zentrale Module und nicht automatisch eigenständige 24/7-Prozesse.

**ID-Konflikt:** Historische Übergaben bezeichnen den Facebook-Engagement-Agenten teilweise als „Agent 18“, während die aktuelle Datei `18_tour_ride_story_agent.md` den Tour-Agenten meint. Maschinelle Aufträge dürfen bis zu einer expliziten Alias-/Migration nur **eindeutige Role-IDs/Dateinamen**, niemals nackte alte Nummern, verwenden.

## Hierarchie und Ausführung

Die menschliche Geschäftsführung autorisiert nur tatsächlich erlaubte Aufträge. Eine einzige zentrale Auftragsannahme über bestehendes Dashboard/Telegram reicht an den noch vollständig abzunehmenden deterministischen Produktionsleiter weiter; dieser aktiviert den passenden fachlichen Teamleiter und nur die nötigen Spezialrollen. Unabhängige Source-Fact-, Rights-, Security- und Final-Gates schützen die Ausgabe; ein fertig geprüftes Ergebnis kommt auf das Goldene Tablett. Externe Veröffentlichungen, Kosten und private Medien bleiben unter Bülents konkreten Freigaben.

Technische Maschinenhierarchie: **Fabrik → Runtime/Container → Maschine/Tool → Agent/Stage.** Der Dashboard-CODE-Eingang für Bülent und automatische Reparaturaufträge von Agent 21 benutzen denselben kontrollierten Coding-Unterbau; es wird keine zweite Coding-Orchestrierung aufgebaut.

Content: Strategie/Discovery → Research/Newsroom → Creative/Writing → plattformgerechter Plan → Media/Voice/Avatar je realer Fähigkeit → Source-/Media-Final-QM → Goldenes Tablett → Human Authority → bestehender Publisher.

Forschung und Weiterentwicklung: Scout → Research/Lizenz/Kostenprüfung → technischer Integrationsplan → isolierter Build → unabhängige Security/CI/QM → kontrollierte Freigabe → zentraler TOOL_INDEX und evidenzgebundenes Memory → erneute Scout-Recherche.

Ein `AGENTS_INDEX`-Eintrag ist keine produktive Freischaltung. Die separate stündliche Infrastruktur-Angebotsprüfung beweist nicht den vollständigen GitHub-Scout. Coding-Probeläufe beweisen nicht den vollständig schreibenden Programmierdispatcher. Fehlende Rückmeldungen/fehlende R2-Nachweise bedeuten **UNVERIFIED**, nicht PASS.
