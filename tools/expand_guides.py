import json, shutil
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
M = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CITIES = [("Los Angeles","America/Los_Angeles"),("New York","America/New_York"),
 ("Mexico City","America/Mexico_City"),("S\u00e3o Paulo","America/Sao_Paulo"),
 ("Santiago","America/Santiago"),("London","Europe/London"),("Berlin","Europe/Berlin"),
 ("Cairo","Africa/Cairo"),("Johannesburg","Africa/Johannesburg"),("Dubai","Asia/Dubai"),
 ("Mumbai","Asia/Kolkata"),("Singapore","Asia/Singapore"),("Tokyo","Asia/Tokyo"),
 ("Sydney","Australia/Sydney"),("Auckland","Pacific/Auckland")]

def trans(tz, year=YEAR):
    z = ZoneInfo(tz); d = datetime(year,1,1,12)
    prev = d.replace(tzinfo=z).utcoffset(); out = []
    while d < datetime(year+1,1,1,12):
        d += timedelta(days=1)
        cur = d.replace(tzinfo=z).utcoffset()
        if cur != prev:
            out.append(d.date()); prev = cur
    return out

dst_list = []
for name, tz in CITIES:
    t = trans(tz)
    if t:
        dst_list.append(name + " \u2014 clocks change on " +
                        " and ".join("%d %s" % (d.day, M[d.month-1]) for d in t) + ".")
    else:
        dst_list.append(name + " \u2014 no clock change at any point in %d." % YEAR)

def fmt(d):
    return "%d %s" % (d.day, ["January","February","March","April","May","June","July",
                              "August","September","October","November","December"][d.month-1])

# The converter guide names the US and European transition dates in prose, so they
# are computed here too rather than written by hand -- otherwise a December re-run
# produces a fresh table sitting next to a stale paragraph.
_us = trans("America/New_York"); _eu = trans("Europe/London")
US_SPRING, US_AUTUMN = fmt(_us[0]), fmt(_us[1])
EU_SPRING, EU_AUTUMN = fmt(_eu[0]), fmt(_eu[1])
US_SPRING_SHORT = "%d" % _us[0].day
EU_SPRING_SHORT = fmt(_eu[0])

RS = "\u2019"   # right single quote
LD = "\u201c"   # left double quote
RD = "\u201d"   # right double quote
EM = "\u2014"   # em dash

