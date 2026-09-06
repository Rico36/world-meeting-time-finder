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

### Holiday coverage gaps (product issue, not a bug)

`nagerholidays.com` returns **no data at all** for seven significant markets.
Verified 6 September 2026:

> India, UAE, Pakistan, Saudi Arabia, Thailand, Malaysia, Israel

These fail visibly as "Holiday status unavailable", and they are precisely the
places where holidays surprise Western schedulers most — Diwali, Eid, and the
Sunday-to-Thursday working week. `app.js` already carries a hardcoded fallback
for three fixed Indian national holidays; the other six have nothing.

Options, roughly in order of effort: extend the hardcoded fallback to cover the
major fixed-date holidays in those countries; add a second holiday source and
merge; or state the coverage limit plainly in the UI rather than showing a bare
"unavailable".

### Feedback form — setup pending

The no-login feedback dialog is shipped but inert: `index.html` carries empty
`data-endpoint` and `data-sitekey` attributes on `#feedback-dialog`, so the
footer link still falls through to the public GitHub issue chooser. Activating
it takes about fifteen minutes and is written up step by step in
`worker/README.md` — a private repo to receive submissions, a fine-grained token
scoped to that repo's issues, a Turnstile widget, and `npx wrangler deploy`.

Once live, submissions arrive as issues labelled `user-feedback` in the private
repo. The Worker's abuse controls and how to tune them are documented in the
same README. Run `node worker/feedback-worker.test.mjs` after any change to the
Worker.

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
