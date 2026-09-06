// Exercises geo-worker.js. Run:  node worker/geo-worker.test.mjs
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const worker = (await import(pathToFileURL(path.resolve('worker/geo-worker.js')).href)).default;
const ENV = { ALLOWED_ORIGIN: 'https://findcommonhours.com' };

function req({ method = 'GET', origin = ENV.ALLOWED_ORIGIN, cf = undefined } = {}) {
  return { method, headers: { get: (name) => (name === 'Origin' ? origin : null) }, cf };
}

let failed = 0;
async function t(name, fn) { try { await fn(); console.log('  ok   ' + name); } catch (e) { failed++; console.log('  FAIL ' + name + ' -> ' + e.message); } }
const eq = (a, b, what) => { if (a !== b) throw new Error(`${what}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); };

const FULL_CF = { city: 'Alpharetta', region: 'Georgia', country: 'US', timezone: 'America/New_York', latitude: '34.07538', longitude: '-84.29409' };

await t('OPTIONS preflight returns 204 with CORS for the allowed origin', async () => {
  const r = await worker.fetch(req({ method: 'OPTIONS' }), ENV);
  eq(r.status, 204, 'status');
  eq(r.headers.get('Access-Control-Allow-Origin'), ENV.ALLOWED_ORIGIN, 'ACAO');
});

await t('POST is rejected', async () => {
  const r = await worker.fetch(req({ method: 'POST' }), ENV);
  eq(r.status, 405, 'status');
});

await t('foreign origin is rejected, CORS echoes null', async () => {
  const r = await worker.fetch(req({ origin: 'https://evil.example' }), ENV);
  eq(r.status, 403, 'status');
  eq(r.headers.get('Access-Control-Allow-Origin'), 'null', 'ACAO');
});

await t('full cf data is echoed with the right shape', async () => {
  const r = await worker.fetch(req({ cf: FULL_CF }), ENV);
  eq(r.status, 200, 'status');
  eq(r.headers.get('Cache-Control'), 'no-store', 'cache-control');
  eq(r.headers.get('Access-Control-Allow-Origin'), ENV.ALLOWED_ORIGIN, 'ACAO');
  const body = await r.json();
  eq(body.city, 'Alpharetta', 'city');
  eq(body.region, 'Georgia', 'region');
  eq(body.countryCode, 'US', 'countryCode');
  eq(body.timezone, 'America/New_York', 'timezone');
  eq(body.latitude, '34.07538', 'latitude');
  eq(body.longitude, '-84.29409', 'longitude');
});

await t('missing cf (no edge geo data) returns nulls, not an error', async () => {
  const r = await worker.fetch(req({ cf: undefined }), ENV);
  eq(r.status, 200, 'status');
  const body = await r.json();
  eq(body.city, null, 'city'); eq(body.region, null, 'region');
  eq(body.countryCode, null, 'countryCode'); eq(body.timezone, null, 'timezone');
});

await t('partial cf (city known, coordinates withheld) does not throw', async () => {
  const r = await worker.fetch(req({ cf: { city: 'Springfield', country: 'US', timezone: 'America/Chicago' } }), ENV);
  eq(r.status, 200, 'status');
  const body = await r.json();
  eq(body.city, 'Springfield', 'city'); eq(body.region, null, 'region'); eq(body.latitude, null, 'latitude');
});

await t('nothing is written anywhere - response depends only on the single request', async () => {
  await worker.fetch(req({ cf: FULL_CF }), ENV);
  const r2 = await worker.fetch(req({ cf: { city: 'Denver', country: 'US', timezone: 'America/Denver' } }), ENV);
  const body = await r2.json();
  eq(body.city, 'Denver', 'city stays request-scoped, no leaked state between calls');
});

console.log(failed ? `\n${failed} test(s) FAILED` : '\nAll geo worker tests passed.');
process.exit(failed ? 1 : 0);
