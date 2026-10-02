# Agenten-Bibliothek

Diese Bibliothek bündelt Rollen der Edirne-22-Content-Fabrik und der entstehenden universellen KI-Werkstatt. Die verbindliche Abteilungsstruktur und Zuständigkeiten stehen in [AGENCY_ORG_AND_HANDOFF.md](../docs/AGENCY_ORG_AND_HANDOFF.md). Die Rollen sind projektspezifisch formuliert und dienen als Arbeitsanweisung für künftige Automatisierungen oder manuelle Aufträge.

Die Struktur ist methodisch inspiriert von [Agency Agents](https://github.com/msitarzewski/agency-agents); das Referenzprojekt steht unter der [MIT-Lizenz](https://github.com/msitarzewski/agency-agents/blob/main/LICENSE).

## Agentenübersicht

| Datei | Rolle | Aktivierung |
| --- | --- | --- |
| [01_content_creator.md](01_content_creator.md) | Entwickelt neue Content-Ideen und produktionsreife Entwürfe. | Bei neuen Themen, täglichen Ideen und konkreten Beitragsentwürfen. |
| [02_instagram_curator.md](02_instagram_curator.md) | Passt Inhalte für Reels, Carousels, Stories und Instagram-Captions an. | Wenn Instagram das Ziel ist oder ein Format gewählt werden muss. |
| [03_tiktok_strategist.md](03_tiktok_strategist.md) | Entwickelt kurze TikTok-Konzepte mit Hook, Szenen und Untertiteln. | Bei TikTok-Ideen, Kurzvideo-Tests und vertikalen Storys. |
| [04_social_media_strategist.md](04_social_media_strategist.md) | Plant Themen, Plattform-Mix und realistische Redaktionsschritte. | Bei Wochenplänen, Kampagnen und Priorisierungsfragen. |
| [05_research_synthesist.md](05_research_synthesist.md) | Prüft Quellen und bereitet Fakten verständlich auf. | Vor externen Tatsachenbehauptungen, Reise-, Sicherheits- oder Plattforminformationen. |
| [06_reddit_community_builder.md](06_reddit_community_builder.md) | Entwirft hilfreiche, regelkonforme Reddit-Beiträge und Antworten. | Bei Reddit-Recherche, Community-Gesprächen und Antwortentwürfen. |
| [07_video_optimization.md](07_video_optimization.md) | Erstellt Schnitt-, Untertitel- und Produktionsbriefe für Kurzvideos. | Bei Reel-, TikTok-, Video- oder Agnes-Asset-Briefings. |
| [08_paid_social_strategist.md](08_paid_social_strategist.md) | Entwirft vorsichtige Paid-Social-Kampagnen und Messpläne. | Nur bei ausdrücklich gewünschter, bezahlter Reichweite. |
| [09_quality_agent.md](09_quality_agent.md) | Prüft Workflow-Ergebnisse, Datenqualität und Sicherheitswarnungen. | Täglich nach den Analyse-Workflows oder manuell vor größeren Änderungen. |
| [10_follow_analysis_agent.md](10_follow_analysis_agent.md) | Erkennt aus freigegebenen öffentlichen Instagram-Profilen Formate, Themen und Hook-Muster. | Geplanter Analyse-Lauf oder Telegram: \`follow-analyse\`; kein Zugriff auf eine private Follow-Liste. |

| [11_system_restart_agent.md](11_system_restart_agent.md) | Prüft sichere Workflow-Zustände und erstellt einen Betriebsstatus. | Täglich als Bericht oder manuell mit ausdrücklicher Freigabe für erlaubte Fehler-Neustarts. |
| [12_music_agent.md](12_music_agent.md) | Wählt lizenzierte lokale Hintergrundmusik und mischt sie in freigegebene Reels und Stories. | Alle 15 Minuten bei `Musik: auto`; veröffentlicht selbst nie. |\n| [18_tour_ride_story_agent.md](18_tour_ride_story_agent.md) | Verwandelt BMW-/Calimoto-/Kurviger-/Motobit-Ridedaten plus Tourmedien in ein evidenzgebundenes Story-Paket. | Bei Motorradtouren, Ride-Screenshots/GPX sowie Foto-/Video-Tourmaterial; kein Publish. |\n| [19_ki_integrationsingenieur.md](19_ki_integrationsingenieur.md) | Plant geprüfte Adapter und isolierte Coding-Änderungen über bestehende Infrastruktur. | Nach Scout-/Research-/Security-Handoff und begrenztem Produktionsleiterauftrag; keine pauschalen Produktivrechte. |\n| [20_maschinen_scout.md](20_maschinen_scout.md) | Sucht weltweit nach neuen Maschinen, APIs, Skills und Speicher-/CPU-/GPU-Angeboten. | Nach echten Scanner- und Scheduler-E2E-Nachweisen; derzeit Rollenbeschreibung, Issue #327. |(18_tour_ride_story_agent.md) | Verwandelt BMW-/Calimoto-/Kurviger-/Motobit-Ridedaten plus Tourmedien in ein evidenzgebundenes Story-Paket. | Bei Motorradtouren, Ride-Screenshots/GPX sowie Foto-/Video-Tourmaterial; kein Publish. |

| [14_memory_curator.md](14_memory_curator.md) | Kuratiert nachvollziehbares Lernen aus Nutzerkorrekturen, Ergebnissen und Regressionen, nie Freigabe durch Memory. | Bestehender Lern-/Memory-Workflow nur gemäß tatsächlich nachgewiesenem Laufstatus. |\n| [15_finance_planner.md](15_finance_planner.md) | Kalkuliert und schlägt Entscheidungen vor, ohne autonom Geld auszugeben. | Nur analysieren; jede wirtschaftlich bindende Entscheidung bei Bülent. |\n| [17_instagram_engagement_agent.md](17_instagram_engagement_agent.md) | Bereitet Instagram-Kommentarentwürfe für echte menschliche Freigabe vor. | Nur wenn offizieller Zugangsweg aktiv; kein automatischer Versand. |\n\n## Aktivierungs-Logik

1. Ordne den Auftrag zuerst einem Hauptagenten zu. Aktiviere nur einen zweiten Agenten, wenn dessen Fachwissen wirklich nötig ist.
2. Bei neuen Beiträgen startet in der Regel der Content Creator. Danach übernimmt der Plattform-Spezialist oder Video-Optimization-Agent.
3. Der Research Synthesist wird vor allen aktuellen, externen oder sicherheitsrelevanten Behauptungen eingesetzt.
4. Der Social Media Strategist plant Reihenfolgen und Wochenziele; er ersetzt nicht die Erstellung einzelner Beiträge.
5. Der Paid Social Strategist erstellt ausschließlich Entwürfe. Er startet weder Anzeigen noch Ausgaben.
6. Der Reddit Community Builder erstellt nur Vorschläge. Beiträge, Kommentare und Nachrichten werden nie automatisch versendet.
7. Jeder Agent liest vor der Arbeit mindestens die passenden Informationen aus `memory/`, `content/` und den Regeln unter `rules/`.
8. Jeder Output ist ein Entwurf. Veröffentlichung, externe Kommunikation, Budgeteinsatz, Buchungen und Kontoveränderungen brauchen immer Bülents ausdrückliche Freigabe.

**Kennungen:** Historisch heißt der Facebook-Engagement-Agent in älteren Unterlagen teils „18“. Die aktuelle Agentenbibliothek verwendet Datei-ID 18 für den Tour-Agenten. Bis zur formal getesteten Migration sind DATEINAMEN/rollenbasierte IDs verbindlich; alte numerische IDs allein dürfen niemals eine Aktion auslösen.\n\nFür neue Maschinen/API-Integrationen gilt: Maschinen-Scout (Issue #327) → Research/Quellen-/Lizenz-/Kostenprüfung → Integrationsingenieur (Architektur und isolierter Build) → unabhängige Quality/Security-/CI-Prüfung → Produktionsleiter und erforderliche menschliche Freigabe. Die Rollenbeschreibung ist noch kein aktivierter automatischer Coding-Workflow.

## Empfohlene Reihenfolgen

- **Tägliche Idee:** Content Creator → optional Research Synthesist → Instagram Curator oder TikTok Strategist.
- **Wochenplanung:** Social Media Strategist → Content Creator → jeweiliger Plattform-Agent.
- **Video:** Content Creator oder TikTok Strategist → Video Optimization → menschliche Freigabe.
- **Recherche-Post:** Research Synthesist → Content Creator → Plattform-Agent.
- **Follow-Analyse:** Follow-Analyse-Agent → Research Synthesist → Content Creator; Muster nur als Inspiration verwenden.
- **Bezahlte Kampagne:** Paid Social Strategist → menschliche Freigabe → manuelle Einrichtung.
- **Betrieb:** Qualitäts-Agent → System-Neustart-Agent → nur bei ausdrücklich aktiviertem Neustart erlaubte Analyse-Workflows.
- **Video mit Musik:** Video Optimization → menschliche Freigabe → Musik-Agent → Publisher.

## Technischer Status

Die Rollen bleiben Arbeitsgrundlage. Der Qualitäts-Agent, der Follow-Analyse-Agent und der System-Neustart-Agent haben zusätzlich klar begrenzte GitHub-Workflows. Die bloße Aufnahme des Integrationsingenieurs aktiviert keine automatische Coding-Ausführung. Die Aufnahme in diese Tabelle bedeutet nicht, dass der Agent technisch aktiviert ist. Viele Rollen besitzen nur einen Prompt-/Arbeitsvertrag oder Teilmodule. Welche ausführenden Pfade aktuell LIVE, getestet, deaktiviert oder nur geplant sind, muss anhand konkreter Workflows und Läufe geprüft werden; siehe Organisationsvertrag. Alle übrigen Rollen werden nicht automatisch durch `router.py` oder `llm_client.py` ausgeführt. Jede spätere Orchestrierung muss die Aktivierungs-Logik und die menschlichen Freigaben respektieren.
