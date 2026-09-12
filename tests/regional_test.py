"""Regional-holiday checks.

Guards the enrichment in tools/gen_holiday_pages.py, which the monthly workflow
re-runs unattended. The failure modes are quiet ones: the section silently
disappearing when an upstream release changes how subdivisions are exposed, the
names reverting to the local language ("Karfreitag" for "Good Friday") because
the language pass stopped applying to subdivisions, or the section shipping
expanded and burying the national dates it is meant to supplement.

Usage:  python -m http.server 8765    # from the repo root, in another shell
        python tests/regional_test.py
"""
import sys, os, re, glob
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

withreg = {n: h for n, h in pages.items() if "regional-section" in h}
print(f"{len(pages)} content pages, {len(withreg)} with a regional section")
check("a plausible number of countries have regional data",
      20 <= len(withreg) <= 60, len(withreg))

# Countries that certainly have sub-national holidays must have the section.
for n in ("switzerland.html", "canada.html", "india.html", "united-states.html",
          "spain.html", "australia.html", "germany.html"):
    check(f"{n} has regional data", n in withreg)

# Countries with no subdivisions must NOT grow an empty shell.
for n in ("uruguay.html", "laos.html"):
    if n in pages:
        check(f"{n} has no empty regional section", n not in withreg)

# Never ship expanded: the page must open as lightly as it did before.
open_by_default = [n for n, h in withreg.items()
                   if re.search(r"<details[^>]*\bopen\b", h)]
check("no regional section ships expanded", not open_by_default, open_by_default)

# Every row needs a machine-readable date and a stated scope.
bad_rows = []
for n, h in withreg.items():
    block = h[h.find("regional-section"):]
    rows = re.findall(r'<div data-date="(\d{4}-\d\d-\d\d)">(.*?)</div>\s*(?=<div|</div>)', block)
    for d, inner in rows[:400]:
        if 'class="where"' not in inner:
            bad_rows.append((n, d)); break
check("every regional row says where it applies", not bad_rows, bad_rows[:3])

# The language pass must survive the subdiv argument.
ch = withreg.get("switzerland.html", "")
check("Swiss names are in English, not German",
      "Good Friday" in ch and "Karfreitag" not in ch)
check("region names are spelled out, not codes",
      "Ticino" in ch and ">ZH<" not in ch)
check("large region lists are summarised, not enumerated",
      re.search(r"\d+ of \d+ cantons", ch) is not None)
check("small region lists are named",
      re.search(r'class="where">[A-Z][a-zü]+(, [A-Z][a-zü]+){0,3}<', ch) is not None)

# The intro must point at the data instead of apologising for its absence.
check("Switzerland's intro cites the regional count",
      re.search(r"further 44 dates are observed in individual cantons", ch) is not None)
check("the old 'only N set nationally' note is gone where data exists",
      "the remaining days are usually fixed by state, province or canton" not in ch)

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/holidays/switzerland.html", wait_until="networkidle", timeout=60000)

    closed = pg.eval_on_selector(".regional-section details", "e=>e.open")
    check("collapsed on load", closed is False)
    h_closed = pg.eval_on_selector(".regional-section details", "e=>e.getBoundingClientRect().height")
    check("adds little height while closed", h_closed < 120, h_closed)

    pg.click(".regional-section summary")
    pg.wait_for_timeout(250)
    check("opens on click", pg.eval_on_selector(".regional-section details", "e=>e.open"))
    h_open = pg.eval_on_selector(".regional-section details", "e=>e.getBoundingClientRect().height")
    check("reveals the rows", h_open > h_closed * 5, (h_closed, h_open))
    n = pg.eval_on_selector_all(".holiday-table.regional div[data-date]", "e=>e.length")
    check("all 44 Swiss regional dates present", n == 44, n)

    # the national table must still come first - the supplement cannot displace it
    order = pg.evaluate("()=>{const a=document.querySelector('.holiday-table:not(.regional)'),"
                        "b=document.querySelector('.regional-section');"
                        "return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING;}")
    check("national dates still come before regional ones", bool(order))
    check("no page errors", not errs, errs)
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All regional checks passed."))
sys.exit(1 if fails else 0)
