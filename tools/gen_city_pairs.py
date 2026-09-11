"""Generate static city-pair meeting-time pages under time/.

Why: AdSense flagged "Low value content" on 2026-09-11. The guides expanded on
6 Sep are substantive (850-980 words each) but the site still has only 5
pages -- Google's content review weighs the size of the indexable site as a
whole, not just words-per-page. This generates a page per pair of 21 major
global business hubs (210 unordered pairs), each with genuinely distinct,
computed content: the current typical offset and every date the gap shifts
across the year (reusing the same tzdata-walk approach as
tools/expand_guides.py), a synthetic 9am-5pm-local best-meeting-window, each
country's next few public holidays (via python-holidays, the same dependency
tools/gen_holidays.py already uses), and a link to the live planner
pre-filled with both cities via the URL scheme app.js already restores from
(?city=NAME|ZONE|CC|SUBDIVISION|COUNTRY).

Deliberately NOT a full cross-product of every city in the app's own
datasets -- an exhaustive cross-product produces obscure, low-intent pairs
that read as doorway pages (Google's "scaled content abuse" policy, a
separate and worse problem than low-value-content). All 21 cities here are
independently defensible major hubs; every pair is a plausible real search.

Usage:  python tools/gen_city_pairs.py
Requires: pip install holidays
Regenerate periodically: the "upcoming holidays" section decays as those
dates pass. See MAINTENANCE.md.
"""
import json, os, re, sys, unicodedata
from datetime import date, datetime, timedelta

try:
    import holidays
except ImportError:
    sys.exit("pip install holidays  (python-holidays) first")
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(REPO, "time")
TODAY = date.today()
YEARS = [TODAY.year, TODAY.year + 1]
SITE = "https://findcommonhours.com"
VERSION = None  # set from index.html's current asset version, see main()

M_LONG = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# name, country, ISO country code, IANA zone. All single-zone, real global
# business/tech hubs, chosen for genuine offset diversity (deliberately not
# two India cities, not Beijing+Shanghai -- same zone, would read as filler).
CITIES = [
    ("New York", "United States", "US", "America/New_York"),
    ("Los Angeles", "United States", "US", "America/Los_Angeles"),
    ("Chicago", "United States", "US", "America/Chicago"),
    ("Toronto", "Canada", "CA", "America/Toronto"),
    ("Mexico City", "Mexico", "MX", "America/Mexico_City"),
    ("São Paulo", "Brazil", "BR", "America/Sao_Paulo"),
    ("London", "United Kingdom", "GB", "Europe/London"),
    ("Paris", "France", "FR", "Europe/Paris"),
    ("Berlin", "Germany", "DE", "Europe/Berlin"),
    ("Madrid", "Spain", "ES", "Europe/Madrid"),
    ("Amsterdam", "Netherlands", "NL", "Europe/Amsterdam"),
    ("Dubai", "United Arab Emirates", "AE", "Asia/Dubai"),
    ("Johannesburg", "South Africa", "ZA", "Africa/Johannesburg"),
    ("Mumbai", "India", "IN", "Asia/Kolkata"),
    ("Singapore", "Singapore", "SG", "Asia/Singapore"),
    ("Hong Kong", "Hong Kong", "HK", "Asia/Hong_Kong"),
    ("Tokyo", "Japan", "JP", "Asia/Tokyo"),
    ("Seoul", "South Korea", "KR", "Asia/Seoul"),
    ("Jakarta", "Indonesia", "ID", "Asia/Jakarta"),
    ("Sydney", "Australia", "AU", "Australia/Sydney"),
    ("Auckland", "New Zealand", "NZ", "Pacific/Auckland"),
]

# ---------------------------------------------------------------- utilities

def slugify(name):
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", n.lower())).strip("-")

def fmt_offset(minutes):
    sign = "+" if minutes >= 0 else "-"
    m = abs(int(round(minutes)))
    h, mm = divmod(m, 60)
    return f"UTC{sign}{h}" + (f":{mm:02d}" if mm else "")

