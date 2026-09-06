/**
 * Anonymous IP geolocation for findcommonhours.com's "detect my city" feature.
 *
 * The browser can only report a time ZONE (Intl.DateTimeFormat), which IANA
 * names after one representative city per zone - "America/New_York" covers
 * the whole US Eastern zone, not literally New York. Cloudflare resolves
 * every request's approximate location at the edge and exposes it as
 * `request.cf`, at no extra cost. This Worker echoes just the fields the
 * client needs as JSON.
 *
 * Nothing is stored, logged, or persisted anywhere - the response is
 * computed fresh per request (Cache-Control: no-store) and this Worker
 * writes nothing to disk or to any database.
 *
 * GET only, CORS-locked to the site's own origin, so this cannot be scraped
 * as a free public geolocation API. No secrets: nothing to configure beyond
 * ALLOWED_ORIGIN in wrangler.geo.toml.
 */

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': origin === env.ALLOWED_ORIGIN ? env.ALLOWED_ORIGIN : 'null',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Max-Age': '86400',
      'Vary': 'Origin',
    };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (request.method !== 'GET') return json({ error: 'method' }, 405, cors);
    if (origin !== env.ALLOWED_ORIGIN) return json({ error: 'origin' }, 403, cors);

    const cf = request.cf || {};
    return json({
      city: cf.city || null,
      region: cf.region || null,
      countryCode: cf.country || null,
      timezone: cf.timezone || null,
      latitude: typeof cf.latitude === 'string' ? cf.latitude : null,
      longitude: typeof cf.longitude === 'string' ? cf.longitude : null,
    }, 200, cors);
  },
};

function json(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...headers },
  });
}
