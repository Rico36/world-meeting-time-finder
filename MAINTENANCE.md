# Maintenance

What this site needs, how often, and how to do it. Written 6 September 2026.

The short version: **one unavoidable job every December**, a quarterly
ten-minute dependency check, and everything else is event-driven.

---

## The calendar

| When | Job | Automated? |
|---|---|---|
| **Every December** | Regenerate the dated content in the guides | **Yes** — opens a PR you review and merge |
| **Monthly** | Check the two external APIs and the static assets | **Yes** — raises an issue only if something breaks |
| **Annually** | Regenerate `REGION_CITIES` / `COUNTRY_CITIES` from GeoNames | No — read the output before shipping |
| **Annually** | Renew the domain | No |
| **Annually** | Rotate the feedback Worker's GitHub token (fine-grained tokens expire) | No — `npx wrangler secret put GITHUB_TOKEN` |
| **Monthly, 5 min** | Search Console + AdSense policy centre | No |

## Automation

Two workflows in `.github/workflows/` cover the two scheduled jobs.

**`annual-content-refresh.yml`** runs at 06:00 UTC on 1 December, regenerates
the guides for the following year, bumps the asset versions, checks the result
still parses, and opens a pull request. It deliberately does not push to `main`:
these generators have produced plausible nonsense before, so a human reads the
diff before it reaches a live, monetised site. Merging deploys automatically.

You can also run it any time from the Actions tab, optionally passing a year.

**`dependency-check.yml`** runs monthly. It confirms the geocoding API still
returns the fields the ranking depends on — a silent field removal would degrade
results with no error anywhere — that the holiday API still answers, and that no
static asset has started 404ing. It is quiet when healthy: it opens an issue only
on failure, and comments on the existing issue rather than filing duplicates. It
also reports if holiday coverage ever *appears* for the seven missing countries,
which would be a cue to drop the hardcoded fallback.

> **Watch for this:** GitHub disables scheduled workflows in repositories with no
> commit activity for 60 days. This repo can easily go quiet for that long. GitHub
> emails the owner first, and re-enabling is one click in the Actions tab — but if
> December passes with no pull request, that is the first thing to check.

Actions may open pull requests on this repo (Settings → Actions → General). The
default token permission is left at read-only; each workflow requests only the
scopes it needs.

## Reviewing what the automation produces

### The December pull request — a five-minute review

The PR touches `guides.js` and the three guide pages. Check three things:

