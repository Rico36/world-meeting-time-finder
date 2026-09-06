# Maintenance

What this site needs, how often, and how to do it. Written 6 September 2026.

The short version: **one unavoidable job every December**, a quarterly
ten-minute dependency check, and everything else is event-driven.

---

## The calendar

| When | Job | Why it can't be skipped |
|---|---|---|
| **Every December** | Regenerate the 2026 dates in the guides | They are written as literal years and go stale on 1 January |
| **Quarterly** | Check the two external APIs and the static assets | Both APIs are free, third-party and have no SLA |
| **Annually** | Regenerate `REGION_CITIES` / `COUNTRY_CITIES` from GeoNames | Populations drift; countries occasionally change DST law |
| **Annually** | Renew the domain | Expiry takes the whole site down |
| **Monthly, 5 min** | Search Console + AdSense policy centre | Catches indexing and policy problems early |

---

## 1. December: refresh the dated guide content

**This is the only job with a hard deadline.** `guides.js` contains nine literal
references to 2026, including a fifteen-city table of clock-change dates in the
daylight-saving guide, and sentences like "In 2026 the United States moves on
8 March and 1 November". On 1 January these become wrong, on a page whose entire
value is being accurate about dates.

```bash
python tools/expand_guides.py      # regenerates the dated sections from IANA tzdata
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
