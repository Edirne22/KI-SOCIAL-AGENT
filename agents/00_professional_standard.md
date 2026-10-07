# Agent 00 – Global Professional Standard

Diese Regel gilt fuer jeden Agenten und jede Redaktions-/QM-Rolle im Repository, unabhaengig von der Spezialdisziplin.

Arbeite auf Senior-/Premium-Niveau, entsprechend mindestens zehn Jahren professioneller Erfahrung als Qualitaetsmassstab. Behaupte niemals, selbst reale Berufsjahre oder persoenliche Erlebnisse zu besitzen.

Verbindlich sind `config/PROFESSIONAL_AGENT_STANDARD.md` und fuer Textarbeit `config/HUMAN_WRITING_PROTOCOL.md`. Domain-Regeln, Quellenregeln, Safety, Rechte und menschliche Freigabe bleiben vorrangig. Jeder Agent prueft seine eigene Ausgabe vor der Uebergabe; jeder QM bleibt unabhaengig und fail-closed.


## Verbindlicher Container-Lifecycle für ALLE Agenten

Diese Regel gilt für **jede** Rolle in `agents/` – Betriebsleitung, QM, Creative, Content, Research, Audio/Musik, Video, Download/Ingest, Social/YouTube-nahe Rollen, Integrations-/Maschinenrollen sowie Wartung/Recovery – sobald sie Containerarbeit auslöst, anfordert, prüft oder deren Verfügbarkeit bewertet.

- Containerarbeit niemals direkt mit „nicht erreichbar“ abbrechen: zuerst den zentralen Wake-/Warmup-Pfad verwenden bzw. dessen Evidenz verlangen.
- Cloudflare-Container-Vertrag: feste Instanz adressieren → `startAndWaitForPorts()` → benötigten Port bestätigen → Dienst- und Zielrevision/Health prüfen → Auftrag genau einmal übergeben.
- Nach Deploy, Destroy oder Restart ist Wake/Port-Readiness erneut Pflicht; `destroy()` allein ist kein Neustart-PASS.
- HTTP 200 allein ist kein Runtime-PASS, wenn Readiness oder erwartete Revision fehlen.
- Nicht-idempotente Jobs/Uploads/Render-Aufträge niemals blind wiederholen. Sichere Readiness-Probes dürfen begrenzt wiederholt werden.
- Rollen ohne Runtime-Berechtigung starten den Container nicht selbst, sondern übergeben an den zentralen Lifecycle-/Agent-11-Pfad und dürfen erst nach dessen Evidenz „unavailable“ melden.
- Reine R2-/Storage-Leseoperationen benötigen keinen Wake.

Verbindliche Detailquelle: `PROJECT_GUARDRAILS.md`, Abschnitt **Container-Aufwecken vor Arbeitsaufträgen** plus **Container-Lifecycle-Ergänzung 07.10.2026**. Diese Globalregel muss nicht in jeder einzelnen Rollen-Datei dupliziert werden; jede Rollenbeschreibung erbt sie über Agent 00.


## Einheitliche Fabriksprache – E22-FCL
Jeder Agent muss `docs/E22_FACTORY_CONTRACT_LANGUAGE.md` lesen und für **ausführbare** Agent↔Agent-, Agent↔Betriebsleitungs- und Agent↔Maschinen-Handoffs `E22-FCL-1.0` verwenden. Rollen dürfen ihre Fachsprache/Nutzersprache weiterhin verwenden, müssen sie vor Ausführung in E22-FCL normalisieren. Rohe Maschinensprachen werden nur von validierten Adaptern erzeugt. Unbekannte Vertragssemantik wird nicht geraten.
