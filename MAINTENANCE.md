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
| **Monthly** | Rebuild the 479 generated pages so their holiday lists move forward | **Yes** — commits straight to main once structural checks pass |
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

**`refresh-generated-pages.yml`** runs on the 1st of every month. It rebuilds
the 479 pages under `time/` and `holidays/`, checks the result structurally
(link integrity, page counts, and that the word count has not collapsed), and
commits straight to `main` if anything moved.

Two deliberate differences from the December workflow, both worth understanding
before changing them:

- **Monthly, not quarterly.** Scheduled workflows are disabled after 60 days
  without commit activity. A quarterly schedule has 90-day gaps, so it would
  switch itself off before its second run and nobody would notice until the
  dates went stale. Monthly stays inside the window, and **each run's own
  commit resets the clock** — the schedule keeps itself alive.
- **It commits rather than opening a PR.** December regenerates prose, which
  has produced plausible nonsense before and needs a human to read it. This
  only advances dates from deterministic generators, so a structural check is
  the useful gate. A PR nobody merges would also fail to reset the 60-day
  clock, defeating the point.

If you would rather review these, change the final step to open a PR — but then
merge them promptly, or the schedule will eventually disable itself.

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

| Dependency | Used for | If it fails |
|---|---|---|
| `geocoding-api.open-meteo.com` | City search | Search degrades to the ~60-city local seed list in `app.js`. Degrades gracefully; already handled |
| `nagerholidays.com/api/v4` | Holiday checks | Cities show "Holiday status unavailable" — this is the headline feature, so it fails visibly |
| Cloudflare Worker + Turnstile (`worker/`) | The "Report a problem" form | The form shows its error message and points people at the GitHub link. Nothing else on the site is affected. Only active once keys are configured — see `worker/README.md` |
| `findcommonhours-geo` Worker (`worker/geo-worker.js`) | Upgrading the detected reference city from a zone guess to a real city name | Silent no-op — the page keeps showing the zone-only guess it already displayed (e.g. "New York" for the whole US Eastern zone). Nothing else on the site is affected, and this dependency has no secrets and nothing to rotate |

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

Every page must also agree on the `?v=` cache-busting version. `bump_assets.py`
rewrites the root pages **and** the 485 generated ones under `time/` and
`holidays/` — it originally did only the root, which meant the December workflow
(generators first, bump second) wrote the generated pages with the *old* version
and left 479 of the site's 490 pages serving a stale stylesheet. If this ever
prints more than one line, something bumped a subset:

```bash
grep -rhoE 'styles\.css\?v=[0-9A-Za-z-]+' --include=*.html . | sort | uniq -c
```

The monthly refresh deliberately does not bump at all, so it should never move
this version.

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

### Detected-city geolocation — active, no secrets

A browser only knows its **time zone**, never its city — `Intl.DateTimeFormat`
reports `America/New_York` for anyone in the entire US Eastern zone, and IANA
just picked New York as that zone's representative name. The first cut of
"open on the visitor's own city" (6 September 2026) showed that representative
city as if it were a precise answer, which is honest about the zone but
overclaims about the location — a visitor in Atlanta saw "New York".

`findcommonhours-geo.ricky-freyre.workers.dev` (source in `worker/geo-worker.js`,
config in `worker/wrangler.geo.toml`) fixes this by echoing Cloudflare's own
per-request edge geolocation (`request.cf`) back to the browser as JSON — no
external API call, no key, nothing stored or logged. `app.js` shows the
zone-only guess immediately, exactly as before, then fires this lookup in the
background and swaps in the real city name **only if** the result arrives
within 1.5s and its time zone agrees with the browser's own. A mismatch
(VPN, travel, a stale system clock, or Cloudflare's IP database simply being
wrong for that connection) leaves the honest zone-only name in place rather
than showing a city next to the wrong time zone.

Nothing to rotate here: no secrets, no expiring token, no third-party account.
The only failure mode is the Worker being unreachable, which the site already
handles by design — see the dependency table above. Redeploy with
`npx wrangler deploy -c wrangler.geo.toml` from `worker/` if the source changes;
`node worker/geo-worker.test.mjs` covers it (7 cases).

Run `node worker/feedback-worker.test.mjs` after any change to the Worker, and
`npx wrangler deploy` from `worker/` to ship it.

### Content volume — city-pair pages

