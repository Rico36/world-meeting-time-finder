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
    check("Saturday invites the visitor to choose, rather than claiming a verdict",
          s["label"] == "Find Best Compromise", s["label"])
    check("Saturday explains why without claiming a best",
          "No hour on this day" in s["note"] and "closest match" not in s["note"], s["note"])

    # ---- dragging the time makes it the visitor's, not the tool's ----
    set_day(pg, FRIDAY)
    before = snap(pg)
    pg.click("#later"); pg.wait_for_timeout(500)
    after = snap(pg)
    check("stepping the time marks it visitor-chosen", after["picked"] is True)
    # The label now reflects one fact only - is everyone inside working hours -
    # so a nudge that stays inside the window must keep saying so. It must never
    # become a claim about who chose the time.
    check("a nudge inside the window keeps the factual label",
          after["label"] == "Inside working hours for everyone", after["label"])
    check("the slot actually moved", after["slot"] == before["slot"] + 1, (before["slot"], after["slot"]))

    # drag far outside working hours: it is flagged, not judged
    pg.evaluate("()=>{document.getElementById('time-slider').value=2;"
                "document.getElementById('time-slider').dispatchEvent(new Event('input'));}")
    pg.wait_for_timeout(500)
    s = snap(pg)
    check("a 1 AM pick is not dressed up as a recommendation",
          s["label"] == "Find Best Compromise", s)
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
    check("a shared slot is honoured", s["picked"] is True and s["slot"] == 4, s)

    # A link naming only cities must still get a computed baseline. Number(null)
    # is 0 and 0 is a valid slot, so the unguarded check turned every such link
    # into a midnight meeting - London and Paris, which overlap almost entirely,
    # opened at 12 AM.
    pg.goto(f"{BASE}/?city=London%7CEurope%2FLondon%7CGB%7C%7CUnited%20Kingdom"
            f"&city=Paris%7CEurope%2FParis%7CFR%7C%7CFrance&date={FRIDAY}",
            wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1800)
    s = snap(pg)
    check("a link without a slot is not treated as a midnight pick", s["picked"] is False, s)
    check("a link without a slot gets a computed time",
          s["label"] == "Inside working hours for everyone", s)
    lon = first_hour(s["summary"])
    check("London lands in its working day, not at midnight",
          lon is not None and 9 <= lon <= 16, (lon, s["summary"]))

    # ---- the calendar button beside the day arrows ----
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(1100)
    add_city(pg, "London"); pg.wait_for_timeout(1200)
    cal = pg.evaluate("""()=>{const b=document.getElementById('pick-day');
        if(!b) return null; const r=b.getBoundingClientRect();
        const st=b.closest('.day-stepper').getBoundingClientRect();
        return {h:r.height, centered:Math.abs((r.left+r.right)/2-(st.left+st.right)/2)<4,
                icon:!!b.querySelector('svg.cal-icon'), label:b.getAttribute('aria-label')||''};}""")
    check("the day stepper has a calendar button", cal is not None)
    check("it carries a calendar icon", cal and cal["icon"], cal)
    check("it sits between the arrows", cal and cal["centered"], cal)
    check("it is a real tap target", cal and cal["h"] >= 40, cal)
    check("it is labelled for screen readers", cal and "date" in cal["label"].lower(), cal)
    before = pg.input_value("#meeting-date")
    pg.click("#pick-day"); pg.wait_for_timeout(600)
    check("opening the picker does not change the date on its own",
          pg.input_value("#meeting-date") == before)

    check("no page errors", not errs, errs[:3])
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All slot checks passed."))
sys.exit(1 if fails else 0)
