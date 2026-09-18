"""Per-country weekend checks.

The planner hardcoded Saturday+Sunday in three places -- the working-hours test,
the slot scorer and the weekend notices -- and gen_holiday_pages did the same in
classify(). That is wrong for 28 countries. For Saudi Arabia and Qatar, the two
countries sending the most impressions, it showed Friday as a working day and
Sunday as a weekend: exactly inverted, on the one question the site exists to
answer.

The data is per country AND per year, which is why the UAE must come out as
Sat+Sun (it moved in 2022) while its neighbours stay Fri+Sat. A test that only
checked "Gulf = Fri+Sat" would pass while being wrong.

Usage:  python -m http.server 8765     # from the repo root, in another shell
        python tests/weekend_test.py
"""
import sys, os, re
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

# 2026-09-18 is a Friday, 2026-09-19 a Saturday, 2026-09-20 a Sunday
FRI, SAT, SUN = "2026-09-18", "2026-09-19", "2026-09-20"
def city(name, zone, cc, country):
    return f"{name}%7C{zone.replace('/', '%2F')}%7C{cc}%7C%7C{country.replace(' ', '%20')}"
RIYADH = city("Riyadh", "Asia/Riyadh", "SA", "Saudi Arabia")
LONDON = city("London", "Europe/London", "GB", "United Kingdom")
DUBAI  = city("Dubai", "Asia/Dubai", "AE", "United Arab Emirates")
HK     = city("Hong Kong", "Asia/Hong_Kong", "HK", "Hong Kong")

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(locale="en-US", timezone_id="Europe/London")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))

    def load(cities, day):
        pg.goto(f"{BASE}/?city={'&city='.join(cities)}&date={day}",
                wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(1600)
        # the weekday rule only: isWorking() also applies the 9-5 window, and the
        # slot is anchored to the first city, so 10:00 in Riyadh is 08:00 in London
        return pg.evaluate("""()=>{const out={};
            state.selected.forEach(c=>{
              const p=localParts(slotDate(20), c.zone);
              out[c.countryCode]=!isWeekendDay(p.weekday, c.countryCode);});
            out._notices=[...document.querySelectorAll('#holiday-notices *')]
              .map(e=>e.textContent.trim()).filter(t=>t.length>3);
            return out;}""")

    # ---- the map itself ----
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(900)
    m = pg.evaluate("()=>({n:Object.keys(WEEKEND_BY_CC).length, sa:WEEKEND_BY_CC.SA,"
                    " ae:WEEKEND_BY_CC.AE, hk:WEEKEND_BY_CC.HK, gb:WEEKEND_BY_CC.GB,"
                    " dflt:weekendDays('GB')})")
    check("the weekend map is embedded", 20 <= m["n"] <= 45, m["n"])
    check("Saudi Arabia is Fri+Sat", m["sa"] == ["Fri", "Sat"], m["sa"])
    check("Hong Kong is Sunday only", m["hk"] == ["Sun"], m["hk"])
    # the point of per-country data: the UAE moved to Sat+Sun in 2022
    check("the UAE is NOT lumped in with its neighbours", m["ae"] is None, m["ae"])
    check("countries absent from the map default to Sat+Sun",
          m["gb"] is None and m["dflt"] == ["Sat", "Sun"], m)

    # ---- Friday: a working day in London, the weekend in Riyadh ----
    r = load([RIYADH, LONDON], FRI)
    check("Friday is the weekend in Riyadh", r["SA"] is False, r)
    check("Friday is a working day in London", r["GB"] is True, r)
    check("the notice says Riyadh is on its weekend",
          any("Riyadh" in n and "Weekend" in n for n in r["_notices"]), r["_notices"])

    # ---- Sunday: the inverse ----
    r = load([RIYADH, LONDON], SUN)
    check("Sunday is a working day in Riyadh", r["SA"] is True, r)
    check("Sunday is the weekend in London", r["GB"] is False, r)
    check("the notice says Riyadh is working",
          any("Riyadh" in n and "Working" in n for n in r["_notices"]), r["_notices"])

    # ---- Saturday is the weekend in both, for different reasons ----
    r = load([RIYADH, LONDON], SAT)
    check("Saturday is the weekend in both", r["SA"] is False and r["GB"] is False, r)

    # ---- the UAE and Hong Kong prove it is per-country, not per-region ----
    r = load([DUBAI, HK], FRI)
    check("Friday is a working day in Dubai", r["AE"] is True, r)
    check("Friday is a working day in Hong Kong", r["HK"] is True, r)
    r = load([DUBAI, HK], SAT)
    check("Saturday is the weekend in Dubai", r["AE"] is False, r)
    check("Saturday is a working day in Hong Kong", r["HK"] is True, r)

    check("no page errors", not errs, errs[:3])
    b.close()

# ---- the generated holiday pages use the same rule ----
def tags_by_weekday(path):
    h = open(os.path.join(REPO, path), encoding="utf-8").read()
    # national tables only: the regional section has a "where" column instead of
    # weekend tags, so including it reports every weekday as untagged
    block = ""
    for m in re.finditer(r'<div class="holiday-table">', h):
        end = h.find("</div></section>", m.end())
        block += h[m.end():end if end != -1 else len(h)]
    out = {}
    for day, rest in re.findall(r'<span class="when">(\w+)[^<]*</span>(.*?)(?=<div data-date|$)',
                                block, re.S):
        tag = ("weekend" if "falls on a weekend" in rest
               else "long" if "long weekend likely" in rest else "none")
        out.setdefault(day, set()).add(tag)
    return out

sa, gb = tags_by_weekday("holidays/saudi-arabia.html"), tags_by_weekday("holidays/united-kingdom.html")
check("Saudi Friday holidays read 'falls on a weekend'", sa.get("Friday") == {"weekend"}, sa.get("Friday"))
check("Saudi Sunday holidays do NOT read as weekend", "weekend" not in (sa.get("Sunday") or set()), sa.get("Sunday"))
check("Saudi Thursday holidays read 'long weekend likely'", sa.get("Thursday") == {"long"}, sa.get("Thursday"))
check("UK Sunday holidays still read as weekend", gb.get("Sunday") == {"weekend"}, gb.get("Sunday"))
check("UK Friday holidays still read 'long weekend likely'", gb.get("Friday") == {"long"}, gb.get("Friday"))

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All weekend checks passed."))
sys.exit(1 if fails else 0)
