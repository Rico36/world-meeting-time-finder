/**
 * Feedback endpoint for findcommonhours.com — a Cloudflare Worker.
 *
 * Accepts a JSON POST from the site's feedback dialog and files it as an issue
 * in a PRIVATE GitHub repository, so user submissions never become public.
 *
 * Abuse controls, in the order they run (cheapest first):
 *   1. Origin check          — only the site may call this
 *   2. Size and shape checks — bounded fields, valid JSON
 *   3. Honeypot              — a hidden field humans never fill in
 *   4. Timing                — forms submitted within 3 s of opening are bots
 *   5. Link density          — more than two URLs in a short message is spam
 *   6. Rate limit (optional) — per-IP cap, if a KV namespace is bound
 *   7. Cloudflare Turnstile  — server-side token verification; tokens are single-use
 *
 * Secrets (set with `wrangler secret put NAME`):  TURNSTILE_SECRET, GITHUB_TOKEN
 * Vars    (in wrangler.toml):                     ALLOWED_ORIGIN, FEEDBACK_REPO
 * Optional binding:                               RATE_KV (KV namespace)
 */

const LIMITS = { message: 2000, cities: 300, contact: 200 };
const RATE = { max: 5, windowSeconds: 3600 };   // per IP, if RATE_KV is bound
const MIN_ELAPSED_MS = 3000;

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const cors = corsHeaders(origin, env.ALLOWED_ORIGIN);

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (request.method !== 'POST') return json({ error: 'method' }, 405, cors);
    if (origin !== env.ALLOWED_ORIGIN) return json({ error: 'origin' }, 403, cors);

    // 2. shape
    let body;
    try {
      const raw = await request.text();
      if (raw.length > 8000) return json({ error: 'too large' }, 413, cors);
      body = JSON.parse(raw);
    } catch { return json({ error: 'bad json' }, 400, cors); }

    const message = clean(body.message, LIMITS.message);
    const cities  = clean(body.cities,  LIMITS.cities);
    const contact = clean(body.contact, LIMITS.contact);
    const token   = typeof body.token === 'string' ? body.token.slice(0, 4096) : '';
    const elapsed = Number(body.elapsed) || 0;
    const page    = clean(body.page, 120);
    const language = clean(body.language, 8);

    if (!message) return json({ error: 'empty' }, 400, cors);
    if (contact && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact)) return json({ error: 'contact' }, 400, cors);

    // 3. honeypot — silently accept so bots think it worked, but file nothing
    if (typeof body.website === 'string' && body.website.trim() !== '') return json({ ok: true }, 200, cors, 'dropped:honeypot');

    // 4. timing
    if (elapsed < MIN_ELAPSED_MS) return json({ ok: true }, 200, cors, 'dropped:timing');

    // 5. link density
    const links = (message.match(/https?:\/\/|www\./gi) || []).length;
    if (links > 2) return json({ ok: true }, 200, cors, 'dropped:links');

    // 6. rate limit (optional)
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    if (env.RATE_KV) {
      const key = `rl:${ip}`;
      const count = Number(await env.RATE_KV.get(key)) || 0;
      if (count >= RATE.max) return json({ error: 'rate' }, 429, cors);
      await env.RATE_KV.put(key, String(count + 1), { expirationTtl: RATE.windowSeconds });
    }

    // 7. Turnstile
    if (!token) return json({ error: 'captcha' }, 400, cors);
    const verify = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ secret: env.TURNSTILE_SECRET, response: token, remoteip: ip }),
    }).then(r => r.json()).catch(() => ({ success: false, 'error-codes': ['siteverify-unreachable'] }));
    if (!verify.success) {
      // "invalid-input-secret" = the stored TURNSTILE_SECRET is wrong; "invalid-input-response" = bad/expired token
      return json({ error: 'captcha' }, 400, cors, 'turnstile:' + ((verify['error-codes'] || []).join(',') || 'unknown'));
    }

    // File the issue
    const title = message.replace(/\s+/g, ' ').slice(0, 80) + (message.length > 80 ? '…' : '');
    const issueBody = [
      message,
      '',
      '---',
      cities   ? `**Cities added:** ${cities}` : null,
      contact  ? `**Contact:** ${contact}` : '**Contact:** not given',
      `**Page:** ${page || '/'}  ·  **Language:** ${language || 'en'}`,
      `**Received:** ${new Date().toISOString()}`,
    ].filter(Boolean).join('\n');

    const gh = await fetch(`https://api.github.com/repos/${env.FEEDBACK_REPO}/issues`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'findcommonhours-feedback-worker',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title, body: issueBody, labels: ['user-feedback'] }),
    });
    if (!gh.ok) {
      // Surface GitHub's own reason (401 bad token, 403 missing Issues permission, 404 wrong repo) - never the token.
      const detail = await gh.json().then(j => j && j.message).catch(() => '') || '';
      return json({ error: 'upstream' }, 502, cors, 'github:' + gh.status + (detail ? ':' + detail.slice(0, 80) : ''));
    }

    return json({ ok: true }, 200, cors);
  },
};

function clean(value, max) {
  if (typeof value !== 'string') return '';
  // strip control characters and angle brackets; the issue body is Markdown
  return value.replace(/[\x00-\x1f\x7f<>]/g, '').trim().slice(0, max);
}

function corsHeaders(origin, allowed) {
  return {
    'Access-Control-Allow-Origin': origin === allowed ? allowed : 'null',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}

function json(data, status, headers, note) {
  // Reason-only log for `wrangler tail`: status and code, never user content.
  console.log(JSON.stringify({ status, error: data && data.error, note }));
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...headers },
  });
}
