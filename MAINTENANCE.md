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

Note the coupling in the first point: the schedule sustains itself only on runs
that *actually commit*. A run where nothing moved prints "Nothing changed" and
commits nothing, so it does not reset the clock. In practice a month never
passes without holidays falling out of the upcoming lists across 246 countries,
so this is close to theoretical — but it is the reason the September 2026 audit
stopped tracking `__pycache__`. While the `.pyc` files were tracked they differed
on every run, so `git diff --quiet` was never true and the job committed
unconditionally. That masked the real change-detection *and* gave the clock a
false reset, which would have hidden a generator that had silently stopped
producing new dates.

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

### Top-bar nav: Holidays and City pairs

Both sections existed on ~480 pages and were reachable only from the footer.
They now sit in the header on **every** page, not just the homepage — adding it
to the homepage alone would have put Holidays one click away and then stranded
the reader, since the generated pages linked back only from their footers.

- The homepage and the five other root pages carry the markup inline.
- The 467 generated pages get it from `header(depth, section)` in
  `tools/gen_city_pairs.py`. `section` is `"holidays"` or `"time"`, which sets
  `aria-current="page"` so the nav says where you are. The 12 redirect stubs
  deliberately have no chrome and so no nav.
- **Below 560px the wordmark is hidden but stays in the accessibility tree**
  (clipped, not `display:none`). Brand mark + wordmark + two links + two buttons
  does not fit a phone, and on the generated pages that wordmark is the brand
  link's only accessible name — removing it outright would leave an unlabelled
  link.

Verified from 1280px down to 260px: no header overflow, no sideways page
scroll, 44px tap targets throughout. Covered by `tests/ux_test.py`, which also
clicks through to confirm the links go somewhere and mark the right section.

While fitting this, a **pre-existing** overflow turned up: the footer nav had
seven links at an 18px gap and no `flex-wrap`, so the whole page scrolled
sideways at 320px. Fixed in the same pass.

### The site is English-only — deliberately

The language selector (English, Spanish, French, German, Portuguese) was removed
on 12 Sep 2026. It was not broken so much as never finished:

- **1 of 485 pages carried translations.** 506 words out of ~210,000. Picking
  Spanish gave a Spanish homepage whose every link led into English.
- **No `hreflang` anywhere**, and the canonical was always `/`, so the five
  languages produced no SEO value at all.
- On the three guide pages the selector was present but the content had **no
  translatable strings**, so choosing a language changed nothing visible. That
  is what the site owner reported as "it reverts to English after a second" —
  nothing reverted; the rest of the site was simply never translated.

Separate per-country domains were considered and rejected: they split domain
authority five ways from a standing start, multiply maintenance by five, and
each needs its own AdSense review — a poor move while a low-value-content flag
is open.

Removing it deleted ~25 KB from `app.js` (112 → 87) and ~31 KB from `guides.js`
(52 → 20), since those files shipped four unused dictionaries to every visitor.

What remains, and why:

- `t()` and the `[data-i18n]` pass stay. They are how the copy reaches the page;
  they simply have one dictionary now. Do not inline the strings — the guide
  generators read the same objects.
- `?lang=` on a shared link is **ignored, not rejected**. Links shared before
  this change still carry it and must still open.
- Start-up clears any stored `commonHoursLanguage`, so a visitor who had chosen
  Spanish is not stranded on a language the site no longer serves.
- `tools/sync_guide_html.js` already hardcoded `lang = 'en'` and
  `tools/expand_guides.py` already emitted `{"en": ...}` only, so neither
  generator needed changing — the static guide HTML was English all along.

If multilingual is ever revisited, do it as `/es/` subdirectories with hreflang,
and start with the holiday pages: `python-holidays` ships **native** holiday
names (`Año Nuevo`, `Confraternização Universal`, `ईद-उल-फितर`), so those 247
pages can be translated properly by generation rather than machine-translated.

### One clock format per screen