AdSense returned **"Needs attention: Low value content"** on 11 September 2026,
with the site still at 5 pages / ~3,700 words. The guides were substantive by
then, so page *count* was the binding constraint: Google weighs the size of the
indexable site, and a single interactive tool plus a few articles reads as small
regardless of how good each article is.

`tools/gen_city_pairs.py` now generates **232 pages** under `time/` — 210 pairs
of 21 major business hubs, 21 per-city hubs, and an index — totalling roughly
91,000 words. Every page is computed, not spun: the real offset and every date
range where the gap shifts across the year, a 9am–5pm overlap window (or an
honest "no shared working hours, here is the least-bad compromise"), both
cities' clock-change dates, both countries' next public holidays, and a link
into the planner pre-filled through the `?city=` URL scheme.

```bash
pip install holidays
python tools/gen_city_pairs.py     # rewrites time/ and sitemap.xml
```

**Regenerate every few months.** The "upcoming public holidays" block is
relative to the generation date and decays as those dates pass; the clock-change
dates roll over each year. The generator clears `time/*.html` first, so
re-running is safe and removes orphans.

Two traps, both hit on the first run:

- **One canonical slug.** Pair filenames and every internal link must come from
  the same `pair_slug()`. Deriving the filename from the city-list order and the
  links from an alphabetical sort produced **934 broken links** across 106
  targets. Sort by *slug*, not name — "São Paulo" sorts after "Seoul" by name
  but before it as `sao-paulo`.
- **No live claims on static pages.** The FAQ originally said "X o'clock in
  Tokyo *right now*", which is wrong for most of the year on a page generated
  once. It now states the majority-of-year offset and points to the planner.

Deliberately not an exhaustive cross-product of every city in the app's data —
that yields obscure, low-intent pairs that read as doorway pages, which is
Google's separate and worse "scaled content abuse" policy. All 21 cities are
independently defensible hubs.

If more pages are needed later, add cities to `CITIES` in the generator; the
pair count grows as n(n−1)/2, so 25 cities would give 300 pairs.

Each pair page opens with an **at-a-glance block** — time gap, best meeting
time, next holiday — before any prose. A visitor from search gets the answer
without reading; the detail still follows for anyone who wants it.

### Public holidays by country

`tools/gen_holiday_pages.py` generates `holidays/` — one page per country for
**246 countries** plus an index, about 105,000 words. Built to be a *tool*
rather than an article: a scannable list with the weekday for every date, a
flag when a holiday lands on a weekend or creates a likely long weekend, and a
marker for dates python-holidays reports as estimated (the moon-sighting ones).

```bash
python tools/gen_holiday_pages.py     # rewrites holidays/ and sitemap.xml
```

Countries whose national list is six days or fewer get a line explaining that
the rest are usually set regionally — Switzerland has four national days and
the rest by canton, so without that note the page reads as broken rather than
correct.

No data for Ukraine or three uninhabited territories; those are skipped.

**Both generators call the same `write_sitemap()`**, which scans `time/` and
`holidays/` on disk rather than being handed a list — so whichever runs last
still produces a complete sitemap and the two can never drift. Currently 484
URLs.

### The day/night map

`tools/gen_map_data.py` builds two assets the planner's map needs:

```bash
python tools/gen_map_data.py     # -> assets/world-land.json, assets/zone-points.json
```

- `world-land.json` — Natural Earth 110m land, **public domain (CC0)**, reduced
  to 84 SVG paths in a 360×180 equirectangular space (`x = lon+180`,
  `y = 90-lat`). ~53 KB. Specks under 1.2 square degrees are dropped.
- `zone-points.json` — the tz database's own `zone1970.tab` coordinates for 312
  zones, used to place a city whose real latitude and longitude we do not have
  (URL-restored cities, the local seed list). Geocoding results carry real
  coordinates and are preferred. Legacy zone names go through `canonicalZone()`
  first, so `Asia/Calcutta` still resolves.

Regenerate only if the land outline or the tz database changes; neither moves
often.

**No time zone boundaries are drawn, deliberately.** Real borders are jagged
and political — China spans five geographic bands on a single zone, Nepal is
+5:45 — so a band map would be approximate in a way that undercuts a site that
hedges moon-sighting holiday dates for accuracy. The map claims two things,
both exactly true: these cities are here, and it is night here.

