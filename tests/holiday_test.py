"""Holiday-page checks.

Rebuilt Sep 2026 after the original scratchpad copy was lost. Deliberately does
not re-cover ground held by its neighbours: freshness_test.py owns the
self-correcting countdown, merge_test.py the retired territories, and
regional_test.py the subdivision sections. What is left - and what this file
guards - is that the pages work as a TOOL rather than an article: every date
carries its weekday, clashes are flagged, moon-sighting estimates are marked
rather than stated as fact, and the index filter finds a country without
counting the furniture around it.

Usage:  python -m http.server 8765     # from the repo root, in another shell
        python tests/holiday_test.py
"""
import sys, os, re, glob, datetime
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

pages = {}
for f in sorted(glob.glob(os.path.join(REPO, "holidays", "*.html"))):
    h = open(f, encoding="utf-8").read()
    if "<!--redirect-stub-->" not in h:
        pages[os.path.basename(f)] = h
countries = {n: h for n, h in pages.items() if n != "index.html"}

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))

    # ---- 1. every date is scannable: weekday spelled out, ISO date attached ----
    WD = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    bad = []
    for n, h in list(countries.items()):
        for iso, when in re.findall(r'data-date="(\d{4}-\d\d-\d\d)"><span class="when">([^<]+)', h):
            d = datetime.date.fromisoformat(iso)
            if not when.startswith(WD[d.weekday()]):
                bad.append((n, iso, when)); break
    check("every date states its own correct weekday", not bad, bad[:3])

    # ---- 2. weekend clashes are flagged, and only real ones ----
    # National tables only. The regional tables carry a "where" column instead of
    # the weekend/long-weekend tags, so scanning the whole page reports every
    # regional row as a missing flag.
    def national_only(html):
        out, pos = [], 0
        for m in re.finditer(r'<div class="holiday-table(?: regional)?">', html):
            if "regional" in m.group(0):
                continue
            end = html.find("</div></section>", m.end())
            out.append(html[m.end():end if end != -1 else len(html)])
        return "".join(out)

    wrong = []
    for n, h in list(countries.items())[:80]:
        for iso, rest in re.findall(r'data-date="(\d{4}-\d\d-\d\d)">(.{0,400}?)(?=<div data-date|$)',
                                    national_only(h), re.S):
            weekend = datetime.date.fromisoformat(iso).weekday() >= 5
            tagged = "falls on a weekend" in rest
            if weekend != tagged:
                wrong.append((n, iso, weekend, tagged)); break
    check("the weekend flag matches the actual weekday", not wrong, wrong[:3])

    # ---- 3. moon-sighting dates are marked, never stated flatly ----
    hits = [n for n, h in countries.items() if "date set by moon sighting" in h]
    check("moon-sighting dates are marked as estimates", len(hits) >= 20, len(hits))
    leaked = [n for n, h in countries.items() if "(estimated)" in re.sub(r"<[^>]+>", "", h)]
    check("the raw '(estimated)' marker never reaches the reader", not leaked, leaked[:3])

    # ---- 4. the seven API-uncovered countries still have real dates ----
    # nagerholidays.com returns nothing for these; the pages are built from
    # python-holidays, so a regression here would be invisible on the live API.
    thin = []
    for n in ("india.html", "united-arab-emirates.html", "pakistan.html",
              "saudi-arabia.html", "thailand.html", "malaysia.html", "israel.html"):
        if n in countries:
            rows = len(re.findall(r'data-date="', countries[n]))
            if rows < 8:
                thin.append((n, rows))
    check("the 7 API-uncovered countries carry real holiday data", not thin, thin)

    # ---- 5. the index filter finds a country and counts only countries ----
    # Retired territories stay listed (pointing at the page that absorbed them),
    # so the index is every country, not every content page.
    stubs = len(glob.glob(os.path.join(REPO, "holidays", "*.html"))) - len(pages)
    expected = len(countries) + stubs
    pg.goto(f"{BASE}/holidays/", wait_until="networkidle", timeout=60000)
    total = pg.eval_on_selector_all("#filter-target li", "e=>e.length")
    check("the index lists every country, retired territories included",
          total == expected, (total, expected))
    retired_rows = pg.eval_on_selector_all(
        "#filter-target li a[title*='calendar']", "e=>e.length")
    check("retired territories are listed and annotated",
          retired_rows == stubs, (retired_rows, stubs))

    pg.fill("#filter", "portu")
    pg.wait_for_timeout(350)
    vis = pg.eval_on_selector_all("#filter-target li:not([hidden])",
                                  "e=>e.map(x=>x.innerText.trim())")
    check("filtering narrows to the match", len(vis) == 1 and "Portugal" in vis[0], vis)
    count_txt = pg.inner_text("#filter-count")
    check("the count reflects the filter", "1" in count_txt, count_txt)

    # The filter must be scoped to #filter-target: /time/ has a second grid above
    # it that must not be counted or hidden (unscoped it reported 231, not 210).
    pg.goto(f"{BASE}/time/", wait_until="networkidle", timeout=60000)
    pg.fill("#filter", "zzzznomatch")
    pg.wait_for_timeout(350)
    outside = pg.eval_on_selector_all(
        ".link-grid a:not(#filter-target .link-grid a)", "e=>e.filter(x=>x.offsetParent!==null).length")
    check("the filter does not hide the browse-by-city grid above it", outside > 0, outside)

    check("no page errors", not errs, errs)
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All holiday checks passed."))
sys.exit(1 if fails else 0)
