"""Clock-format consistency checks.

The planner shows a time in five places - the city rows, the result heading,
the meeting summary, each timeline row label, and the timeline axis. Before
this was fixed they did not agree: `hour:'numeric'` resolves to 12-hour under
`en` and 24-hour under `fr`, while the axis was static markup reading
"12 AM / 6 AM / 12 PM / 6 PM" no matter what. A French visitor saw 24-hour
times above a 12-hour axis.

Formats may differ between visitors. They must never differ within one screen,
and that is what this file checks.

Usage:  python -m http.server 8765     # from the repo root, in another shell
        python tests/clock_test.py
"""
import sys, re
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

MERIDIEM = re.compile(r"\b[AaPp]\.?\s?[Mm]\.?\b|\u202f?[AP]M")

def snapshot(pg):
    return pg.evaluate("""()=>({
        clock: state.clock,
        button: document.getElementById('clock-toggle').textContent.trim(),
        cityClocks: [...document.querySelectorAll('.city-clock strong')].map(e=>e.textContent),
        title: document.getElementById('results-title').textContent,
        summary: document.getElementById('meeting-summary').textContent,
        timeline: [...document.querySelectorAll('.timeline-city span')].map(e=>e.textContent),
        axis: [...document.querySelectorAll('#timeline-axis span')].map(e=>e.textContent)
    })""")

def all_times(s):
    """Every rendered time on the screen, as one list."""
    out = list(s["cityClocks"]) + list(s["axis"]) + [s["title"], s["summary"]]
    out += list(s["timeline"])
    return [x for x in out if x and x.strip()]

def setup(pg):
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1200)
    pg.fill("#city-search", "")
    pg.locator("#city-search").press_sequentially("Delhi", delay=35)
    pg.wait_for_timeout(1600)
    pg.click("#add-city"); pg.keyboard.press("Escape")
    pg.wait_for_timeout(1800)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []

    for locale, expect_default in (("en-US", "12"), ("fr-FR", "24"), ("de-DE", "24")):
        ctx = b.new_context(locale=locale, timezone_id="America/New_York")
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        setup(pg)
        s = snapshot(pg)

        check(f"{locale}: default follows the visitor's own locale",
              s["clock"] == expect_default, (s["clock"], expect_default))
        check(f"{locale}: the toggle shows the active format",
              s["button"] == expect_default + "h", s["button"])
        check(f"{locale}: the axis is rendered, not left empty", len(s["axis"]) == 5, s["axis"])

        times = all_times(s)
        marked = [x for x in times if MERIDIEM.search(x)]
        if s["clock"] == "12":
            # every time must carry a meridiem - except axis ticks, where the
            # hour alone is unambiguous and shorter
            body = list(s["cityClocks"]) + [s["title"], s["summary"]] + list(s["timeline"])
            missing = [x for x in body if not MERIDIEM.search(x)]
            check(f"{locale}: every 12-hour time carries AM/PM", not missing, missing)
            check(f"{locale}: no 24-hour time leaks in",
                  not [x for x in body if re.search(r"\b(1[3-9]|2[0-3]):\d\d", x)], body)
        else:
            check(f"{locale}: no AM/PM anywhere in 24-hour mode", not marked, marked)
            padded = [x for x in s["cityClocks"] + s["axis"] if not re.match(r"^\d\d:", x.strip())]
            check(f"{locale}: 24-hour times are padded to hh:mm", not padded, padded)

        # ---- the toggle flips every surface together ----
        pg.click("#clock-toggle"); pg.wait_for_timeout(600)
        s2 = snapshot(pg)
        check(f"{locale}: the toggle switches the format",
              s2["clock"] != s["clock"], (s["clock"], s2["clock"]))
        check(f"{locale}: the button label follows", s2["button"] == s2["clock"] + "h", s2["button"])

        t2 = all_times(s2)
        marked2 = [x for x in t2 if MERIDIEM.search(x)]
        if s2["clock"] == "24":
            check(f"{locale}: after toggling to 24h nothing still shows AM/PM", not marked2, marked2)
            check(f"{locale}: the axis followed to 24h",
                  all(re.match(r"^\d\d:\d\d$", x.strip()) for x in s2["axis"]), s2["axis"])
        else:
            check(f"{locale}: after toggling to 12h the axis followed",
                  all(MERIDIEM.search(x) for x in s2["axis"]), s2["axis"])
            check(f"{locale}: no 24-hour time survives the switch",
                  not [x for x in s2["cityClocks"] if re.search(r"\b(1[3-9]|2[0-3]):", x)],
                  s2["cityClocks"])

        # ---- the choice survives a reload; the locale default does not override it ----
        pg.reload(wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(1800)
        s3 = snapshot(pg)
        check(f"{locale}: the chosen format is remembered", s3["clock"] == s2["clock"],
              (s2["clock"], s3["clock"]))
        ctx.close()

    # ---- the header stays intact on a phone ----
    ctx = b.new_context(locale="en-US", timezone_id="America/New_York",
                        viewport={"width": 375, "height": 812})
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1000)
    box = pg.evaluate("""()=>{const c=document.getElementById('clock-toggle');
        const h=c.closest('.header-actions'); const r=c.getBoundingClientRect();
        return {w:r.width,h:r.height,headerOverflow:h.scrollWidth>h.clientWidth+1,
                bodyOverflow:document.documentElement.scrollWidth>window.innerWidth+1};}""")
    check("the toggle keeps a 44px tap target on mobile",
          box["w"] >= 40 and box["h"] >= 40, box)
    check("the header does not overflow on a phone", not box["headerOverflow"], box)
    check("the page does not scroll sideways on a phone", not box["bodyOverflow"], box)
    ctx.close()

    check("no page errors", not errs, errs[:3])
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All clock checks passed."))
sys.exit(1 if fails else 0)
