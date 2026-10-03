# Telegram private album – fixed acceptance matrix

Scope: authorized owner's Telegram /privat album into **private** R2 only. No social publication, no real personal media in CI.

| Criterion | Proof | Current status |
|---|---|---|
| Captioned first + following album photos/videos | Synthetic multi-item integration | PASS in earlier CI |
| No caption before owner authorization | Quarantine, no Vision/social fallback | Partially tested; router E2E pending |
| Out-of-order uncaptioned item before caption | Durable bounded quarantine and automatic recovery | OPEN: current code drops first item |
| Restart, retry, duplicate update | Persistent idempotent manifest, same asset once | Partial synthetic retry PASS; interrupted R2 writes pending |
| Parallel items, CAS conflicts | Retry without overwriting or losing assets | OPEN |
| Wrong chat, unsupported MIME, invalid group, oversize | Fail closed and do not publish | Partial; complete negative suite pending |
| Full owner intake → R2 manifest → private acknowledgement | Synthetic E2E, production-safe smoke without personal files | OPEN |
| Existing Telegram commands and routing | Existing full CI suite | Prior checks green; rerun final HEAD |

Do not merge or claim completion until all in-scope rows PASS on the same final HEAD. No live personal uploads without owner participation; no social publication.
