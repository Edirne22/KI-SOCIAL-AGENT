# Cloud-only AI crew: binding architecture

**Laptop is not involved**. The previous local OmniRoute connection was a provider-routing prototype, not cloud infrastructure. No hosted job must depend on localhost:20128.

1. GitHub Actions runs short, explicitly started cloud jobs with existing configured NVIDIA/Groq/Gemini/OpenRouter API secrets. PR checks run only offline mocked tests.
2. Independent analysis is advisory only. Record API errors/timeouts and model identity; no invented consensus.
3. GitHub uploads the resulting bounded sanitized review artifact. Optional private Cloudflare R2 archive path: ai-diagnostics/openchatcut/run-<RUN_ID>/multi-model-review.json.
4. R2 is storage, not computation or a model host. Runner executes tools; secrets never go into R2 or model prompts.
5. Later isolated coding lane: pin and test OpenCode CLI and compatible provider against the real available NVIDIA catalog. GitHub task -> isolated job -> proposed patch -> offline validation -> PR -> Guardian CI -> user merge decision. Do not grant general write scopes, bypass permissions or auto-merge. Jules still coding-only.
6. Paid/slow model use requires model-level availability and timeout probes. Kimi timed out and Groq currently returned HTTP 404. No API key or free-model access is assumed.

OpenChatCut evidence: first comparison raw 3/6, SDK 1/6, occasional Cloudflare port 5199 error. New diagnostic run #36853426401: raw 0/6, SDK 0/6, idle 0/1, all timed out. This proves no current stable MCP path, not a container restart or SDK root cause. Cloudflare lifecycle logs remain essential.

Cloudflare runtime must not be changed blindly; no auto-deploy from this diagnostic bridge. Keep model-generated code and responses untrusted until independently verified.

Official OpenCode CLI automation reference: https://opencode.ai/docs/cli/
Official OpenCode provider configuration: https://opencode.ai/docs/providers/