def fmt_date(d):
    return f"{d.day} {M_LONG[d.month-1]} {d.year}" if d.year != TODAY.year else f"{d.day} {M_LONG[d.month-1]}"

_holiday_cache = {}
def english_holidays(cc, years):
    key = (cc, tuple(years))
    if key in _holiday_cache:
        return _holiday_cache[key]
    result = None
    for lang in ("en_US", "en_GB", "en"):
        try:
            h = holidays.country_holidays(cc, years=years, language=lang)
            if any(re.search(r"[A-Za-z]", str(n)) for n in h.values()):
                result = h; break
        except Exception:
            continue
    if result is None:
        result = holidays.country_holidays(cc, years=years)
    _holiday_cache[key] = result
    return result

def upcoming_holidays(cc, limit=4):
    h = english_holidays(cc, YEARS)
    rows = sorted((d, re.sub(r"\s*\(estimated\)\s*", "", str(n), flags=re.I))
                  for d, n in h.items() if d >= TODAY)
    # de-duplicate same-date multi-name entries (e.g. "Eid al-Fitr" + "Eid al-Fitr Holiday")
    seen, out = set(), []
    for d, n in rows:
        if (d, n) in seen: continue
        seen.add((d, n)); out.append((d, n))
        if len(out) >= limit: break
    return out

def offset_minutes(zone, dt):
    return dt.replace(tzinfo=ZoneInfo(zone)).utcoffset().total_seconds() / 60

def gap_segments(zone_a, zone_b, year):
    """Walk the year day by day; return [(start_date, end_date, gap_minutes)]
    where gap = offset(b) - offset(a), merging consecutive equal-gap days."""
    d = datetime(year, 1, 1, 12)
    end = datetime(year, 12, 31, 12)
    segments = []
    cur_start, cur_gap = d, None
    while d <= end:
        gap = offset_minutes(zone_b, d) - offset_minutes(zone_a, d)
        if cur_gap is None:
            cur_gap = gap
        elif gap != cur_gap:
            segments.append((cur_start.date(), (d - timedelta(days=1)).date(), cur_gap))
            cur_start, cur_gap = d, gap
        d += timedelta(days=1)
    segments.append((cur_start.date(), end.date(), cur_gap))
    return segments

def typical_gap(segments):
    return max(segments, key=lambda s: (s[1] - s[0]).days)[2]

def gap_description(zone_a, zone_b):
    """Segments for the CURRENT year only (next year repeats the same pattern
    shifted by tzdata's own future-DST-date rules; showing one year keeps the
    prose readable and is regenerated periodically anyway)."""
    segs = gap_segments(zone_a, zone_b, TODAY.year)
    typical = typical_gap(segs)
    return segs, typical

def best_overlap(offset_a, offset_b):
    """Scan a's local clock in 30-min steps for a 1-hour slot landing inside
    9am-5pm local for BOTH cities. Returns (start_a_min, start_b_min) of the
    first such slot, or None if no standard-workday slot exists on either
    side (the pairing is more than 8h+1h apart in both directions)."""
    WORK_START, WORK_END = 9 * 60, 17 * 60
    for start_a in range(WORK_START, WORK_END - 60 + 1, 30):
        start_utc = (start_a - offset_a) % 1440
        start_b = (start_utc + offset_b) % 1440
        if WORK_START <= start_b <= WORK_END - 60:
            return start_a, start_b
    return None

def hm(total_min):
    h, m = divmod(int(total_min) % 1440, 60)
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ampm}" if m else f"{h12} {ampm}"