Times appear in five places on the planner: the city rows, the result heading,
the meeting summary, each timeline row label, and the timeline axis. They must
all agree.

They did not, and the reason is worth knowing before touching any of them.
`hour:'numeric'` in `Intl.DateTimeFormat` resolves to **12-hour under `en` and
24-hour under `fr`** — so the format silently followed whichever locale string
was passed. The axis was worse: static markup reading `12 AM / 6 AM / 12 PM /
6 PM`, which followed nothing. A French visitor got 24-hour times above a
12-hour axis.

The rules now:

- `clockOpts()` in `app.js` is the single source. It passes `hour12` **explicitly**
  rather than letting the locale decide. Never call `Intl.DateTimeFormat` with
  `hour`/`minute` directly — go through `formatTime()` or `clockOpts()`.
- The axis is built by `renderAxis()` from the same setting. It cannot be static.
- 24-hour is padded to `hh:mm`; some locales otherwise write `0:00` next to
  `22:00` in one column. 12-hour is left unpadded, because `08:00 AM` is not how
  anyone writes it.
- The default comes from the **visitor's own locale**, via
  `Intl.…resolvedOptions().hour12`, not from the site language and not
  hard-coded. Forcing 12-hour would show `8:00 PM` to a German visitor, which no
  clock there displays; forcing 24-hour does the same to an American. The `12h` /
  `24h` toggle in the header overrides it and persists in `commonHoursClock`.
- The initial paint calls `applyClock(state.clock, false)` — `persist=false`, so
  the locale-derived default is not frozen into storage. Only an actual click
  persists a choice.

`tests/clock_test.py` checks all five surfaces agree, in three locales, before
and after toggling, and across a reload.

### Tests live in `tests/` — run them after any change

```bash
python -m http.server 8765          # from the repo root, in another shell
python tests/run_all.py             # 8 suites, ~2 minutes
python tests/run_all.py https://findcommonhours.com    # after a deploy
```

See `tests/README.md`. These were previously kept in a temporary scratchpad and
three suites — detection, holiday and feedback, about 56 checks — were lost when
it was cleaned. They have been rewritten from the code they cover. Anything
worth running twice belongs in the repo.

### The holidays library is pinned — regenerate with the same version

Both content workflows install `holidays==0.104`, and **the pin must match in
both**. Before regenerating the pages by hand, match it locally:

```bash
pip install "holidays==0.104"
```

This is not caution for its own sake. The install was originally unpinned, and
the day 0.104 shipped, the monthly job rewrote 27 pages: Brunei's *Isra' and
Mi'raj* moved a day, Ethiopia went from 13 public holidays to 12. Nothing in the
diff said why, and the sanity checks passed, because structurally nothing was
wrong. Two things follow from that:

1. **Content changes on a monetised site should be traceable to a decision.**
   An unpinned dependency publishes upstream edits automatically, unreviewed.
2. **Local and CI must agree, or they fight.** A maintainer regenerating on
   0.103 reverts the bot's output; the bot reverts theirs next month; repeat
   indefinitely. The symptom looks like a flapping workflow, not a version skew,
   so it is unpleasant to diagnose.

`tools/check_dependencies.py` reports when a newer release exists, **fails** if
either workflow stops pinning, and **fails** if the two pins disagree. So raising
the pin is a deliberate act that cannot be silently forgotten. To raise it: bump
both workflows, install the same version locally, regenerate, and read the diff
before committing — that diff is the upstream's holiday corrections, which is
exactly what deserves a human glance.

### Regional holidays — how the thin pages were fixed

Switzerland's page once showed 4 national holidays and read like a stub at 229
words. It now shows 44 more, by canton, at 596 words. The data was always there,
one argument away: `holidays.country_holidays(code, subdiv=...)`. 30 countries
have it; India gains 159 dates and Italy 194.

