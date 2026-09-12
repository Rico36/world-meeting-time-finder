"""Day/night map checks. Usage: python map_test.py [base]"""
import sys, math
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

def py_subsolar(dt):
    jd = dt.replace(tzinfo=timezone.utc).timestamp() / 86400.0 + 2440587.5
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    dec = math.degrees(math.asin(math.sin(eps) * math.sin(lam)))
    ra_h = (math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))) / 15) % 24
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    lon = ((-15 * ((gmst - ra_h) % 24) + 180) % 360) - 180
    return dec, lon

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(timezone_id="America/New_York", locale="en-US")
    pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))

    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(2200)
    # shows from the FIRST city on purpose: gating it behind a second city meant a
    # first-time visitor never saw the only visual on the page
    check("map visible with just the detected city",
          not pg.eval_on_selector("#world-map-figure", "e=>e.hidden"))

    # add a second city
    pg.fill("#city-search", ""); pg.locator("#city-search").press_sequentially("Tokyo", delay=35)
    pg.wait_for_timeout(1600); pg.click("#add-city"); pg.keyboard.press("Escape")
    pg.wait_for_timeout(2500)

    check("map visible with two cities",
          not pg.eval_on_selector("#world-map-figure", "e=>e.hidden"))
    land = pg.eval_on_selector_all("#world-map .land path", "e=>e.length")
    check("land outlines drawn", land > 50, land)
    check("exactly one night polygon",
          pg.eval_on_selector_all("#world-map .night", "e=>e.length") == 1)
    pins = pg.eval_on_selector_all("#world-map .pin", "e=>e.length")
    check("a pin per selected city", pins == 2, pins)
    labels = pg.eval_on_selector_all("#world-map .pin-label", "e=>e.map(x=>x.textContent)")
    check("labels name the cities", "Tokyo" in labels, labels)
    check("no time zone boundaries drawn",
          pg.eval_on_selector_all("#world-map .zone,#world-map [class*=boundary]", "e=>e.length") == 0)

    # the JS subsolar math must agree with the independently-computed Python one
    js = pg.evaluate("()=>{const s=subsolarPoint(new Date());return [s.dec,s.lon];}")
    pdec, plon = py_subsolar(datetime.now(timezone.utc))
    check("declination matches Python within 0.1 deg", abs(js[0] - pdec) < 0.1, (js[0], pdec))
    dlon = abs(((js[1] - plon + 180) % 360) - 180)
    check("subsolar longitude matches within 0.3 deg", dlon < 0.3, (js[1], plon, dlon))

    # a pin's x position must match its longitude in the 0-360 viewBox
    pin_x = pg.evaluate("()=>{const c=document.querySelectorAll('#world-map .pin');"
                        "return [...c].map(p=>parseFloat(p.getAttribute('cx')));}")
    check("pins inside the viewBox", all(0 <= x <= 360 for x in pin_x), pin_x)
    # Tokyo is ~139.7E -> x ~319.7
    check("Tokyo pin near its true longitude",
          any(abs(x - 319.7) < 3 for x in pin_x), pin_x)

    check("no page errors", not errs, errs)
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All map checks passed."))
sys.exit(1 if fails else 0)