def best_compromise(offset_a, offset_b):
    """No standard-workday slot exists on both sides. Find the 1h slot that
    minimises how far outside 9-5 the WORSE-off city sits, scanning a's full
    day. Returns (start_a_min, start_b_min, worst_deviation_minutes)."""
    WORK_START, WORK_END = 9 * 60, 17 * 60
    def deviation(start):
        if start < WORK_START: return WORK_START - start
        if start > WORK_END - 60: return start - (WORK_END - 60)
        return 0
    best = None
    for start_a in range(0, 1440, 30):
        start_utc = (start_a - offset_a) % 1440
        start_b = (start_utc + offset_b) % 1440
        worst = max(deviation(start_a), deviation(start_b))
        if best is None or worst < best[2]:
            best = (start_a, start_b, worst)
    return best

# ------------------------------------------------------------------- markup

THEME_SCRIPT = ("document.documentElement.dataset.theme=localStorage.getItem('commonHoursTheme')"
    "||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');"
    "document.getElementById('theme-toggle').addEventListener('click',()=>{"
    "const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';"
    "document.documentElement.dataset.theme=theme;localStorage.setItem('commonHoursTheme',theme);});")

CF_BEACON = ('<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" '
             'data-cf-beacon=\'{"token":"1fa3e675ae4f4a6ca7406cb3d20594f0"}\'></script>')

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))

def header(depth):
    root = "../" * depth
    return (f'<header class="site-header"><a class="brand" href="{root}"><span class="brand-mark" '
            f'aria-hidden="true">☀</span><span>Common Hours</span></a><div class="header-actions">'
            f'<button class="icon-button" id="theme-toggle" type="button" aria-label="Switch color theme">◐</button>'
            f'</div></header>')

def footer(depth):
    root = "../" * depth
    return (f'<footer><span>Common Hours</span><span>A free world meeting time finder.</span>'
            f'<nav><a href="{root}">Meeting planner</a><a href="{root}privacy.html">Privacy</a>'
            f'<a href="{root}time/">All city pairs</a></nav></footer>')

def head(title, description, canonical_path, depth):
    root = "../" * depth
    return (f'<!doctype html>\n<html lang="en">\n<head>\n'
            f'  <meta charset="utf-8">\n'
            f'  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'  <meta name="description" content="{esc(description)}">\n'
            f'  <link rel="canonical" href="{SITE}/{canonical_path}">\n'
            f'  <meta property="og:type" content="article">'
            f'<meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(description)}">'
            f'<meta property="og:url" content="{SITE}/{canonical_path}">'
            f'<meta property="og:image" content="{SITE}/assets/og.jpg">\n'
            f'  <title>{esc(title)}</title>\n'
            f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?'
            f'client=ca-pub-4158152621897495" crossorigin="anonymous"></script>\n'
            f'  <link rel="stylesheet" href="{root}styles.css?v={VERSION}">\n'
            f'</head>')

def meeting_url(city_a, city_b):
    from urllib.parse import quote
    def enc(c):
        name, country, cc, zone = c
        return quote("|".join([name, zone, cc, "", country]), safe="")
    return f"{SITE}/?city={enc(city_a)}&city={enc(city_b)}"

def ordered(city_a, city_b):
    """Canonical city order for a pair: alphabetical by name. Used for the
    filename, the H1, the title and every internal link, so a pair has exactly
    one URL no matter which direction it is reached from. (Deriving the
    filename from one order and the links from another produced 934 broken
    links on the first run.) Sorts by SLUG, not name: "São Paulo" sorts after
    "Seoul" by name but before it as "sao-paulo", so sorting by name here
    would reintroduce the same class of mismatch."""
    return tuple(sorted([city_a, city_b], key=lambda c: slugify(c[0])))

def pair_slug(city_a, city_b):
    a, b = ordered(city_a, city_b)
    return f"{slugify(a[0])}-and-{slugify(b[0])}.html"

