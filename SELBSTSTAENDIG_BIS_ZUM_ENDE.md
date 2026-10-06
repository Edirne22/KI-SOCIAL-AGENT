# SELBSTSTÄNDIG BIS ZUM ENDE – BLOCKRUN-BETRIEBSREGEL

> **STATUS: VERBINDLICHE OPERATIVE ERGÄNZUNG**
>
> Zweck: Ein klar definiertes Ziel wird selbstständig bis zum nachweisbaren Ergebnis abgearbeitet. Statusmeldungen, laufende Actions, PRs, Builds oder Deployments sind keine Stoppsignale.
>
> Diese Datei ergänzt `PROJECT_GUARDRAILS.md`, `AGENTS.md` und `CLAUDE.md`. Bei Widerspruch gelten die strengeren Sicherheits-/Projekt-Guardrails.

## 1. Grundsatz

**Ziel bekannt → arbeiten → prüfen → Fehler analysieren → reparieren → testen → mergen/deployen, soweit freigegeben → wieder in Betrieb nehmen → E2E prüfen → dokumentieren → erst dann fertig.**

Ein Auftrag bleibt aktiv, bis:

1. das definierte Ziel vollständig erreicht und mit geeigneten Belegen/E2E nachgewiesen ist, oder
2. eine echte Entscheidung oder Handlung von Bülent zwingend erforderlich ist.

Ein Zwischenstand beendet den Auftrag niemals.

## 2. Status ist Information, kein Stoppsignal

Fragen wie „Status?“, „Wie weit bist du?“ oder „Zwischenstand?“ bedeuten ausschließlich: aktuellen Stand mitteilen.

Danach wird mit dem nächsten technisch möglichen Schritt fortgefahren. Es ist **keine** neue Aufforderung wie „weiter“, „mach weiter“ oder „du darfst“ erforderlich.

Unzulässiges Muster:

```text
Workflow gestartet
→ Status gemeldet
→ Chat/Agent wartet auf Bülent
→ Bülent muss nachfragen
→ erst dann geht es weiter
```

Zielmuster:

```text
Arbeit
→ Status auf Nachfrage
→ Arbeit läuft weiter
→ Ergebnis eines Laufs auswerten
→ nächster Schritt
→ E2E
→ Abschluss
```

## 3. Keine passive Wartezeit

Ein laufender Workflow, PR-Check, Build, Deployment oder externer Test ist **kein Arbeitspausen-Grund**.

Während ein abhängiger Prozess läuft:

- unabhängige nächste Schritte vorbereiten oder ausführen,
- Logs/Code/Tests für folgende Stufen prüfen,
- E2E-/Regressionstests vorbereiten,
- Dokumentation und sichere Diagnosepfade aktualisieren,
- bekannte offene Punkte untersuchen,
- bei sinnvoller Trennbarkeit parallele Arbeitspakete nutzen.

**Parallelisieren, wo unabhängig; synchronisieren, wo abhängig.**

Es darf nicht auf einem noch unbekannten Testergebnis blind weitergebaut werden, wenn dadurch widersprüchliche Änderungen, Datenverlust oder unsichere Deployments entstehen könnten.

## 4. Nach Action/PR/Build automatisch weiterdenken

Nach Abschluss eines technischen Laufs gilt:

### SUCCESS
Ergebnis verifizieren → Beleg sichern → unmittelbar nächsten notwendigen Schritt ausführen.

### FAILURE
Fehler offen melden → Guardrails erneut lesen → Logs und betroffene Dateien untersuchen → Root Cause bestimmen → Fix → Regressionstest → neuer Lauf.

### Unerwarteter Zustand
Nicht raten und nicht passiv warten. Tatsächlichen HEAD, Branch, Workflow, Runtimezustand und relevante Dateien erneut prüfen.

Ein grüner Workflow allein bedeutet nicht automatisch „Gesamtziel erreicht“.

## 5. Produktivität statt Beschäftigung

Ziel ist nicht, möglichst viele Aktionen oder Statusmeldungen zu erzeugen. Ziel sind **funktionierende Ergebnisse und fertige Produkte**.

Priorität:

```text
Ergebnis
→ Funktionsnachweis
→ Stabilität
→ Dokumentation
→ erst danach kosmetische/optionale Arbeit
```

Keine unnötigen Änderungen nur zur Vermeidung von Leerlauf.

## 6. Fehler- und Reparaturkette

Bei einer Störung:

