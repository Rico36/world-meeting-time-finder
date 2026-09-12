"""Visitor-city detection checks.

Rebuilt Sep 2026 after the original scratchpad copy was lost. Covers the three
things that have actually broken here before:

  * Chromium reports LEGACY IANA zone names (Asia/Calcutta, Europe/Kiev) while
    the site's data uses current ones. Without ZONE_ALIASES, India silently
    detected nothing.
  * The geo upgrade must never show a city name next to a time zone it does not
    belong to - a VPN or a wrong IP database is worse than the honest zone-only
    guess.
  * Re-detection is gated on "is a detected row present", NOT on a city count.
    Gating on `length < 2` meant a visitor with three saved cities never got
    their own city back. That is test L below, and it was reported from real
    use, not found by a test.

Usage:  python -m http.server 8765     # from the repo root, in another shell
        python tests/detect_test.py
"""
import sys, json
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

GEO = "https://findcommonhours-geo.ricky-freyre.workers.dev"

def geo_route(page, body, status=200):
    """Stand in for the Cloudflare geo Worker. Routed rather than live so the
    disagree/fail paths can be exercised at all - they cannot be provoked from
    a real edge response."""
    def handler(route):
        if body is None:
            route.abort()
        else:
            route.fulfill(status=status, content_type="application/json",
                          headers={"Access-Control-Allow-Origin": "*"},
                          body=json.dumps(body))
    page.route(GEO + "**", handler)

