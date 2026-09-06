"""Health check for the site's external dependencies and static assets.

Exits non-zero with a readable report if anything is wrong, so a scheduled
workflow can raise an issue. Checks:

  1. Open-Meteo geocoding still responds AND still returns the fields the
     search ranking depends on (timezone, population, feature_code, admin1,
     country_code). A silent field removal would degrade results without
     any error.
  2. The holiday API still responds with dated entries.
  3. The static assets referenced by the pages all return 200.

Usage:  python tools/check_dependencies.py
"""
import json, sys, datetime, urllib.request, urllib.parse, urllib.error

UA = {"User-Agent": "findcommonhours-healthcheck", "Accept": "application/json"}
SITE = "https://findcommonhours.com"
problems, notes = [], []


def get(url, as_json=True, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r) if as_json else r.read()


# 1. geocoding -----------------------------------------------------------
REQUIRED = ["timezone", "population", "feature_code", "admin1", "country_code"]
try:
    data = get("https://geocoding-api.open-meteo.com/v1/search"
               "?name=Berlin&count=5&language=en&format=json")
    results = data.get("results") or []
    if not results:
        problems.append("geocoding: query for Berlin returned no results")
    else:
        missing = [f for f in REQUIRED if not any(f in r for r in results)]
        if missing:
            problems.append("geocoding: response no longer contains %s "
                            "- search ranking and the country fallback depend on these"
                            % ", ".join(missing))
        else:
            notes.append("geocoding: ok (%d results, all required fields present)" % len(results))
except Exception as e:
    problems.append("geocoding: request failed (%s: %s)" % (type(e).__name__, e))

# 2. holidays ------------------------------------------------------------
year = datetime.date.today().year
try:
    d = get("https://nagerholidays.com/api/v4/Holidays/US/%d" % year)
    if not isinstance(d, list) or not d:
        problems.append("holidays: US/%d returned no entries" % year)
    elif "date" not in d[0] or "name" not in d[0]:
        problems.append("holidays: entries no longer carry date/name fields")
    else:
        notes.append("holidays: ok (US/%d returned %d entries)" % (year, len(d)))
except Exception as e:
    problems.append("holidays: request failed (%s: %s)" % (type(e).__name__, e))

# Known-empty countries. Tracked so the list can be revisited, not treated as
# a failure -- these have never had coverage upstream.
KNOWN_EMPTY = ["IN", "AE", "PK", "SA", "TH", "MY", "IL"]
recovered = []
for cc in KNOWN_EMPTY:
    try:
        d = get("https://nagerholidays.com/api/v4/Holidays/%s/%d" % (cc, year), timeout=20)
        if isinstance(d, list) and d:
            recovered.append("%s (%d)" % (cc, len(d)))
    except Exception:
        pass
if recovered:
    notes.append("holidays: coverage APPEARED for %s - consider removing the "
                 "hardcoded fallback for these" % ", ".join(recovered))

# 3. static assets -------------------------------------------------------
ASSETS = ["favicon.ico", "favicon.svg", "apple-touch-icon.png", "assets/og.jpg",
          "ads.txt", "robots.txt", "sitemap.xml"]
for path in ASSETS:
    url = "%s/%s" % (SITE, path)
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200:
                problems.append("asset: %s returned HTTP %d" % (path, r.status))
    except urllib.error.HTTPError as e:
        problems.append("asset: %s returned HTTP %d" % (path, e.code))
    except Exception as e:
        problems.append("asset: %s failed (%s)" % (path, type(e).__name__))
if not any(p.startswith("asset:") for p in problems):
    notes.append("assets: ok (%d checked)" % len(ASSETS))

# ------------------------------------------------------------------------
for n in notes:
    print("  OK   " + n)
for p in problems:
    print("  FAIL " + p)

if problems:
    print("\n%d problem(s) found." % len(problems))
    sys.exit(1)
print("\nAll dependency checks passed.")
