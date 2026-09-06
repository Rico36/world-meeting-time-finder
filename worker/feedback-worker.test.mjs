// Exercises every abuse control in feedback-worker.js with a mocked network.
// Run:  node worker/feedback-worker.test.mjs
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const worker = (await import(pathToFileURL(path.resolve('worker/feedback-worker.js')).href)).default;

const ENV = { ALLOWED_ORIGIN: 'https://findcommonhours.com', FEEDBACK_REPO: 'Rico36/findcommonhours-feedback',
              TURNSTILE_SECRET: 'ts-secret', GITHUB_TOKEN: 'gh-token' };
let calls = [];
globalThis.fetch = async (url, init) => {
  calls.push({ url, init });
  if (url.includes('turnstile')) return new Response(JSON.stringify({ success: true }), { status: 200 });
  if (url.includes('api.github.com')) return new Response('{}', { status: 201 });
  throw new Error('unexpected fetch ' + url);
};

const good = { message: 'Typed New Mexico, expected Albuquerque', cities: 'New York, London',
               contact: '', website: '', elapsed: 8000, page: '/', language: 'en', token: 'tok-1' };
function req(body, { method = 'POST', origin = ENV.ALLOWED_ORIGIN, ip = '203.0.113.9' } = {}) {
  return new Request('https://feedback.example/', { method,
    headers: { 'Origin': origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': ip },
    body: method === 'POST' ? JSON.stringify(body) : undefined });
}
async function run(body, opts, env = ENV) { calls = []; const r = await worker.fetch(req(body, opts), env); return { status: r.status, json: await r.json().catch(() => null), gh: calls.some(c => c.url.includes('api.github.com')), ts: calls.some(c => c.url.includes('turnstile')) }; }

let failed = 0;
async function t(name, fn) { try { await fn(); console.log('  ok   ' + name); } catch (e) { failed++; console.log('  FAIL ' + name + ' -> ' + e.message); } }
const eq = (a, b, what) => { if (a !== b) throw new Error(`${what}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); };

await t('OPTIONS preflight returns 204', async () => { const r = await worker.fetch(req(null, { method: 'OPTIONS' }), ENV); eq(r.status, 204, 'status'); });
await t('GET is rejected', async () => { const r = await run(null, { method: 'GET' }); eq(r.status, 405, 'status'); });
await t('foreign origin is rejected before anything else', async () => { const r = await run(good, { origin: 'https://evil.example' }); eq(r.status, 403, 'status'); eq(r.ts, false, 'no turnstile call'); });
await t('oversized body is rejected', async () => { const r = await run({ ...good, message: 'x'.repeat(9000) }); eq(r.status, 413, 'status'); });
await t('empty message is rejected', async () => { const r = await run({ ...good, message: '   ' }); eq(r.status, 400, 'status'); });
await t('malformed contact is rejected', async () => { const r = await run({ ...good, contact: 'not-an-email' }); eq(r.status, 400, 'status'); });
await t('honeypot: fake success, nothing filed, no turnstile call', async () => { const r = await run({ ...good, website: 'http://spam' }); eq(r.status, 200, 'status'); eq(r.json.ok, true, 'ok'); eq(r.gh, false, 'github'); eq(r.ts, false, 'turnstile'); });
await t('timing: submitted in under 3s is silently dropped', async () => { const r = await run({ ...good, elapsed: 900 }); eq(r.status, 200, 'status'); eq(r.gh, false, 'github'); });
await t('link density: three URLs is silently dropped', async () => { const r = await run({ ...good, message: 'see http://a.x http://b.x www.c.x' }); eq(r.status, 200, 'status'); eq(r.gh, false, 'github'); });
await t('two URLs are allowed through', async () => { const r = await run({ ...good, message: 'see http://a.x and http://b.x' }); eq(r.status, 200, 'status'); eq(r.gh, true, 'github'); });
await t('missing token is rejected before turnstile is called', async () => { const r = await run({ ...good, token: '' }); eq(r.status, 400, 'status'); eq(r.ts, false, 'turnstile'); });
await t('turnstile failure is rejected and nothing is filed', async () => {
  const orig = globalThis.fetch;
  globalThis.fetch = async (url, init) => url.includes('turnstile') ? new Response(JSON.stringify({ success: false }), { status: 200 }) : orig(url, init);
  const r = await run(good); globalThis.fetch = orig; eq(r.status, 400, 'status'); eq(r.gh, false, 'github');
});
await t('happy path: verifies token, files a labelled issue in the private repo', async () => {
  const r = await run(good); eq(r.status, 200, 'status'); eq(r.json.ok, true, 'ok');
  const ts = calls.find(c => c.url.includes('turnstile')); const tsBody = JSON.parse(ts.init.body);
  eq(tsBody.secret, 'ts-secret', 'secret'); eq(tsBody.response, 'tok-1', 'token'); eq(tsBody.remoteip, '203.0.113.9', 'ip');
  const gh = calls.find(c => c.url.includes('api.github.com'));
  eq(gh.url, 'https://api.github.com/repos/Rico36/findcommonhours-feedback/issues', 'repo url');
  eq(gh.init.headers['Authorization'], 'Bearer gh-token', 'auth');
  const issue = JSON.parse(gh.init.body);
  eq(issue.labels[0], 'user-feedback', 'label');
  if (!issue.body.includes('Typed New Mexico')) throw new Error('message missing from body');
  if (!issue.body.includes('**Cities added:** New York, London')) throw new Error('cities missing from body');
  if (!issue.body.includes('**Contact:** not given')) throw new Error('contact line missing');
});
await t('angle brackets are stripped so markdown cannot be injected', async () => {
  await run({ ...good, message: 'hello <script>alert(1)</script> world' });
  const issue = JSON.parse(calls.find(c => c.url.includes('api.github.com')).init.body);
  if (issue.body.includes('<')) throw new Error('angle bracket survived');
});
await t('github failure surfaces as 502, not a fake success', async () => {
  const orig = globalThis.fetch;
  globalThis.fetch = async (url, init) => url.includes('api.github.com') ? new Response('{}', { status: 500 }) : orig(url, init);
  const r = await run(good); globalThis.fetch = orig; eq(r.status, 502, 'status');
});
await t('rate limit: sixth submission from one IP is refused when KV is bound', async () => {
  const store = new Map();
  const kv = { get: async k => store.get(k) ?? null, put: async (k, v) => { store.set(k, v); } };
  const env = { ...ENV, RATE_KV: kv };
  for (let i = 0; i < 5; i++) { const r = await run(good, {}, env); eq(r.status, 200, `submission ${i + 1}`); }
  const r = await run(good, {}, env); eq(r.status, 429, 'sixth');
  const other = await run(good, { ip: '198.51.100.7' }, env); eq(other.status, 200, 'different ip unaffected');
});
await t('CORS header echoes only the allowed origin', async () => {
  const r = await worker.fetch(req(good), ENV); eq(r.headers.get('Access-Control-Allow-Origin'), ENV.ALLOWED_ORIGIN, 'allowed');
  const bad = await worker.fetch(req(good, { origin: 'https://evil.example' }), ENV); eq(bad.headers.get('Access-Control-Allow-Origin'), 'null', 'foreign');
});

console.log(failed ? `\n${failed} test(s) FAILED` : '\nAll worker tests passed.');
process.exit(failed ? 1 : 0);
