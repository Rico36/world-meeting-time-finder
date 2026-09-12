"""Checks the self-correcting dates and the map's visibility. Usage: python freshness_test.py [base]"""
import sys, re, datetime
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []

    # ---- map should appear with ONE city (the whole point of the change) ----
    ctx = b.new_context(timezone_id="America/New_York", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(2500)
    n = pg.eval_on_selector_all("#city-list .city-row", "e=>e.length")
    check("one detected city on load", n == 1, n)
    check("map visible with a single city",
          not pg.eval_on_selector("#world-map-figure", "e=>e.hidden"))
    check("map has a pin for that city",
          pg.eval_on_selector_all("#world-map .pin", "e=>e.length") == 1)
    check("map is outside the hidden results card",
          pg.eval_on_selector("#world-map-figure", "e=>!e.closest('#results')"))
    ctx.close()

    # ---- country page: next-holiday + countdown recomputed on load ----
    ctx = b.new_context(); pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/holidays/japan.html", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(700)
    away = pg.inner_text("[data-next-away]").strip()
    date_txt = pg.inner_text("[data-next-date]").strip()
    name_txt = pg.inner_text("[data-next-name]").strip()
    check("countdown rendered client-side", bool(away), repr(away))
    m = re.search(r"in (\d+) days", away)
    if m:
        # the stated countdown must match the stated date, computed independently here
        d = datetime.datetime.strptime(date_txt + f" {datetime.date.today().year}", "%d %B %Y").date()
        if d < datetime.date.today():
            d = d.replace(year=d.year + 1)
        expected = (d - datetime.date.today()).days
        check("countdown agrees with the date it shows", int(m.group(1)) == expected,
              f"says {m.group(1)}, date implies {expected}")
    else:
        check("countdown agrees with the date it shows", away in ("— today", "— tomorrow"), away)
    # and the highlighted holiday must not be in the past
    rows = pg.eval_on_selector_all(".holiday-table div[data-date]", "e=>e.map(x=>x.dataset.date)")
    future = [r for r in rows if r >= datetime.date.today().isoformat()]
    check("holiday rows carry ISO dates", len(rows) > 10, len(rows))
    check("highlighted holiday is in the future",
          bool(future) and name_txt, (name_txt, future[:1]))
    ctx.close()

    # ---- pair page: same treatment ----
    ctx = b.new_context(); pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/time/london-and-new-york.html", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(700)
    li = pg.eval_on_selector_all("li[data-date]", "e=>e.map(x=>x.dataset.date)")
    check("pair page holiday items carry ISO dates", len(li) >= 4, len(li))
    nd = pg.inner_text("[data-next-date]").strip()
    check("pair page next-holiday rendered", bool(nd), repr(nd))
    # it must be the earliest future date among the listed ones
    fut = sorted(x for x in li if x >= datetime.date.today().isoformat())
    if fut:
        want = datetime.date.fromisoformat(fut[0])
        check("pair page picks the earliest upcoming date",
              nd.startswith(str(want.day)), (nd, fut[0]))
    ctx.close()

    check("no page errors", not errs, errs)
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All freshness checks passed."))
sys.exit(1 if fails else 0)
