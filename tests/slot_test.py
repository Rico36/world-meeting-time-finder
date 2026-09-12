"""Slot selection and result labelling.

Two defects this file exists to prevent coming back:

  * The result heading said "Best compromise" for whatever slot the visitor had
    dragged to, crediting their own choice to the tool.
  * findBestSlot() scored slots by counting how many city-half-hours fell inside
    9-5. That count is a boolean, so it could not rank 6:30 AM above 3 AM, and
    when nothing scored at all -- every weekend, and any pairing with no overlap
    -- the tie went to the lowest index. The tool proposed a MIDNIGHT meeting
    for New York and London every Saturday.

Usage:  python -m http.server 8765     # from the repo root, in another shell
        python tests/slot_test.py
"""
import sys, re
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

FRIDAY, SATURDAY = "2026-09-18", "2026-09-19"

def add_city(pg, name):
    pg.fill("#city-search", "")
    pg.locator("#city-search").press_sequentially(name, delay=30)
    pg.wait_for_timeout(1500)
    pg.click("#add-city"); pg.keyboard.press("Escape"); pg.wait_for_timeout(900)

def set_day(pg, iso):
    pg.fill("#meeting-date", iso); pg.dispatch_event("#meeting-date", "change")
    pg.wait_for_timeout(1200)

def snap(pg):
    return pg.evaluate("""()=>({label:document.getElementById('result-label').textContent.trim(),
      summary:document.getElementById('meeting-summary').textContent.trim(),
      note:(document.getElementById('compromise-note').hidden?'':document.getElementById('compromise-note').textContent.trim()),
      picked:state.userPicked, slot:state.slot})""")

def first_hour(summary):
    """The reference city's local hour, as a float.

    Read positionally, not by city name: the reference row is whatever the
    visitor's own geolocation resolves to, so against production it is
    "Alpharetta" rather than the "New York" a timezone-only guess gives. Matching
    on the name passed locally and failed on the live site.
    """
    m = re.match(r"\s*(\d{1,2}):(\d\d)(?:\s*(AM|PM))?", summary)
    if not m: return None
    h = int(m.group(1))
    if m.group(3):                       # 12-hour
        h = h % 12 + (12 if m.group(3) == "PM" else 0)
    return h + int(m.group(2)) / 60

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []

    # ---- a pair with a real overlap must find it ----
    ctx = b.new_context(locale="en-US", timezone_id="America/New_York")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(1100)
    add_city(pg, "London")
    set_day(pg, FRIDAY)
    s = snap(pg)
    check("weekday overlap is found", s["label"] == "Inside working hours for everyone", s)
    check("no note when everyone is inside hours", s["note"] == "", s["note"])
    check("the computed slot is not attributed to the visitor", s["picked"] is False)
    ny = first_hour(s["summary"])
    check("the reference city lands in its working day", ny is not None and 9 <= ny <= 16, (ny, s["summary"]))

    # ---- THE REGRESSION: a weekend must not collapse to midnight ----
    set_day(pg, SATURDAY)
    s = snap(pg)
    ny = first_hour(s["summary"])
    check("Saturday does not propose a midnight meeting",
          ny is not None and not (0 <= ny < 5), (ny, s["summary"]))
    check("Saturday still proposes a civilised hour",
          ny is not None and 7 <= ny <= 19, (ny, s["summary"]))
    check("Saturday is labelled as closest, not as a fit",
          s["label"] == "Closest to working hours", s["label"])
    check("Saturday explains why", "closest" in s["note"].lower(), s["note"])

    # ---- dragging the time makes it the visitor's, not the tool's ----
    set_day(pg, FRIDAY)
    before = snap(pg)
    pg.click("#later"); pg.wait_for_timeout(500)
    after = snap(pg)
    check("stepping the time marks it visitor-chosen", after["picked"] is True)
    check("the heading stops claiming the tool chose it",
          after["label"] == "Selected time", after["label"])
    check("the slot actually moved", after["slot"] == before["slot"] + 1, (before["slot"], after["slot"]))

    # drag far outside working hours: it is flagged, not judged
    pg.evaluate("()=>{document.getElementById('time-slider').value=2;"
                "document.getElementById('time-slider').dispatchEvent(new Event('input'));}")
    pg.wait_for_timeout(500)
    s = snap(pg)
    check("a 1 AM pick is still labelled as the visitor's", s["label"] == "Selected time", s)
    check("it names who is outside working hours",
          "Outside normal working hours in" in s["note"], s["note"])
    check("it does not rule the choice out",
          "not ruled out" in s["note"] or "may still suit" in s["note"], s["note"])

    # ---- changing the date hands control back to the tool ----
    set_day(pg, FRIDAY)
    s = snap(pg)
    check("recalculating clears the visitor-chosen flag", s["picked"] is False, s)

    # ---- a shared link's time belongs to whoever shared it ----
    pg.goto(f"{BASE}/?city=London%7CEurope%2FLondon%7CGB%7C%7CUnited%20Kingdom"
            f"&city=Tokyo%7CAsia%2FTokyo%7CJP%7C%7CJapan&slot=4",
            wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1600)
    s = snap(pg)
    check("a shared slot is not presented as computed",
          s["label"] == "Selected time" and s["picked"] is True, s)

    check("no page errors", not errs, errs[:3])
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All slot checks passed."))
sys.exit(1 if fails else 0)