def related_pairs_for(city_a, city_b, all_cities, limit=6):
    """Other pairs sharing either city, alternating between the two so the
    block is not six links about whichever city happened to come first."""
    out, seen = [], set()
    others = [c for c in all_cities if c[0] not in (city_a[0], city_b[0])]
    for i, other in enumerate(others):
        for anchor in ((city_a, city_b) if i % 2 == 0 else (city_b, city_a)):
            slug = pair_slug(anchor, other)
            if slug in seen: continue
            seen.add(slug)
            a, b = ordered(anchor, other)
            out.append((f"{a[0]} and {b[0]}", slug))
            break
        if len(out) >= limit: break
    return out

def dst_line(name, zone):
    changes = []
    for yr in YEARS:
        d = datetime(yr, 1, 1, 12); prevo = offset_minutes(zone, d); out = []
        end = datetime(yr, 12, 31, 12)
        while d < end:
            d += timedelta(days=1)
            o = offset_minutes(zone, d)
            if o != prevo: out.append(d.date()); prevo = o
        if out: changes.append((yr, out))
    if not changes:
        return f"{name} does not change clocks."
    # the year already prefixes each group, so don't repeat it inside the dates
    parts = [f"{yr}: " + " and ".join(f"{d.day} {M_LONG[d.month-1]}" for d in out)
             for yr, out in changes]
    return f"{name} changes clocks — " + "; ".join(parts) + "."