This mattered beyond page length. India is one of the seven countries the live
holiday API does not cover at all, so its page was leaning entirely on the
fallback — it is now the richest country page on the site.

Three decisions worth keeping:

- **The section is collapsed by default** (`<details>`). A reader who came to
  check one date should not have to scroll past 159 rows to reach the national
  ones. The page opens as lightly as it did before and the reader chooses to
  expand — which is the same principle the homepage follows. Google indexes
  content inside a collapsed `<details>`, so nothing is lost by hiding it.
- **Large region lists are counted, not named.** "24 of 27 cantons" is the
  useful fact; enumerating 24 names is noise. Below five, the names *are* the
  useful fact, so they are spelled out.
- **`REGION_NOUN` names each country's divisions properly** — cantons, provinces
  and territories, autonomous communities, union territories. Calling Swiss
  cantons "regions" is exactly the detail that makes generated content read as
  generated. Unlisted countries fall back to "regions".

The subdivision pass costs about a second for all 624 subdivisions, so there was
no reason to cache or precompute it.

`tests/regional_test.py` guards this, and the monthly workflow fails if fewer
than 20 pages carry a section (upstream could stop exposing subdivisions and
everything else would still pass) or if any section ships expanded.

**Six pages remain under 300 words** — Antarctica, Uruguay, Tokelau, Mexico,
Pitcairn Islands, Laos. These have no subdivisions and genuinely few holidays,
so they are short because they are complete, not because they are missing
something. Antarctica is the one genuine oddity: a public-holiday page for a
continent with no civilian population. It is a candidate for retirement if the
low-value-content review ever needs another gesture.

### Territories that share a sovereign's calendar

Twelve territory pages are retired into the sovereign page whose calendar they
actually observe — Svalbard into Norway, Åland into Finland, seven French
overseas territories into France, and so on. This was done because they were the
site's worst near-duplicates: `svalbard-and-jan-mayen.html` was a **92%** textual
match for `norway.html`, which is the exact shape AdSense treats as scaled,
low-value content. A second URL that says nothing the first does not is a
liability, not extra coverage.

**How the decision is made.** `SOVEREIGN` in `tools/gen_holiday_pages.py` is a
curated map of territory → sovereign. It supplies only the *direction*, because
the data cannot: ranking countries by holiday count proposes "American Samoa is
the parent of the United States" and "Benin is the parent of Switzerland", since
a superset relationship is not a sovereignty relationship.

Whether a merge actually happens is then decided from the holiday data on every
run. A territory is retired only if its sovereign's calendar already covers
**≥ 90%** of its dates (`MERGE_THRESHOLD`). Of 38 listed territories, 12 pass.
Puerto Rico (64%), Jersey (50%) and Gibraltar (46%) keep their own pages because
their calendars genuinely differ — which is the point. The goal is removing
pages that say nothing new, not shrinking the site.

Because the gate is re-evaluated every run, **adding a territory to `SOVEREIGN`
does not retire its page**, and a territory comes back automatically if the
upstream library ever gains distinct dates for it. Nobody has to notice.

**What a retirement produces:**

- A redirect stub at the old URL, marked `<!--redirect-stub-->`. GitHub Pages
  cannot issue a 301, so the stub is the static equivalent: `rel="canonical"` to
  the surviving page plus an instant meta refresh, which Google consolidates.
- **No ad code on the stub.** Ads on a body-less redirect page are precisely the
  "little or no content" case AdSense prohibits. `write_sitemap()` and the
  workflow's ad assertion both skip stubs by that marker — if you change the
  marker, change it in all three places.
- The territory stays listed on `holidays/index.html` and stays findable by the
  filter, linking to the parent with a "· France calendar" note. Dropping it
  would turn a duplication fix into a coverage loss.
- The parent page gains a "Where else these dates apply" section naming every
  territory it absorbed, so someone searching for Svalbard lands somewhere that
  confirms the answer.

`tests/merge_test.py` guards all of this — run it after touching the generator.

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