def rows(pg):
    return pg.eval_on_selector_all(
        "#city-list .city-row",
        "e=>e.map(r=>r.innerText.replace(/\\s+/g,' ').trim())")

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []

    # ---- A-E: a zone resolves to a city, in several shapes of data ----
    for zone, expect, label in (
        ("America/New_York",   None,        "US eastern zone"),
        ("Asia/Tokyo",         "Tokyo",     "seed-list city"),
        ("Europe/Lisbon",      None,        "COUNTRY_CITIES lookup"),
        ("Australia/Perth",    None,        "REGION_CITIES lookup"),
        ("Pacific/Auckland",   None,        "southern-hemisphere zone"),
    ):
        ctx = b.new_context(timezone_id=zone, locale="en-US")
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        geo_route(pg, None)            # geo unavailable: the zone guess must stand alone
        pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(1200)
        r = rows(pg)
        ok = len(r) == 1 and bool(r[0].strip())
        check(f"{label} ({zone}) detects a city", ok, r)
        if expect:
            check(f"{zone} resolves to {expect}", expect in r[0], r)
        ctx.close()

    # ---- F: legacy IANA names must not silently miss ----
    for legacy, current, country in (("Asia/Calcutta", "Asia/Kolkata", "India"),
                                     ("Europe/Kiev", "Europe/Kyiv", "Ukraine"),
                                     ("America/Buenos_Aires", "America/Argentina/Buenos_Aires", "Argentina")):
        ctx = b.new_context(timezone_id=legacy, locale="en-US")
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        geo_route(pg, None)
        pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(1200)
        r = rows(pg)
        check(f"legacy {legacy} still detects", len(r) == 1 and bool(r[0].strip()), r)
        check(f"canonicalZone maps {legacy} -> {current}",
              pg.evaluate(f"()=>canonicalZone({legacy!r})") == current)
        ctx.close()

    # ---- G: the detected row is never persisted ----
    ctx = b.new_context(timezone_id="Asia/Tokyo", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, None)
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1200)
    saved = pg.evaluate("()=>JSON.parse(localStorage.getItem('commonHoursCitiesV2')||'[]')")
    check("detected row is not written to localStorage",
          not any(c.get("detected") for c in saved), saved)
    ctx.close()

    # ---- H: geo upgrade applies when the zone agrees ----
    ctx = b.new_context(timezone_id="America/New_York", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, {"city": "Alpharetta", "region": "Georgia",
                   "countryCode": "US", "timezone": "America/New_York"})
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(2500)
    r = rows(pg)
    check("geo upgrades the displayed city when the zone agrees",
          "Alpharetta" in r[0], r)
    z = pg.evaluate("()=>state.selected[0].zone")
    check("the upgrade never changes the zone used for the maths",
          z == "America/New_York", z)
    ctx.close()

    # ---- I: geo DISAGREES -> keep the honest zone guess ----
    ctx = b.new_context(timezone_id="America/New_York", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, {"city": "Berlin", "region": "Berlin",
                   "countryCode": "DE", "timezone": "Europe/Berlin"})
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(2500)
    r = rows(pg)
    check("a VPN/wrong-IP city is rejected when its zone disagrees",
          "Berlin" not in r[0], r)
    ctx.close()

    # ---- J: geo fails or is slow -> the zone guess stands ----
    for body, label in ((None, "geo unreachable"), ({"nonsense": True}, "geo returns junk")):
        ctx = b.new_context(timezone_id="Asia/Tokyo", locale="en-US")
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        geo_route(pg, body)
        pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(2200)
        r = rows(pg)
        check(f"{label}: the zone-based guess still shows", len(r) == 1 and bool(r[0].strip()), r)
        ctx.close()

    # ---- K: a fully-specified shared link is not modified ----
    ctx = b.new_context(timezone_id="Asia/Tokyo", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, None)
    pg.goto(f"{BASE}/?city=London%7CEurope%2FLondon%7CGB%7C%7CUnited%20Kingdom"
            f"&city=Paris%7CEurope%2FParis%7CFR%7C%7CFrance",
            wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1800)
    r = rows(pg)
    check("a 2-city shared link gets no city injected", len(r) == 2, r)
    check("the shared link's own cities are intact",
          any("London" in x for x in r) and any("Paris" in x for x in r), r)
    ctx.close()

    # ---- K2: a ONE-city link does get the viewer's city as the partner ----
    ctx = b.new_context(timezone_id="Asia/Tokyo", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, None)
    pg.goto(f"{BASE}/?city=London%7CEurope%2FLondon%7CGB%7C%7CUnited%20Kingdom",
            wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1800)
    r = rows(pg)
    check("a 1-city link is completed with the viewer's city", len(r) == 2, r)
    ctx.close()

    # ---- L: the return-visit regression, reported from real use ----
    # Three cities saved (detected + two added). The restore strips the detected
    # one, leaving two - which a `length < 2` gate read as "enough" and so never
    # re-detected. The visitor's own city vanished permanently on that device.
    ctx = b.new_context(timezone_id="America/New_York", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, None)
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.evaluate("""()=>localStorage.setItem('commonHoursCitiesV2',JSON.stringify([
        {name:'Alpharetta',zone:'America/New_York',countryCode:'US',country:'United States',detected:true},
        {name:'London',zone:'Europe/London',countryCode:'GB',country:'United Kingdom'},
        {name:'Tokyo',zone:'Asia/Tokyo',countryCode:'JP',country:'Japan'}]))""")
    pg.reload(wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1800)
    r = rows(pg)
    check("all three cities return on a revisit", len(r) == 3, r)
    check("the detected city is among them and comes first",
          len(r) == 3 and any(x in r[0] for x in ("New York", "Alpharetta")), r)
    check("the saved cities survive too",
          any("London" in x for x in r) and any("Tokyo" in x for x in r), r)
    ctx.close()

    # ---- M: two saved real cities still get the visitor's city back ----
    ctx = b.new_context(timezone_id="Asia/Tokyo", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, None)
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.evaluate("""()=>localStorage.setItem('commonHoursCitiesV2',JSON.stringify([
        {name:'London',zone:'Europe/London',countryCode:'GB',country:'United Kingdom'},
        {name:'Paris',zone:'Europe/Paris',countryCode:'FR',country:'France'}]))""")
    pg.reload(wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1800)
    r = rows(pg)
    check("two saved cities plus the detected one = three rows", len(r) == 3, r)
    ctx.close()

    # ---- N: a visitor already in a saved city's zone is not duplicated ----
    ctx = b.new_context(timezone_id="Europe/London", locale="en-US")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    geo_route(pg, None)
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.evaluate("""()=>localStorage.setItem('commonHoursCitiesV2',JSON.stringify([
        {name:'London',zone:'Europe/London',countryCode:'GB',country:'United Kingdom'}]))""")
    pg.reload(wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1800)
    r = rows(pg)
    check("no duplicate row when the visitor's zone is already present",
          len(r) == 1, r)
    ctx.close()

    check("no page errors anywhere", not errs, errs[:3])
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All detection checks passed."))
sys.exit(1 if fails else 0)