```text
ERKENNEN
→ BELEG/LOG
→ ROOT-CAUSE
→ FIX
→ REGRESSION
→ CI/TEST
→ DEPLOY
→ WIEDERANLAUF
→ HEALTHCHECK
→ E2E
→ DOKUMENTATION
→ BETRIEBSBEREIT
```

Eine Reparatur gilt nicht als abgeschlossen, nur weil Code geändert oder CI grün ist. Die betroffene Maschine/Dienststrecke muss – soweit der Auftrag Runtime betrifft – kontrolliert wieder in Betrieb genommen und verifiziert werden.

## 7. Agent 11 / Agent 21

Wo diese Agenten im jeweiligen Block vorgesehen und technisch verdrahtet sind:

- **Agent 11:** Wächter/Beobachter. Erkennt relevante Störungen/Zustände, sammelt sichere Diagnoseinformationen und stößt den vorgesehenen Eskalationspfad an.
- **Agent 21:** Diagnostik/Root-Cause und, innerhalb seiner festgelegten Schreib- und Sicherheitsgrenzen, Reparaturunterstützung.

Agent 21 darf seine bestehenden Schutzgrenzen nicht umgehen. Geschützte Dateien, Secrets, Workflows oder andere in den Guardrails gesperrte Bereiche werden nicht eigenmächtig freigegeben.

Nach einer Reparatur muss der vorgesehene Wiederanlauf-/Verifikationspfad die Anlage zurück in einen belegten betriebsbereiten Zustand bringen.

## 8. Ehrlichkeit über fortlaufende Arbeit

Es darf niemals behauptet werden „ich arbeite im Hintergrund weiter“, wenn kein realer Mechanismus weiterläuft.

Fortlaufende Arbeit über einen einzelnen Chat-Turn hinaus benötigt einen tatsächlichen Mechanismus, z. B.:

- GitHub Action/Workflow,
- Agent-/Runtime-Trigger,
- Automation,
- andere im Projekt tatsächlich implementierte Ausführung.

Wenn kein solcher Mechanismus existiert und der nächste Schritt nicht im aktuellen Arbeitszug ausgeführt werden kann, muss das offen benannt werden.

## 9. Stopbedingungen

Vor dem Ziel wird nur gestoppt, wenn mindestens eine dieser Bedingungen erfüllt ist:

- zwingende Entscheidung von Bülent,
- zusätzliche Kosten außerhalb bestehender Freigaben,
- Secret/Berechtigung fehlt und kann nicht sicher selbst hergestellt werden,
- Sicherheits-/Guardrail-Grenze verbietet den nächsten Schritt,
- irreversible/riskante Aktion liegt außerhalb der Vollmacht,
- technische Plattformgrenze verhindert die weitere Ausführung.

Dann muss klar dokumentiert werden:

1. wo die Kette steht,
2. was bereits nachweislich funktioniert,
3. der konkrete Blocker,
4. welche **eine konkrete Aktion/Entscheidung** von Bülent benötigt wird,
5. wie es danach weitergeht.

## 10. Standard-Aufruf

Für neue Arbeiten kann Bülent kurz beauftragen:

```text
/BLOCKRUN
Ziel: <konkretes Ziel>

Arbeite nach SELBSTSTAENDIG_BIS_ZUM_ENDE.md.
Zieh den Auftrag bis zum nachweisbaren E2E-Ergebnis durch.
Statusmeldungen sind keine Stoppsignale.
Nutze Wartezeiten für sichere unabhängige Arbeit.
Stoppe nur bei Zielerreichung oder echtem Bülent-Blocker.
```

Die bestehenden Projekt-Guardrails, Kostenregeln, Privacy-Regeln, Merge-/Deployment-Grenzen und Veröffentlichungsfreigaben bleiben vollständig wirksam.

## 11. Definition „Fertig“

**Fertig** bedeutet nicht „Code geschrieben“, „PR erstellt“ oder „Action grün“.

Fertig bedeutet – soweit für den Auftrag relevant:

- gewünschte Funktion umgesetzt,
- Regression/CI erfolgreich,
- notwendige Runtime/Deployment-Stufe erfolgreich,
- betroffene Anlage wieder betriebsbereit,
- E2E-Funktionsweg nachgewiesen,
- keine bekannten Blocker im vereinbarten Scope,
- relevante Änderungen/Ergebnisse dokumentiert,
- Belege (Commit/PR/Run/Runtime) vorhanden.

**Leitsatz: Status informieren. Arbeit fortsetzen. Produkt fertigstellen. Ergebnis beweisen.**