def render_pair_page(city_a, city_b, all_cities):
    city_a, city_b = ordered(city_a, city_b)
    name_a, country_a, cc_a, zone_a = city_a
    name_b, country_b, cc_b, zone_b = city_b
    slug = pair_slug(city_a, city_b)
    title = f"{name_a} and {name_b} Time Zone — Meeting Planner | Common Hours"
    now = datetime.now()
    oa_now, ob_now = offset_minutes(zone_a, now), offset_minutes(zone_b, now)
    segs, typical = gap_description(zone_a, zone_b)
    ahead = name_b if typical > 0 else (name_a if typical < 0 else None)
    behind = name_a if typical > 0 else name_b
    gap_h = abs(typical) / 60
    gap_h_str = f"{gap_h:g}"
    description = (f"{name_a} and {name_b} are {gap_h_str} hours apart"
                    f"{' (' + ahead + ' ahead)' if ahead else ' (same local time)'}. "
                    f"See the best meeting time, upcoming holidays and clock-change dates for both.")

    if len(segs) == 1:
        gap_para = (f"The gap between {name_a} and {name_b} is constant all year: "
                    f"{'the two cities share the same local time' if typical == 0 else f'{ahead} is {gap_h_str} hours ahead of {behind}'}.")
        seg_list = ""
    else:
        gap_para = (f"For most of the year, "
                    f"{('the two cities share the same local time' if typical == 0 else ahead + ' is ' + gap_h_str + ' hours ahead of ' + behind)}. "
                    f"That gap does not hold all year — here is how it actually moves:")
        seg_list = '<ul class="guide-points">' + "".join(
            f"<li>{fmt_date(s)} to {fmt_date(e)}: "
            f"{'same local time' if g == 0 else (name_b if g > 0 else name_a) + ' is ' + f'{abs(g)/60:g}' + ' hours ahead of ' + (name_a if g > 0 else name_b)}</li>"
            for s, e, g in segs) + "</ul>"

    typ_seg = max(segs, key=lambda s: (s[1] - s[0]).days)
    mid = typ_seg[0] + (typ_seg[1] - typ_seg[0]) / 2
    mid_dt = datetime(mid.year, mid.month, mid.day, 12)
    oa, ob = offset_minutes(zone_a, mid_dt), offset_minutes(zone_b, mid_dt)
    ov = best_overlap(oa, ob)
    if ov:
        meeting_section = (f"<p>A one-hour meeting starting around <strong>{hm(ov[0])} in {name_a}</strong> "
                            f"lands at <strong>{hm(ov[1])} in {name_b}</strong> — inside normal working "
                            f"hours (9 AM–5 PM) for both sides.</p>")
    else:
        c = best_compromise(oa, ob)
        meeting_section = (f"<p>{name_a} and {name_b} do not share a normal working-hours window. "
                            f"The best compromise is <strong>{hm(c[0])} in {name_a}</strong> / "
                            f"<strong>{hm(c[1])} in {name_b}</strong> — still early or late for whoever "
                            f"is furthest from a normal day, which is the honest trade-off at this distance.</p>")

    dst_points = f'<ul class="guide-points"><li>{dst_line(name_a, zone_a)}</li><li>{dst_line(name_b, zone_b)}</li></ul>'

    hol_a, hol_b = upcoming_holidays(cc_a), upcoming_holidays(cc_b)
    def hol_list(name, rows):
        if not rows: return f"<li>No upcoming public holidays found for {name}.</li>"
        return "".join(f"<li>{fmt_date(d)} — {name}: {esc(n)}</li>" for d, n in rows)
    hol_points = f'<ul class="guide-points">{hol_list(name_a, hol_a)}{hol_list(name_b, hol_b)}</ul>'

    both_no_dst = (offset_minutes(zone_a, datetime(TODAY.year,1,1,12)) == offset_minutes(zone_a, datetime(TODAY.year,7,1,12))
                   and offset_minutes(zone_b, datetime(TODAY.year,1,1,12)) == offset_minutes(zone_b, datetime(TODAY.year,7,1,12)))
    a_no_dst = offset_minutes(zone_a, datetime(TODAY.year,1,1,12)) == offset_minutes(zone_a, datetime(TODAY.year,7,1,12))
    b_no_dst = offset_minutes(zone_b, datetime(TODAY.year,1,1,12)) == offset_minutes(zone_b, datetime(TODAY.year,7,1,12))
    if both_no_dst:
        dst_answer = f"Neither {name_a} nor {name_b} observes daylight saving time."
    elif a_no_dst:
        dst_answer = f"{name_a} does not observe daylight saving time; {name_b} does, so the gap shifts when {name_b} changes clocks."
    elif b_no_dst:
        dst_answer = f"{name_b} does not observe daylight saving time; {name_a} does, so the gap shifts when {name_a} changes clocks."
    else:
        dst_answer = f"Both cities observe daylight saving, but not always on the same dates — see the clock-change dates above."

    faq = [
        (f"What time is it in {name_b} when it is 9 AM in {name_a}?",
         # computed from the majority-of-year offsets, not "now" - this is a static
         # page, so claiming a live time would be wrong for most of the year
         f"For most of the year, 9 AM in {name_a} is {hm((9*60 - oa + ob) % 1440)} in {name_b} "
         f"({fmt_offset(oa)} against {fmt_offset(ob)})."
         + (f" During the weeks listed above when the gap shifts, it moves by an hour."
            if len(segs) > 1 else "")
         + f" Open the planner for a specific date."),
        (f"Does {name_a} or {name_b} change clocks first?", dst_answer),
        (f"Is there a public holiday in {name_a} or {name_b} soon?",
         (f"{name_a}: {hol_a[0][1]} on {fmt_date(hol_a[0][0])}. " if hol_a else f"No upcoming holiday found for {name_a}. ") +
         (f"{name_b}: {hol_b[0][1]} on {fmt_date(hol_b[0][0])}." if hol_b else f"No upcoming holiday found for {name_b}.")),
    ]
    faq_html = "".join(f"<h3>{esc(q)}</h3><p>{a}</p>" for q, a in faq)
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
                             for q, a in faq]}
    breadcrumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Common Hours", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "City time zone pairs", "item": SITE + "/time/"},
        {"@type": "ListItem", "position": 3, "name": f"{name_a} and {name_b}", "item": f"{SITE}/time/{slug}"},
    ]}

    related_list = "".join(f'<li><a href="{href}">{esc(label)}</a></li>'
                            for label, href in related_pairs_for(city_a, city_b, all_cities))

    body = (
        f'{head(title, description, "time/" + slug, 1)}\n<body>\n  {header(1)}\n'
        f'  <main class="content-page">\n'
        f'    <p class="eyebrow">Time zone meeting planner</p>\n'
        f'    <h1>{esc(name_a)} and {esc(name_b)}: plan a meeting across time zones</h1>\n'
        f'    <p class="lede">{esc(description)}</p>\n'
        f'    <a class="primary-button" href="{esc(meeting_url(city_a, city_b))}">Open in the free planner</a>\n'
        f'    <section><h2>The time difference</h2><p>{gap_para}</p>{seg_list}</section>\n'
        f'    <section><h2>Best time to meet</h2>{meeting_section}</section>\n'
        f'    <section><h2>Clock changes to plan around</h2>{dst_points}</section>\n'
        f'    <section><h2>Upcoming public holidays</h2>{hol_points}'
        f'<p>Holiday data uses country-level public calendars and may miss regional observances or '
        f'company shutdowns — confirm with your participant if the date matters.</p></section>\n'
        f'    <section><h2>Questions about {esc(name_a)} and {esc(name_b)}</h2>{faq_html}</section>\n'
        f'    <nav class="guide-nav" aria-label="Other city pairs"><h2>Related city pairs</h2><ul>{related_list}</ul></nav>\n'
        f'  </main>\n  {footer(1)}\n'
        f'  <script type="application/ld+json">{json.dumps(breadcrumb_ld)}</script>\n'
        f'  <script type="application/ld+json">{json.dumps(faq_ld)}</script>\n'
        f'  <script>{THEME_SCRIPT}</script>{CF_BEACON}\n'
        f'</body>\n</html>\n'
    )
    return slug, body