The terminator is computed live in `subsolarPoint()` in `app.js`. If you touch
that maths, check it the way it was checked originally: June must give a
declination near +23.44 with the north pole lit, December near −23.43 with it
dark, and the equinoxes near 0. The night polygon closes along whichever pole
is in darkness and **that edge flips at the equinox** — test both solstices
rather than discovering it in December.

### Where the planner CTA belongs

Generated pages do **not** carry "Open the meeting planner" above their
content. A visitor on a holiday page came for holidays; a call to action for a
different tool in front of that is a distraction, and every generated page
already links to the planner from its footer and its related-links nav.

The one exception is the pair pages, whose CTA is contextual — it opens the
planner with both cities pre-filled — so it sits under "Best time to meet"
and names the two cities rather than advertising the planner generically.

### Checking generated output

After running either generator, verify links before pushing. This caught 934
broken links the first time:

```bash
python - <<'PY'
import os, re
root = "."
for sub in ("time", "holidays"):
    d = os.path.join(root, sub); files = set(os.listdir(d))
    for f in files:
        if not f.endswith(".html"): continue
        for h in re.findall(r'href="([^"]+)"', open(os.path.join(d, f), encoding="utf-8").read()):
            h = h.split("?")[0].split("#")[0]
            if not h or h.startswith("http") or h.endswith("/"): continue
            if h.startswith("../"):
                if not os.path.exists(os.path.join(root, h[3:])): print("BROKEN", sub, f, h)
            elif h.endswith(".html") and h not in files: print("BROKEN", sub, f, h)
print("done")
PY
```

Strip the query string first — `styles.css?v=…` is not a missing file, and a
checker that forgets this reports several hundred false positives.

### Dates that correct themselves

The at-a-glance "next public holiday" on both the country pages and the pair
pages is **recomputed in the browser** from `data-date` attributes on the
dates already in the page. It is not baked in.

That matters because these pages are rebuilt monthly, not daily: a static
"in 81 days" is wrong the next morning, and a static "next holiday" is wrong
the moment that date passes. Regeneration moves the *lists* forward; the
browser keeps the *highlight* correct in between.

If you edit either generator, keep the `data-date` attributes — without them
the scripts find nothing and the block hides itself rather than showing
something false.

### Index pages: grouping and filter

Both `/time/` and `/holidays/` list hundreds of links, which as a flat
alphabetical list is a wall nobody scrolls. Each index groups its links
(holidays by continent from GeoNames `countryInfo.txt`, city pairs by first
city) and carries a type-to-filter box.

The filter is scoped to `#filter-target`, deliberately: `/time/` has a
"browse by city" grid *above* the filter that must not be counted or hidden by
it. If a future index adds links outside that wrapper they are ignored by the
filter, which is usually what you want — but the running count only reflects
what is inside the wrapper.

### Homepage: what belongs there

The homepage is the tool, not the article. Until 11 September it also had to
carry the site's entire text weight, because there were only five pages; with
~490 pages that is no longer true, and it was cut back accordingly:

- **Tools** (`#tools`) and **Guides** (`#guides`) are separate sections. Tools
  lists what the site *does* (planner, city pairs, holidays); guides lists the
  three explanatory articles. They were one mixed grid and read as a grab-bag.
- The 156-word holiday methodology block became a 45-word stub linking to
  **`holiday-data-accuracy.html`**, which now also collects the limitations
  that were scattered elsewhere: the seven countries with no upstream data,
  moon-sighting estimates, and why a clear public calendar is not the same as
  a free colleague.

Homepage is ~520 words. **Do not cut it to a bare widget** — a tool with 150
words of chrome is exactly the thin signal that got flagged in the first
place. The FAQ in particular earns its place: scannable, and it carries
schema.

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
| *(fresh load, no saved cities)* | Your own city appears as the first row within about a second, labelled "Your reference". It may briefly show the zone's representative city (e.g. "New York") before upgrading to your real city (e.g. "Alpharetta") once the geo lookup resolves — that upgrade only happens if it agrees with your browser's zone. If no city appears at all, the browser may report a **legacy zone name** (Chromium says `Asia/Calcutta`, `Europe/Kiev`) — add it to `ZONE_ALIASES` in `app.js` |
| *(add your detected city plus 2+ others, then reload)* | Your detected city is still the first row after reloading. This broke once already: restoring 3+ saved cities correctly strips the one flagged `detected` before trusting storage, but the two that were left had been silently read as "already have enough" — the re-detection gate must key off "is a detected row present", not a city count |

Then add two cities and confirm the timeline and holiday panel still render.
