"""Generate holidays-fallback.json for countries the live holiday API does not cover.

nagerholidays.com returns nothing for these countries because their holidays are
announced rather than fixed: Islamic dates depend on moon sighting, Thailand and
Malaysia add substitution days by decree, Israel follows the Hebrew calendar and
India layers lunar festivals over state lists. python-holidays models all of that,
so we generate the list at build time and ship it as a static file. app.js reads
it only when the live API has nothing for a country.

Entries use the SAME shape as the live API so the matching code is shared:
  {"date": "2026-03-20", "name": "Eid al-Fitr", "nationalHoliday": true,
   "subdivisionCodes": null, "estimated": true}

`estimated` is set where python-holidays itself marks the date as an estimate -
in practice the moon-sighting holidays - and the UI renders those with a hedge.

Usage:  python tools/gen_holidays.py [year ...]     default: this year and next
Requires: pip install holidays
"""
import json, os, re, sys, datetime

try:
    import holidays
except ImportError:
    sys.exit("pip install holidays  (python-holidays) first")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "holidays-fallback.json")

# Countries the live API returns nothing for. Verified 6 Sep 2026; the monthly
# dependency check reports if any of them gain upstream coverage.
COUNTRIES = {
    "IN": "India", "AE": "United Arab Emirates", "SA": "Saudi Arabia",
    "PK": "Pakistan", "TH": "Thailand", "MY": "Malaysia", "IL": "Israel",
}

years = [int(y) for y in sys.argv[1:]] or [datetime.date.today().year, datetime.date.today().year + 1]
EST = re.compile(r"\s*\((?:estimated|estimate)\)\s*", re.I)

def english(cc, yrs):
    """Prefer English names; python-holidays falls back to the default language if
    en_US is not available for a country, so try the common tags in order."""
    for lang in ("en_US", "en_GB", "en"):
        try:
            h = holidays.country_holidays(cc, years=yrs, language=lang)
            # accept only if at least one name looks Latin-script; otherwise try next
            if any(re.search(r"[A-Za-z]", n) for n in h.values()):
                return h
        except Exception:
            continue
    return holidays.country_holidays(cc, years=yrs)

out = {"generated": datetime.date.today().isoformat(), "source": "python-holidays " + holidays.__version__,
       "years": years, "countries": {}}
summary = []
for cc, name in COUNTRIES.items():
    h = english(cc, years)
    rows = []
    for d, raw in sorted(h.items()):
        # a single date can carry several names joined by "; " - keep them separate for clarity
        for label in str(raw).split("; "):
            est = bool(EST.search(label))
            clean = EST.sub("", label).strip()
            rows.append({"date": d.isoformat(), "name": clean, "nationalHoliday": True,
                         "subdivisionCodes": None, "estimated": est})
    out["countries"][cc] = rows
    summary.append((cc, name, len(rows), sum(r["estimated"] for r in rows),
                    sum(1 for r in rows if not re.search(r"[A-Za-z]", r["name"]))))

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", os.path.relpath(OUT, REPO), "for", years, "-", os.path.getsize(OUT), "bytes\n")
print("  cc  country               entries  estimated  non-latin-names")
for cc, name, n, est, nonlatin in summary:
    print(f"  {cc}  {name:20}  {n:>7}  {est:>9}  {nonlatin:>15}")