def render_city_hub(city, all_cities):
    name, country, cc, zone = city
    slug = f"{slugify(name)}.html"
    title = f"{name} Time Zone — Meeting Times With 20 Major Cities | Common Hours"
    description = (f"Compare {name} ({zone}) with 20 major business hubs: time differences, "
                    f"best meeting windows, clock changes and public holidays.")
    rows = []
    for other in all_cities:
        if other[0] == name: continue
        pair = pair_slug(city, other)
        segs, typical = gap_description(zone, other[3])
        gap_h = abs(typical) / 60
        if typical == 0:
            gap_txt = "same local time"
        else:
            gap_txt = f"{gap_h:g} h {'ahead' if typical > 0 else 'behind'}"
        rows.append(f'<li><a href="{pair}">{esc(name)} and {esc(other[0])}</a> — {esc(other[0])} is {gap_txt}</li>')
    body = (
        f'{head(title, description, "time/" + slug, 1)}\n<body>\n  {header(1)}\n'
        f'  <main class="content-page">\n'
        f'    <p class="eyebrow">Time zone meeting planner</p>\n'
        f'    <h1>Meeting times between {esc(name)} and other major cities</h1>\n'
        f'    <p class="lede">{esc(description)} {esc(dst_line(name, zone))}</p>\n'
        f'    <a class="primary-button" href="{SITE}/">Open the free planner</a>\n'
        f'    <section><h2>{esc(name)} paired with</h2><ul class="guide-points">{"".join(rows)}</ul></section>\n'
        f'    <nav class="guide-nav" aria-label="All city pairs"><h2>More</h2>'
        f'<ul><li><a href="./">All city pairs</a></li>'
        f'<li><a href="../meeting-time-zone-converter.html">Meeting time-zone converter guide</a></li>'
        f'<li><a href="../daylight-saving-holidays.html">Daylight saving and holidays guide</a></li></ul></nav>\n'
        f'  </main>\n  {footer(1)}\n'
        f'  <script>{THEME_SCRIPT}</script>{CF_BEACON}\n'
        f'</body>\n</html>\n'
    )
    return slug, body