REF = {
"converter": [
 ["The three weeks each year when the gap changes",
  "North America and Europe do not change their clocks on the same day, so the difference between "
  "them shifts twice a year for about three weeks at a time. In %d the United States moves on "
  "%s and %s, while the United Kingdom and most of Europe move on %s and %s. London is normally "
  "five hours ahead of New York, but between %s and %s, and again between %s and %s, it is only "
  "four. A recurring call that felt comfortable in February can land an hour early in the middle "
  "of March without anyone having touched the invitation."
  % (YEAR, US_SPRING, US_AUTUMN, EU_SPRING, EU_AUTUMN,
     US_SPRING_SHORT, EU_SPRING_SHORT, EU_AUTUMN, US_AUTUMN)],
 ["Why time-zone abbreviations are unreliable",
  ["CST is used for United States Central Standard Time, China Standard Time and Cuba Standard Time.",
   "IST is used for India Standard Time, Irish Standard Time and Israel Standard Time.",
   "EST and EDT are an hour apart, and which one is correct depends entirely on the date.",
   "BST means British Summer Time in London and Bangladesh Standard Time in Dhaka.",
   "A city name together with a date is never ambiguous; an abbreviation frequently is."]],
 ["Converting a meeting that repeats",
  "Choose one city as the anchor " + EM + " usually where the meeting owner sits " + EM +
  " and keep that local time fixed. Everyone else" + RS + "s local time will then move by an hour "
  "whenever their own region changes clocks. That is the real trade-off: either the anchor city "
  "stays stable and the others drift, or everyone else stays stable and the anchor moves. Decide "
  "which before the first invitation goes out, and re-check the series in March, April, September "
  "and October, when most of the world" + RS + "s transitions fall."],
 ["A worked example across the March transition",
  "A one-hour call is set for 9:00 AM in New York. On 1 March that is 2:00 PM in London and "
  "7:30 PM in Mumbai. On 15 March, after the United States has moved its clocks but Europe has "
  "not, the same 9:00 AM in New York becomes 1:00 PM in London, and Mumbai shifts to 6:30 PM. By "
  "1 April, once Europe has moved as well, London is back to 2:00 PM. India never changed "
  "anything " + EM + " Mumbai moved because New York did."]],
"planner": [
 ["Rotate the burden on recurring calls",
  "Once a team spans more than about eight hours, someone is always outside normal working hours. "
  "A fixed weekly time means the same person absorbs that cost every week, which is a quiet and "
  "persistent source of resentment on distributed teams. Rotating the slot " + EM + " early for "
  "the Americas one month, early for Asia-Pacific the next " + EM + " spreads it. Write the "
  "rotation into the calendar invitation itself, so it is visible rather than remembered and a "
  "new joiner can see the arrangement is deliberate."],
 ["Working weeks are not the same everywhere",
  ["Several Gulf states, including the United Arab Emirates, Saudi Arabia, Qatar and Kuwait, work "
   "Sunday to Thursday, so a Friday meeting excludes them entirely.",
   "Friday around midday is commonly reserved for prayer across much of the Muslim world.",
   "Israel also works Sunday to Thursday, with Friday a short day.",
   "France, Italy and Spain thin out sharply through August, and Japan does the same during "
   "Golden Week in late April and early May.",
   "Lunch in Spain and much of Latin America falls later than the noon-to-one that most "
   "scheduling tools quietly assume."]],
 ["When there is genuinely no overlap",
  "Some pairings have no shared working hours at all. California and India sit close to twelve "
  "hours apart, and no hour of the day suits both sides. The realistic options are worth naming "
  "plainly: rotate the inconvenience between the two regions, shorten the call so the cost is "
  "smaller, split it into two regional calls joined by a written handoff, or drop the meeting and "
  "move the decision into a document. A planner that offers the least-bad hour is still telling "
  "you something useful, but the honest answer is sometimes that a live meeting is the wrong "
  "format for this particular group."],
 ["Write an invitation that survives",
  ["Give the date, the city and the local time together: " + LD + "Tuesday 14 April, 9:00 AM New "
   "York" + RD + " leaves nothing to interpret.",
   "Send a calendar invitation with a real time zone attached, so each participant" + RS + "s own "
   "client performs the conversion.",
   "Avoid writing " + LD + "EST" + RD + " in summer " + EM + " the correct abbreviation is then "
   "EDT, and the two are an hour apart.",
   "State the finish time as well as the start, so nobody discovers the overrun only once it "
   "happens.",
   "For a recurring series, say which city is the anchor and warn that the others will drift "
   "around it."]]],
"dst": [
 ["Clock changes in %d for major business hubs" % YEAR, dst_list],
 ["Places that do not change their clocks at all",
  "Much of Asia, Africa and the Middle East keeps a single offset all year: India, Singapore, "
  "Japan, the United Arab Emirates, Nigeria and South Africa never move. Mexico abolished "
  "daylight saving nationwide in 2022, though border cities such as Tijuana still follow the "
  "United States schedule. Within the United States, Arizona does not change its clocks " + EM +
  " except the Navajo Nation, which does. Queensland and Western Australia stay fixed while the "
  "rest of Australia moves. These mixed pairings cause the most confusion, because one side of "
  "the call shifts and the other simply does not."],
 ["Holidays that move from year to year",
  ["Lunar New Year falls between late January and late February and closes offices across China, "
   "Singapore and much of South-East Asia for a week or more.",
   "Eid al-Fitr and Eid al-Adha follow the lunar calendar and arrive roughly eleven days earlier "
   "each year.",
   "Holidays tied to Easter " + EM + " Good Friday, Easter Monday, Ascension, Whit Monday " + EM +
   " move with it.",
   "Many countries add a substitute day when a fixed-date holiday falls on a weekend.",
   "Some bridge a midweek holiday to the nearest weekend, closing offices for several days "
   "either side."]],
 ["What a national holiday check cannot tell you",
  "A country-level calendar is the right place to start and the wrong place to stop. It cannot "
  "know about regional holidays that apply in one state, province or canton but not the next; "
  "company shutdowns between Christmas and New Year; school holidays that quietly change when "
  "parents are available; or ordinary personal leave. Treat a flag as a prompt to ask rather than "
  "as an answer. Confirm with the person you are inviting, and remember that a clear public "
  "calendar is not the same thing as a free colleague."]],
}

os.makedirs(os.path.join(HERE, ".cache"), exist_ok=True)
path = REPO + "/guides.js"
shutil.copyfile(path, os.path.join(HERE, ".cache", "guides.js.bak"))  # git holds the real history
s = open(path, encoding="utf-8").read()

payload = {k: {"en": v} for k, v in REF.items()}
js = "const guideReference = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n\n"

# re-running must replace, not duplicate, the generated block
TERM = "\n};\n\n"
start = s.find("const guideReference = ")
if start != -1:
    end = s.find(TERM, start)
    assert end != -1, "could not find the end of the existing guideReference block"
    s = s[:start] + s[end + len(TERM):]

anchor = "function renderGuide(language){"
assert anchor in s, "renderGuide not found"
s = s.replace(anchor, js + anchor, 1)

old = "...(guideDeepening[key]?.[lang]||[])]};"
new = "...(guideDeepening[key]?.[lang]||[]),...(guideReference[key]?.[lang]||[])]};"
if new not in s:
    assert old in s, "assembly line not found"
    s = s.replace(old, new, 1)

open(path, "w", encoding="utf-8").write(s)
words = sum(len(str(c).split()) for g in REF.values() for h, c in g)
print("guides.js patched, new size", len(s))
print("new english words added:", words)
for k, v in REF.items():
    print("  %-10s +%d sections" % (k, len(v)))
