# OPENCHATCUT DEPLOY #67 – AUDIT UND DIAGNOSEBERICHT

**Datum:** 01.10.2026
**Repository:** `Edirne22/KI-SOCIAL-AGENT`
**Run #67:** `36847153610` (https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/36847153610)
**PR:** #271 (`fix/openchatcut-cloudflare-lifecycle-readiness`)
**Commit SHA:** `3324349b8f0c91218cdb4b2dbaab1efea1824ebf`

---

## 1. Ergebnisse von Run #67

- **Contract:** SUCCESS
- **Deploy:** SUCCESS (Wrangler Worker-Upload ca. 10:11:53 UTC, Containeraktualisierung ca. 10:15:32 UTC)
- **Live-Acceptance:** FAILURE

---

## 2. Detaillierter Ablauf & Telemetrie (ca. 10:16–10:21 UTC)

1. **Post-Deploy MCP-Readiness Probes:**
   - Versuch 1: HTTP 200
   - Versuch 2: HTTP 500
   - Versuch 3/4: HTTP 200
   - Versuch 5: HTTP 500
   - Versuch 6/7/8: HTTP 200
   - 3 aufeinanderfolgende gültige MCP-Initialize-Antworten um 10:17:02 UTC bestätigt.

2. **Live-Acceptance gegen Deployed Version:**
   - 10:17:48 UTC: Geschützte Health (`/_factory/health`) -> HTTP 200 OK.
   - 10:17:48 UTC: Raw MCP Initialize Probe -> HTTP 200 OK.
   - 10:17:50 UTC: MCP Client Connect via `StreamableHTTPClientTransport` erfolgreich, `mcp-session-id` erhalten.
   - 10:17:51 UTC: Erster Tool-Aufruf `openchatcut_status` schlägt fehl mit:
     ```json
     {"code": -32001, "message": "MCP session not found or expired"}
     ```

---

## 3. Exakte Code-Lokalisierung der Fehlerquelle

### A. Cloudflare Worker Module (`infra/openchatcut-cloudflare/src/index.ts`)
- Die Fehlermeldung `MCP session not found or expired` existiert in unserem Worker **nicht**.
- `workerBootId` und `workerStartedAt` werden in `workerIdentity()` als modulweite Variablen des Cloudflare Worker Isolates erzeugt.
- **Beweis:** `workerBootId` belegt nur die Lebensdauer des V8 Worker Isolates, **nicht** den Start- oder Neustartzeitpunkt des OpenChatCut Containerprozesses. Ein Wechsel der Boot-ID darf nicht als Container-Crash interpretiert werden.

### B. Upstream OpenChatCut (`0xsline/OpenChatCut@d1af1ade45521e8ed9a5be09e3acad823f269453`)
- **Datei:** `server/external-agent/mcp.ts`
- **Funktion:** `handleMcpRequest`
- **Verhalten:**
  1. `pruneMcpSessions(now)` wird aufgerufen.
  2. `sessionId = request.headers.get("mcp-session-id")`.
  3. `const session = sessions.get(sessionId)` wird in der Prozess-RAM-Speicherstruktur `const sessions = new Map<string, McpSession>()` gesucht.
  4. Wenn der Eintrag fehlt, gibt OpenChatCut HTTP 404 / JSON-RPC Code `-32001` mit der Meldung `"MCP session not found or expired"` zurück.
- **Session-Lifecycle:**
  - Registrierung erfolgt in `onsessioninitialized`.
  - Löschung erfolgt bei `transport.onclose` oder im Inaktivitäts-Pruning (`pruneMcpSessions`).

---

## 4. Schlussfolgerungen & Verbindliche Vorgaben

1. **Keine voreilige Neustart-Behauptung:**
   Das Fehlen der Session in der In-Memory-`Map` beweist für sich genommen noch keinen Container-Crash. Es kommen Prozess-Restart, Transport-Close oder Routing auf eine andere Containerinstanz in Betracht.
2. **Änderungsstopp & Diagnose-Fokus:**
   Keine weiteren Code-Änderungen an der Runtime, keine Instanzvergrößerungen (z. B. auf 8 GiB RAM) und keine blinden Retry-Schleifen.
3. **Nächste harte Diagnose-Anforderung:**
   Erfassen und Korrelieren der Cloudflare-Lifecycle-Logs (`onStart`, `onStop`, `onError`, Exit-Codes, Rollout-/Proxy-Fehler) im erweiterten Zeitfenster **10:16–10:21 UTC** mit den Upstream MCP Session-Events.