def render_index(all_cities, pairs):
    title = "City Time Zone Pairs — Meeting Planner Index | Common Hours"
    description = (f"Time differences, best meeting windows, clock changes and public holidays for "
                    f"{len(pairs)} pairs of major world business hubs.")
    city_links = "".join(f'<li><a href="{slugify(c[0])}.html">{esc(c[0])}</a> — {esc(c[1])} ({esc(c[3])})</li>'
                          for c in all_cities)
    pair_links = "".join(f'<li><a href="{href}">{esc(a[0])} and {esc(b[0])}</a></li>'
                          for a, b, href in pairs)
    body = (
        f'{head(title, description, "time/", 1)}\n<body>\n  {header(1)}\n'
        f'  <main class="content-page">\n'
        f'    <p class="eyebrow">Time zone meeting planner</p>\n'
        f'    <h1>City time zone pairs</h1>\n'
        f'    <p class="lede">{esc(description)} Every page shows the real difference across the whole '
        f'year — including the weeks when it shifts — plus each country’s upcoming public holidays.</p>\n'
        f'    <a class="primary-button" href="{SITE}/">Open the free planner</a>\n'
        f'    <section><h2>By city</h2><ul class="guide-points">{city_links}</ul></section>\n'
        f'    <section><h2>All {len(pairs)} pairs</h2><ul class="guide-points">{pair_links}</ul></section>\n'
        f'  </main>\n  {footer(1)}\n'
        f'  <script>{THEME_SCRIPT}</script>{CF_BEACON}\n'
        f'</body>\n</html>\n'
    )
    return "index.html", body

def write_sitemap(pair_slugs, city_slugs):
    today = TODAY.isoformat()
    urls = [f"{SITE}/", f"{SITE}/privacy.html", f"{SITE}/meeting-time-zone-converter.html",
            f"{SITE}/international-meeting-planner.html", f"{SITE}/daylight-saving-holidays.html",
            f"{SITE}/time/"]
    urls += [f"{SITE}/time/{s}" for s in city_slugs]
    urls += [f"{SITE}/time/{s}" for s in pair_slugs]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>")
    xml.append("</urlset>\n")
    open(os.path.join(REPO, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml))
    return len(urls)

def main():
    global VERSION
    idx = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
    m = re.search(r"styles\.css\?v=([0-9A-Za-z\-]+)", idx)
    VERSION = m.group(1) if m else "1"

    os.makedirs(OUT_DIR, exist_ok=True)
    # clear previously generated pages so renames/removals never leave orphans
    for f in os.listdir(OUT_DIR):
        if f.endswith(".html"): os.remove(os.path.join(OUT_DIR, f))

    pairs = []
    for i, a in enumerate(CITIES):
        for b in CITIES[i + 1:]:
            slug, html = render_pair_page(a, b, CITIES)
            open(os.path.join(OUT_DIR, slug), "w", encoding="utf-8").write(html)
            pairs.append((a, b, slug))

    city_slugs = []
    for c in CITIES:
        slug, html = render_city_hub(c, CITIES)
        open(os.path.join(OUT_DIR, slug), "w", encoding="utf-8").write(html)
        city_slugs.append(slug)

    slug, html = render_index(CITIES, pairs)
    open(os.path.join(OUT_DIR, slug), "w", encoding="utf-8").write(html)

    total_urls = write_sitemap([p[2] for p in pairs], city_slugs)
    words = 0
    for f in os.listdir(OUT_DIR):
        t = open(os.path.join(OUT_DIR, f), encoding="utf-8").read()
        t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S | re.I)
        words += len(re.sub(r"<[^>]+>", " ", t).split())
    print(f"  cities:      {len(CITIES)}")
    print(f"  pair pages:  {len(pairs)}")
    print(f"  city hubs:   {len(city_slugs)}")
    print(f"  index:       1")
    print(f"  sitemap:     {total_urls} URLs")
    print(f"  asset ver:   {VERSION}")
    print(f"  total words across generated pages: {words:,}")

if __name__ == "__main__":
    main()
