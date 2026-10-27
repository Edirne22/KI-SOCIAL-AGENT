// Only a clock: no content, approvals, R2, containers or public dispatch endpoint.
export const REPO = 'Edirne22/KI-SOCIAL-AGENT';
export const CRON = '2-57/5 * * * *';
const API = `https://api.github.com/repos/${REPO}/actions/workflows/`;
const ACTIVE = new Set(['queued', 'in_progress', 'waiting', 'pending', 'requested']);
export function due(time) {
  if (!Number.isFinite(time)) return [];
  const minute = new Date(time).getUTCMinutes();
  if (minute % 5 !== 2) return [];
  const workflows = ['telegram-receive.yml'];
  if (minute % 15 === 2) workflows.push('facebook-publish.yml');
  if (minute % 15 === 7) workflows.push('instagram-publish.yml');
  return workflows;
}
export async function tick(event, env, request = fetch, now = Date.now()) {
  if (env.SCHEDULER_ENABLED !== 'true') return [{status: 'disabled'}];
  if (!env.GITHUB_DISPATCH_TOKEN) throw new Error('dispatch_credential_missing');
  if (event.cron !== CRON || !Number.isFinite(event.scheduledTime) ||
      now - event.scheduledTime > 300000 || event.scheduledTime > now + 60000) {
    return [{status: 'stale_or_invalid_tick'}];
  }
  const headers = {Authorization: `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
    Accept: 'application/vnd.github+json', 'User-Agent': 'edirne22-scheduler',
    'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'};
  const results = [];
  for (const workflow of due(event.scheduledTime)) {
    try {
      // Fixed URLs and no redirects prevent credentials reaching another host.
      const response = await request(`${API}${workflow}/runs?branch=main&per_page=5`,
        {headers, redirect: 'error', signal: AbortSignal.timeout(15000)});
      if (!response.ok) { results.push({workflow, status: 'lookup_failed', code: response.status}); continue; }
      const body = await response.json();
      if (!Array.isArray(body.workflow_runs)) { results.push({workflow, status: 'invalid_response'}); continue; }
      const runs = body.workflow_runs;
      if (runs.some(run => ACTIVE.has(run.status))) {
        results.push({workflow, status: 'active'}); continue;
      }
      // Best-effort duplicate suppression across restarts; publication claims in
      // GitHub remain authoritative. This is not an exactly-once delivery claim.
      if (runs.some(run => Date.parse(run.created_at) >= event.scheduledTime)) {
        results.push({workflow, status: 'already_started'}); continue;
      }
      const dispatched = await request(`${API}${workflow}/dispatches`, {
        method: 'POST', headers, redirect: 'error', signal: AbortSignal.timeout(15000),
        body: JSON.stringify({ref: 'main'})
      });
      // No POST retry on timeout/ambiguous response: next scheduled tick recovers.
      results.push({workflow, status: dispatched.status === 204 ? 'accepted' : 'dispatch_failed', code: dispatched.status});
    } catch {
      results.push({workflow, status: 'request_failed'});
    }
  }
  return results;
}
export default {
  async scheduled(event, env) {
    const results = await tick(event, env);
    console.log(JSON.stringify(results)); // fixed status fields only; no response bodies
    if (results.some(r => ['lookup_failed','invalid_response','dispatch_failed','request_failed'].includes(r.status))) {
      throw new Error('scheduler_tick_incomplete');
    }
  },
  fetch() { return new Response('Not found', {status: 404}); }
};
