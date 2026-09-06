# Feedback endpoint — setup (about 15 minutes, all free)

The site's "Report a problem" link opens a short form that needs no account.
Submissions go to this Worker, which checks them and files each one as an issue
in a **private** repository. Until the two keys below are pasted into
`index.html`, the link simply falls back to the public GitHub issue chooser, so
nothing is broken while you set this up.

## 1. A private repo to receive feedback

Create `findcommonhours-feedback` as a **private** repo (Settings → New → Private).
Private repos are free. Nothing else is needed in it.

## 2. A token that can only open issues in that repo

GitHub → Settings → Developer settings → Fine-grained tokens → Generate:

- Repository access: **Only select repositories** → `findcommonhours-feedback`
- Permissions → Repository → **Issues: Read and write**. Nothing else.
- Expiration: a year is fine; put a note in your calendar.

Copy the token. You will paste it once in step 5 and never see it again.

## 3. A Turnstile widget

Cloudflare dashboard → **Turnstile** → Add widget:

- Domain: `findcommonhours.com`
- Widget mode: **Managed** (invisible for almost everyone; shows a checkbox only
  when Cloudflare is unsure)

You get a **site key** (public, goes in the page) and a **secret key** (private,
goes in the Worker).

## 4. Deploy the Worker

Install Wrangler once (`npm i -g wrangler`), then from this folder:

```bash
wrangler login
wrangler deploy
```

Wrangler prints the Worker's URL, something like
`https://findcommonhours-feedback.<your-subdomain>.workers.dev`. Keep it.

## 5. Store the two secrets

```bash
wrangler secret put TURNSTILE_SECRET     # paste the Turnstile secret key
wrangler secret put GITHUB_TOKEN         # paste the fine-grained token
```

They live encrypted in Cloudflare and are never in the repo.

## 6. Switch the site over

In `index.html`, find the `<dialog id="feedback-dialog"` element and fill in:

```html
data-endpoint="https://findcommonhours-feedback.<your-subdomain>.workers.dev"
data-sitekey="<Turnstile site key>"
```

Bump the asset version (`python tools/bump_assets.py`), commit, push. Done.

## Check it works

Open the site, click **Report a problem**, send a test message. Within a few
seconds an issue labelled `user-feedback` should appear in the private repo.
If nothing arrives, the Worker's logs (`wrangler tail`) will say which check
rejected it.

## What each control does

| Control | Stops | Cost to a real person |
|---|---|---|
| Turnstile (managed) | Bots, scripted abuse; tokens are single-use | Usually nothing; occasionally one checkbox |
| Honeypot field | Dumb form-fillers | None — it is invisible |
| 3-second timing | Instant scripted submits | None |
| Link density | Spam pasting URLs | Only if pasting 3+ links |
| Per-IP rate limit (optional) | One source flooding | 5 per hour is generous |
| Origin check | Other sites calling the endpoint | None |

Rejected submissions from the honeypot, timing and link checks are answered with
a fake success, so bots do not learn what tripped them.

## Rotating or revoking

- Token leaked or expired: revoke it on GitHub, generate a new one, run
  `wrangler secret put GITHUB_TOKEN` again. The Worker picks it up immediately.
- Too much spam getting through: switch the Turnstile widget to
  **Non-interactive** or lower `RATE.max` in `feedback-worker.js` and redeploy.