1. **Spot-check two dates against an independent source.** Open the diff, find
   the "Clock changes in YYYY" list, and compare New York and London against
   [timeanddate.com/time/change](https://www.timeanddate.com/time/change/) for
   that year. If those two are right, the rest almost certainly are — they all
   come from the same tzdata.
2. **Read the converter paragraph.** It should name the same US and European
   dates as the list. If the paragraph and the list disagree, the generator's
   prose template has drifted from its data.
3. **Scan for surprises.** A city that has always changed clocks suddenly saying
   "no clock change", or vice versa, is worth a second look. It might be a real
   law change (Mexico did this in 2022) or a tzdata quirk.

If all three pass, merge. Deployment is automatic.

**If something is wrong:** close the PR without merging (nothing has deployed),
fix the cause, then re-run from the Actions tab → *Annual content refresh* →
*Run workflow*, entering the year. The branch is force-pushed, so re-running is
safe. The usual causes are a city entry in the `CITIES` list at the top of
`tools/expand_guides.py`, or the prose template in the same file.

### Dependency-check failures — what each one means

The issue the workflow opens quotes the report line. Match it here:

| Report says | What happened | What to do |
|---|---|---|
| `geocoding: response no longer contains ...` | Open-Meteo changed its response shape | Search is degraded but working. Update the field names in `searchPlaces()` in `app.js` to match the new response |
| `geocoding: request failed` | Open-Meteo is down or moved | Search falls back to the ~60-city seed list automatically. Wait a day; if persistent, check open-meteo.com for a new endpoint |
| `holidays: US/YYYY returned no entries` | Holiday API down or year not yet published | Holiday panel shows "unavailable". Early in a new year this can be the API lagging; re-run in a week before doing anything |
| `holidays: coverage APPEARED for ...` | Good news — a missing country now has data | Consider removing that country's hardcoded fallback in `app.js` |
| `asset: X returned HTTP 404` | A file was renamed or deleted | Find what references it (`grep -rn "X" *.html`) and fix the reference or restore the file |

Close the issue once fixed; the next monthly run will comment on it again if the
problem persists.

### Feedback form failures — read the Worker's reason log

If a submission shows "Couldn't send", the Worker logs *why* — status, error
code and a short note, never the message text. Watch it live from `worker/`:

```bash
npx wrangler tail --format json
```

then submit again and match the `note`:

| Note in the log | What it means | What to do |
|---|---|---|
| `github:403:Resource not accessible by personal access token` | The fine-grained token lacks **Issues: Read and write**, or `findcommonhours-feedback` isn't selected under its repository access | Edit the token on GitHub. Editing permissions in place keeps the same token value, so no `secret put` is needed; if you *regenerate* it instead, run `npx wrangler secret put GITHUB_TOKEN` |
| `github:401:…` | Token revoked or expired | Generate a new one and `npx wrangler secret put GITHUB_TOKEN` |
| `github:404:…` | `FEEDBACK_REPO` in `wrangler.toml` names a repo the token can't see | Fix the name or the token's repository access |
| `turnstile:invalid-input-secret` | The stored `TURNSTILE_SECRET` is wrong | `npx wrangler secret put TURNSTILE_SECRET` with the widget's secret key |
| `turnstile:invalid-input-response` / `timeout-or-duplicate` | The browser's token was bad or expired (dialog left open too long) | Nothing to fix; the user retries |
| `dropped:honeypot` / `dropped:timing` / `dropped:links` | Treated as a bot: hidden field filled, sent under 3 s, or 3+ URLs | Expected. A real person who sees this submitted too fast |
| `403 origin` | Request didn't come from `https://findcommonhours.com` | Only relevant if the site moves domains — update `ALLOWED_ORIGIN` |

Tail captures land in `worker/tail*.log` and are gitignored — they contain IPs.

---

## 1. December: refresh the dated guide content

**This is the only job with a hard deadline.** `guides.js` contains nine literal
references to 2026, including a fifteen-city table of clock-change dates in the
daylight-saving guide, and sentences like "In 2026 the United States moves on
8 March and 1 November". On 1 January these become wrong, on a page whose entire
value is being accurate about dates.

```bash
python tools/expand_guides.py 2027   # regenerates the dated sections from IANA tzdata
node tools/sync_guide_html.js      # mirrors the result into the static HTML
python tools/gen_holidays.py 2027 2028   # holiday fallback for the seven uncovered countries
```

Then bump the `?v=` query string on `styles.css`, `app.js` and `guides.js` across
all `*.html`, commit, and push. GitHub Pages sets `max-age=600`, so without the
bump returning visitors keep the cached files.

Change the `year=2026` default in `tools/expand_guides.py` before running.

---

## 2. Quarterly: the ten-minute check

### External runtime dependencies

The site has exactly two, both free and neither guaranteed:

| Dependency | Used for | If it fails |
|---|---|---|
| `geocoding-api.open-meteo.com` | City search | Search degrades to the ~60-city local seed list in `app.js`. Degrades gracefully; already handled |
| `nagerholidays.com/api/v4` | Holiday checks | Cities show "Holiday status unavailable" — this is the headline feature, so it fails visibly |
| Cloudflare Worker + Turnstile (`worker/`) | The "Report a problem" form | The form shows its error message and points people at the GitHub link. Nothing else on the site is affected. Only active once keys are configured — see `worker/README.md` |

Check both still return the expected shape:

```bash
curl -s "https://geocoding-api.open-meteo.com/v1/search?name=Berlin&count=3&format=json" | head -c 200
curl -s "https://nagerholidays.com/api/v4/Holidays/US/2026" | head -c 200
```

The geocoding response must keep `timezone`, `population`, `feature_code`,
`admin1` and `country_code` — the search ranking and the country fallback all
depend on those fields.

### Static assets

Confirm nothing 404s. This has bitten before: `og.png` was renamed to `og.jpg`
while the meta tag still pointed at the old name, silently breaking social
previews.

```bash
for p in favicon.ico favicon.svg apple-touch-icon.png assets/og.jpg ads.txt robots.txt sitemap.xml; do
  printf "%-24s %s\n" "$p" "$(curl -sS -o /dev/null -w '%{http_code}' https://findcommonhours.com/$p)"
done
```

---

## 3. Annually: regenerate the place data

`app.js` embeds two generated maps: `REGION_CITIES` (US states, DC, Canadian
provinces) and `COUNTRY_CITIES` (230 countries plus aliases). Both come from
GeoNames and change slowly.

```bash
python tools/gen_regions.py     # -> region_cities.js
python tools/gen_countries.py   # -> country_cities.js
```

Regenerate sooner if a country changes its DST law, since the "one city per time
zone" grouping would then be wrong.

**Read the output before wiring it in.** Both generators have produced plausible
nonsense that only eyeballing caught: grouping by zone *name* instead of real UTC
offset gave Brazil four cities at the same offset and no Manaus; without a
population floor, "UK" suggested Dhekelia (a base in Cyprus) and "India"
suggested Abbaspur. Both guards are in the scripts now, but new data can find new
edges.

---

## 4. What does NOT need maintaining

- **Time zone rules.** The site resolves offsets through the browser's own
  `Intl` and tzdata. When a country changes its DST rules, visitors get the fix
  through their OS updates. Nothing here needs to change.
- **The meeting-time calculation.** No external input, no dated assumptions.
- **Hosting.** GitHub Pages serves static files; there is no server, no
  dependency tree and nothing to patch.

---

## 5. Known open issues

### Holiday coverage for countries the live API skips

`nagerholidays.com` returns nothing for **India, UAE, Saudi Arabia, Pakistan,
Thailand, Malaysia and Israel** — not by accident: their holidays are announced
rather than fixed (moon sighting, cabinet decrees, lunar calendars), and no free
API attempts them. `date.nager.at` covers 204 countries and none of these.

These are now served from **`holidays-fallback.json`**, generated at build time
by `tools/gen_holidays.py` from the `python-holidays` library, which models the
lunar and Islamic calendars. `app.js` reads it only when the live API has nothing
for a country, and only for the years the file covers — outside those it still
shows "unavailable" rather than guessing. Entries use the live API's own shape,
so the matching code is shared.

**Estimated dates are shown as such.** The library marks moon-sighting holidays
(Eid, Arafah, Islamic New Year, Prophet's Birthday, Ashura) as estimates, and the
UI renders them with *"expected date — the final day is set by moon sighting"*.
Saudi Arabia carries no estimates because it publishes its calendar in advance.
Don't remove that hedge: being honest about what can't be known ahead is the
feature.

Regeneration is part of the December workflow (two years ahead, so January is
never blind). To do it by hand:

```bash
pip install holidays
python tools/gen_holidays.py 2027 2028
```

To add a country, put its ISO code in `COUNTRIES` in the generator. To retire one
because the live API gained it, remove it there — the monthly dependency check
reports when that happens. What the file still can't know: same-week substitute
days and the ±1 day when a moon sighting differs from the estimate.

### Feedback form — active

The no-login feedback dialog is live and was verified end to end on
6 September 2026: a real submission from the site cleared every control,
including Turnstile, and arrived as issue #1 labelled `user-feedback` in the
private `Rico36/findcommonhours-feedback` repo. **Check that repo for new
feedback** — nothing notifies you otherwise unless you turn on issue
notifications for it on GitHub.

Moving parts: the Worker at `findcommonhours-feedback.ricky-freyre.workers.dev`
(source and setup in `worker/`), a Turnstile widget for `findcommonhours.com`,
and a fine-grained GitHub token holding only **Issues: Read and write** on the
private repo. The one setup mistake made the first time was selecting
"Repository advisories" instead of "Issues" in the token's permission list —
they sit close together and the wrong one fails with *"Resource not accessible
by personal access token"*.

Run `node worker/feedback-worker.test.mjs` after any change to the Worker, and
`npx wrangler deploy` from `worker/` to ship it.

### Content volume

Five pages, roughly 3,500 words. Guides sit at 870–980 words each after the
September 2026 expansion. Page *count* is now the weaker axis than words per
page.

### Multilingual SEO

Five languages, one URL, no `hreflang`, canonical always `/`. The translations
carry no SEO value as built, and the expanded guide content is English-only.

---

## 6. After any change

The search UI has broken in non-obvious ways twice, both times in edge cases
that the obvious test queries missed. Before pushing, check these by hand:

| Query | Expect |
|---|---|
| `New Mexico` | Albuquerque first, under a "Cities in New Mexico" header |
| `Ontario` | **Toronto** first, not Ontario, California |
| `Bayamón` | Every row shows a country — Open-Meteo omits it for territories |
| `Germany` | Berlin, Hamburg, Munich |
| `Texas` | Houston, San Antonio, **El Paso** (the Mountain-time city) |

Then add two cities and confirm the timeline and holiday panel still render.
