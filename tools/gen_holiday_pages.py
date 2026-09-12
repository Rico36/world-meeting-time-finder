"""Generate public-holiday pages under holidays/ — one per country, plus an index.

Why: the site had exactly one function (the planner) surrounded by prose. A
visitor wanting "when is the next holiday in Japan" had nowhere to go, and
"<country> public holidays <year>" is a real, high-volume search the site
captured none of. Holiday lists are also inherently scannable rather than
essay-shaped, which is the opposite failure mode to the city-pair pages.

Each page lists this year's remaining holidays and next year's, with the
weekday for each, a flag when one lands on a weekend (no day off in lieu in
most countries) or creates a likely long weekend, and a marker for dates
python-holidays itself reports as estimated — the moon-sighting holidays whose
final date is set by observation, the same honesty the planner already applies.

Shares its page chrome and helpers with tools/gen_city_pairs.py so the two
sections stay visually identical and the sitemap stays complete.

Usage:  python tools/gen_holiday_pages.py
Requires: pip install holidays
"""
import os, re, sys, json
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import holidays
from gen_city_pairs import (SITE, REPO, TODAY, YEARS, M_LONG, CITIES, slugify, esc,
                            head, header, footer, THEME_SCRIPT, CF_BEACON,
                            english_holidays, write_sitemap)
import gen_city_pairs

OUT_DIR = os.path.join(REPO, "holidays")
WEEKDAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")

CONTINENTS = {"EU": "Europe", "AS": "Asia", "NA": "North America", "SA": "South America",
              "AF": "Africa", "OC": "Oceania", "AN": "Antarctica"}
CONTINENT_ORDER = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania", "Antarctica"]

def continent_map():
    """ISO alpha-2 -> continent name, from the GeoNames countryInfo.txt the
    city/country data already comes from. 246 names in one alphabetical column
    is a wall; grouped by continent it is browsable."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "countryInfo.txt")
    if not os.path.exists(path):
        import urllib.request
        urllib.request.urlretrieve("https://download.geonames.org/export/dump/countryInfo.txt", path)
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("#"): continue
        f = line.split("\t")
        if len(f) > 8 and f[0]:
            out[f[0]] = CONTINENTS.get(f[8].strip(), "Other")
    return out

HOLIDAY_SCRIPT = """(function(){
  var M=['January','February','March','April','May','June','July','August','September','October','November','December'];
  var box=document.querySelector('[data-next-holiday]');
  if(!box) return;
  var rows=[].slice.call(document.querySelectorAll('.holiday-table div[data-date]'));
  var today=new Date(); today.setHours(0,0,0,0);
  var next=null;
  for(var i=0;i<rows.length;i++){
    var parts=rows[i].getAttribute('data-date').split('-');
    var d=new Date(+parts[0],+parts[1]-1,+parts[2]);
    if(d>=today){ next={date:d,name:(rows[i].querySelector('.what')||{}).textContent||''}; break; }
  }
  if(!next){ box.hidden=true; return; }
  var days=Math.round((next.date-today)/86400000);
  box.querySelector('[data-next-date]').textContent=next.date.getDate()+' '+M[next.date.getMonth()];
  box.querySelector('[data-next-name]').textContent=next.name;
  box.querySelector('[data-next-away]').textContent=
    ' \\u2014 '+(days===0?'today':days===1?'tomorrow':'in '+days+' days');
})();"""

FILTER_SCRIPT = """(function(){
  var box=document.getElementById('filter'),count=document.getElementById('filter-count');
  if(!box) return;
  var scope=document.getElementById('filter-target')||document;
  var items=[].slice.call(scope.querySelectorAll('.link-grid li')),
      groups=[].slice.call(scope.querySelectorAll('.link-group')),total=items.length;
  items.forEach(function(li){ li.dataset.k=(li.textContent||'').toLowerCase(); });
  function run(){
    var q=box.value.trim().toLowerCase(),shown=0;
    items.forEach(function(li){ var hit=!q||li.dataset.k.indexOf(q)!==-1; li.hidden=!hit; if(hit)shown++; });
    groups.forEach(function(g){ g.hidden=!g.querySelector('li:not([hidden])'); });
    count.textContent=q?(shown+' of '+total+' shown'):(total+' in total');
  }
  box.addEventListener('input',run); run();
})();"""

def country_list():
    out = []
    for key, val in holidays.registry.COUNTRIES.items():
        name, code = val[0], val[1]
        try:
            h = english_holidays(code, YEARS)
            if len(h) == 0: continue
        except Exception:
            continue
        # registry names are CamelCase run-together ("UnitedStates"); space them,
        # then lowercase connecting words so it is "Antigua and Barbuda", not
        # "Antigua And Barbuda" (14 countries were affected)
        pretty = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name).replace("_", " ").strip()
        words = pretty.split()
        pretty = " ".join(w if i == 0 or w.lower() not in ("and", "of", "the", "da")
                          else w.lower() for i, w in enumerate(words))
        out.append((pretty, code))
    return sorted(set(out))

# Territories that observe a sovereign state's calendar. This is the *direction*
# only - which page would absorb which - and it is curated because the data
# cannot supply it: ranking by holiday count alone proposes "American Samoa is
# the parent of the United States" and "Benin is the parent of Switzerland",
# since a superset relationship is not a sovereignty relationship.
#
# Whether a merge actually happens is decided by the data, in merge_plan()
# below. Listing a territory here does not retire its page.
SOVEREIGN = {
    "AX": "FI",
    "SJ": "NO",
    "FO": "DK", "GL": "DK",
    "GF": "FR", "GP": "FR", "MQ": "FR", "RE": "FR", "YT": "FR", "BL": "FR",
    "MF": "FR", "PM": "FR", "TF": "FR", "NC": "FR", "PF": "FR", "WF": "FR",
    "IM": "GB", "JE": "GB", "GG": "GB", "GI": "GB", "FK": "GB", "SH": "GB",
    "BQ": "NL", "SX": "NL", "CW": "NL", "AW": "NL",
    "AS": "US", "GU": "US", "MP": "US", "PR": "US", "VI": "US", "UM": "US",
    "NF": "AU", "CX": "AU", "CC": "AU",
    "TK": "NZ", "NU": "NZ", "CK": "NZ",
}

# How much of a territory's calendar the sovereign must already cover before the
# territory's page is retired into it. At 0.90, twelve of the thirty-eight
# listed territories merge; Puerto Rico (64%), Jersey (50%) and Gibraltar (46%)
# keep their own pages because their calendars genuinely differ, which is the
# point - the goal is removing pages that say nothing new, not shrinking the
# site.
MERGE_THRESHOLD = 0.90

# Marks a retired URL. Both write_sitemap() and the AdSense assertion in
# .github/workflows/refresh-generated-pages.yml look for this: a stub is not a
# content page, so it stays out of the sitemap and deliberately carries no ad
# code - ads on a body-less redirect page are exactly the "little or no content"
# case AdSense prohibits.
STUB_MARKER = "<!--redirect-stub-->"

def merge_plan(countries):
    """Decide which territory pages fold into a sovereign's page.

    Returns (retired, followers): retired maps a territory code to its
    sovereign's code; followers maps a sovereign's code to the list of
    territory names its page now speaks for.

    The decision is re-made from the holiday data on every run, so if the
    upstream library ever gains distinct dates for one of these territories,
    its page comes back automatically and nobody has to notice.
    """
    names = {code: pretty for pretty, code in countries}
    sets = {}
    for pretty, code in countries:
        sets[code] = {(d, str(v)) for d, v in english_holidays(code, YEARS).items()}

    retired, followers = {}, {}
    for terr, sov in sorted(SOVEREIGN.items()):
        if terr not in names or sov not in names:
            continue
        st, ss = sets.get(terr) or set(), sets.get(sov) or set()
        if not st or not ss:
            continue
        if len(st & ss) / len(st) >= MERGE_THRESHOLD:
            retired[terr] = sov
            followers.setdefault(sov, []).append(names[terr])
    for sov in followers:
        followers[sov].sort()
    return retired, followers

def render_stub(pretty, slug, parent_pretty, parent_slug):
    """A retired URL. GitHub Pages cannot issue a 301, so this is the static
    equivalent: a canonical pointing at the surviving page plus an instant meta
    refresh, which Google treats as a redirect and consolidates. It is kept out
    of the sitemap and carries no ads."""
    return (
        f'<!doctype html>\n<html lang="en">\n<head>\n{STUB_MARKER}\n'
        f'  <meta charset="utf-8">\n'
        f'  <title>Public holidays in {esc(pretty)} — see {esc(parent_pretty)}</title>\n'
        f'  <link rel="canonical" href="{SITE}/holidays/{parent_slug}">\n'
        f'  <meta http-equiv="refresh" content="0; url=./{parent_slug}">\n'
        f'</head>\n<body>\n'
        f'  <p>{esc(pretty)} observes the {esc(parent_pretty)} public holiday calendar. '
        f'Redirecting to <a href="./{parent_slug}">public holidays in {esc(parent_pretty)}</a>.</p>\n'
        f'</body>\n</html>\n'
    )

# What a country calls its first-level divisions. Getting this right is most of
# what makes the section read as knowledge rather than as generated filler -
# calling Swiss cantons "regions" is the kind of detail a reader from there
# notices immediately. Anything not listed falls back to "regions".
REGION_NOUN = {
    "CH": "cantons", "CA": "provinces and territories", "US": "states",
    "AU": "states and territories", "ES": "autonomous communities",
    "DE": "federal states", "GB": "nations", "IT": "provinces",
    "IN": "states and union territories", "BR": "states", "AR": "provinces",
    "MY": "states", "PT": "districts and regions", "FR": "overseas regions",
    "NZ": "regions", "AT": "federal states", "BE": "regions", "JP": "prefectures",
    "CN": "regions", "ZA": "provinces", "MX": "states", "NG": "states",
    "ID": "provinces", "PH": "regions", "BA": "entities", "BO": "departments",
}

def regional_holidays(code, national_dates):
    """Dates observed in some of a country's regions but not nationally.

    This is the honest fix for the site's thinnest pages. Switzerland showed 4
    national holidays and read as a stub; it has 44 more that are real, dated
    and cantonal. India - one of the seven countries the live holiday API does
    not cover at all - gains 159. The data was always there, one argument away.

    Returns [(date, name, [region names])], date-ordered. Cheap: all 624
    subdivisions across all 35 countries resolve in about a second.
    """
    try:
        base = holidays.country_holidays(code, years=YEARS)
        subs = list(getattr(base, "subdivisions", ()) or ())
    except Exception:
        return []
    if not subs:
        return []

    # subdivisions_aliases maps name -> code, and a code can have several names
    # ("Bern" and "Berne"). Reverse it and keep the first, which is the
    # library's canonical spelling.
    pretty_sub = {}
    for name, sub_code in (getattr(base, "subdivisions_aliases", {}) or {}).items():
        for c in (sub_code if isinstance(sub_code, (list, tuple)) else [sub_code]):
            pretty_sub.setdefault(c, name)

    found = {}
    for s in subs:
        h = english_holidays(code, YEARS, subdiv=s)
        for d, raw in (h.items() if hasattr(h, "items") else []):
            if d in national_dates:
                continue
            for label in str(raw).split("; "):
                clean = re.sub(r"\s*\(estimated\)\s*", "", label).strip()
                if clean:
                    found.setdefault((d, clean), []).append(pretty_sub.get(s, s))
    return [(d, n, sorted(set(regions)))
            for (d, n), regions in sorted(found.items())]

def render_regional(code, rows, total_subs, noun):
    """Collapsed by default: the page stays as light as it was at first glance,
    and the reader chooses to open it. Forcing 159 extra rows on someone who
    came to check one date would make the page worse, not better."""
    if not rows:
        return "", 0
    this_year = [r for r in rows if r[0].year == TODAY.year]
    next_year = [r for r in rows if r[0].year == TODAY.year + 1]

    def block(items, year):
        if not items:
            return ""
        out = [f'<h3>{year}</h3><div class="holiday-table regional">']
        for d, name, regions in items:
            # Naming twenty regions is noise; a count is the useful fact. Below
            # four, the names themselves are what the reader wants.
            if len(regions) <= 4:
                where = ", ".join(regions)
            else:
                where = f"{len(regions)} of {total_subs} {noun}"
            out.append(f'<div data-date="{d.isoformat()}"><span class="when">'
                       f'{WEEKDAY[d.weekday()]} {d.day} {M_LONG[d.month-1]}</span>'
                       f'<span class="what">{esc(name)}</span>'
                       f'<span class="where">{esc(where)}</span></div>')
        out.append("</div>")
        return "".join(out)

    return (f'<section class="regional-section"><details><summary>'
            f'<span class="summary-title">Regional holidays</span>'
            f'<span class="summary-count">{len(rows)} more dates observed in '
            f'individual {noun}</span></summary>'
            f'{block(this_year, TODAY.year)}{block(next_year, TODAY.year + 1)}'
            f'<p class="note">These are not observed nationwide. Confirm the '
            f'specific region before assuming someone is working.</p>'
            f'</details></section>\n'), len(rows)

def classify(d, name):
    """Notes that make a bare date genuinely useful for meeting planning."""
    tags = []
    wd = d.weekday()
    if wd >= 5:
        tags.append("falls on a weekend")
    elif wd == 0:
        tags.append("long weekend likely")
    elif wd == 4:
        tags.append("long weekend likely")
    if re.search(r"estimated", name, re.I):
        tags.append("date set by moon sighting")
    return tags

def render_country(pretty, code, hub_cities, follows=()):
    slug = f"{slugify(pretty)}.html"
    h = english_holidays(code, YEARS)
    rows = []
    for d, raw in sorted(h.items()):
        for label in str(raw).split("; "):
            est = bool(re.search(r"\(estimated\)", label, re.I))
            clean = re.sub(r"\s*\(estimated\)\s*", "", label).strip()
            rows.append((d, clean, est))
    upcoming = [r for r in rows if r[0] >= TODAY]
    nxt = upcoming[0] if upcoming else None
    this_year = [r for r in rows if r[0].year == TODAY.year]
    next_year = [r for r in rows if r[0].year == TODAY.year + 1]

    title = f"Public Holidays in {pretty} — {TODAY.year} and {TODAY.year+1} | Common Hours"
    description = (f"Every public holiday in {pretty} for {TODAY.year} and {TODAY.year+1}, "
                    f"with the weekday for each and which ones fall on a weekend. "
                    f"Check before scheduling an international meeting.")

    # Territories whose page folded into this one. Naming them is what makes the
    # merge honest: someone searching for Svalbard still lands somewhere that
    # confirms the answer rather than on a page that never mentions it.
    if follows:
        listed = (follows[0] if len(follows) == 1
                  else ", ".join(follows[:-1]) + " and " + follows[-1])
        description += f" Also observed in {listed}."
        follows_html = (
            f'<section><h2>Where else these dates apply</h2>'
            f'<p>The same calendar is observed in {esc(listed)}. '
            f'{"It keeps" if len(follows) == 1 else "They keep"} the '
            f'{esc(pretty)} public holiday schedule, so the dates below apply there too. '
            f'Local observances can still be added on top, so confirm anything '
            f'that falls close to a deadline.</p></section>\n')
    else:
        follows_html = ""

    def table(items):
        if not items:
            return '<p>No dates recorded for this year.</p>'
        out = ['<div class="holiday-table">']
        for d, name, est in items:
            tags = classify(d, name + (" (estimated)" if est else ""))
            tag_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)
            out.append(f'<div data-date="{d.isoformat()}"><span class="when">'
                       f'{WEEKDAY[d.weekday()]} {d.day} {M_LONG[d.month-1]}'
                       f'</span><span class="what">{esc(name)}</span>{tag_html}</div>')
        out.append('</div>')
        return "".join(out)

    if nxt:
        # The date, the name and the countdown are all recomputed on load from the
        # data-date attributes below. A static "in 81 days" is wrong the next day,
        # and a static "next holiday" is wrong once that date passes - on a page
        # that is only regenerated every few months.
        glance = ('<div class="at-a-glance">'
                  f'<div data-next-holiday><span class="label">Next public holiday</span>'
                  f'<strong data-next-date>{nxt[0].day} {M_LONG[nxt[0].month-1]}</strong>'
                  f'<span class="sub"><span data-next-name>{esc(nxt[1])}</span>'
                  f'<span data-next-away></span></span></div>'
                  f'<div><span class="label">{TODAY.year}</span><strong>{len(this_year)} days</strong>'
                  f'<span class="sub">public holidays in total</span></div>'
                  f'<div><span class="label">{TODAY.year+1}</span><strong>{len(next_year)} days</strong>'
                  f'<span class="sub">already scheduled</span></div>'
                  '</div>')
    else:
        glance = ""

    weekend_count = sum(1 for d, _, _ in this_year if d.weekday() >= 5)
    weekend_txt = ("" if not weekend_count else
                   f", of which {weekend_count} "
                   f"{'falls' if weekend_count == 1 else 'fall'} on a weekend")
    # Regional dates. Until these were added, a short national list could only be
    # apologised for ("the rest are usually fixed by canton, so check"); now the
    # page can show them, so the note points at them instead.
    national_dates = {d for d, _, _ in rows}
    reg_rows = regional_holidays(code, national_dates)
    try:
        total_subs = len(list(getattr(holidays.country_holidays(code, years=YEARS),
                                      "subdivisions", ()) or ()))
    except Exception:
        total_subs = 0
    noun = REGION_NOUN.get(code, "regions")
    regional_html, reg_count = render_regional(code, reg_rows, total_subs, noun)

    if reg_count:
        short_note = (f" A further {reg_count} dates are observed in individual {noun} "
                      f"rather than nationwide — they are listed below.")
    elif 0 < len(this_year) <= 6:
        short_note = (f" Only {len(this_year)} are set nationally — where the national list is "
                      f"this short, the remaining days are usually fixed by state, province or "
                      f"canton, so check the specific region.")
    else:
        short_note = (" Dates below are national holidays; regions, states and individual "
                      "companies often add their own, so confirm with the person you are "
                      "scheduling with.")
    intro = f"{pretty} has {len(this_year)} public holidays in {TODAY.year}{weekend_txt}.{short_note}"

    hub_links = "".join(
        f'<li><a href="../time/{slugify(c[0])}.html">Meeting times for {esc(c[0])}</a></li>'
        for c in hub_cities)
    related = (f'<nav class="guide-nav" aria-label="Related"><h2>Plan around these dates</h2><ul>'
               f'{hub_links}'
               f'<li><a href="./">Public holidays in other countries</a></li>'
               f'<li><a href="../daylight-saving-holidays.html">Holidays and daylight saving guide</a></li>'
               f'</ul></nav>')

    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f"When is the next public holiday in {pretty}?",
         "acceptedAnswer": {"@type": "Answer",
                            "text": (f"{nxt[1]} on {nxt[0].day} {M_LONG[nxt[0].month-1]} {nxt[0].year}."
                                     if nxt else "No upcoming date recorded.")}},
        {"@type": "Question", "name": f"How many public holidays does {pretty} have in {TODAY.year}?",
         "acceptedAnswer": {"@type": "Answer", "text": f"{len(this_year)} national public holidays."}},
    ]}
    crumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Common Hours", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Public holidays", "item": SITE + "/holidays/"},
        {"@type": "ListItem", "position": 3, "name": pretty, "item": f"{SITE}/holidays/{slug}"},
    ]}

    body = (
        f'{head(title, description, "holidays/" + slug, 1)}\n<body>\n  {header(1, "holidays")}\n'
        f'  <main class="content-page">\n'
        f'    <p class="eyebrow">Public holidays</p>\n'
        f'    <h1>Public holidays in {esc(pretty)}</h1>\n'
        f'    <p class="lede">{esc(intro)}</p>\n'
        f'    {glance}\n'
        f'    <section><h2>{TODAY.year}</h2>{table(this_year)}</section>\n'
        f'    <section><h2>{TODAY.year + 1}</h2>{table(next_year)}</section>\n'
        f'    {regional_html}'
        f'    {follows_html}'
        f'    <section><h2>How to use this</h2><p>A public holiday does not always mean nobody is '
        f'working, and a clear calendar does not mean your colleague is free. Treat these dates as a '
        f'prompt to ask rather than an answer — especially the ones marked as set by moon sighting, '
        f'where the final date is confirmed only days ahead.</p></section>\n'
        f'    {related}\n'
        f'  </main>\n  {footer(1)}\n'
        f'  <script type="application/ld+json">{json.dumps(crumb_ld)}</script>\n'
        f'  <script type="application/ld+json">{json.dumps(faq_ld)}</script>\n'
        f'  <script>{THEME_SCRIPT}{HOLIDAY_SCRIPT}</script>{CF_BEACON}\n'
        f'</body>\n</html>\n'
    )
    return slug, body

def render_index(countries, retired=None):
    # Retired territories stay listed and stay findable by the filter - they
    # just point at the page that actually answers the question. Dropping them
    # from the index would make the merge a loss of coverage rather than a
    # removal of duplication.
    retired = retired or {}
    title = f"Public Holidays by Country — {TODAY.year} and {TODAY.year+1} | Common Hours"
    description = (f"Public holiday dates for {len(countries)} countries, with weekdays and weekend "
                    f"clashes marked. Check before scheduling an international meeting.")
    cmap = continent_map()
    grouped = {}
    for name, code in countries:
        grouped.setdefault(cmap.get(code, "Other"), []).append((name, code))
    order = [c for c in CONTINENT_ORDER if c in grouped] + \
            [c for c in sorted(grouped) if c not in CONTINENT_ORDER]
    pretty_of = {code: name for name, code in countries}

    def link(name, code):
        sov = retired.get(code)
        if not sov:
            return f'<li><a href="{slugify(name)}.html">{esc(name)}</a></li>'
        parent = pretty_of.get(sov, "")
        return (f'<li><a href="{slugify(parent)}.html" '
                f'title="Observes the {esc(parent)} calendar">{esc(name)}'
                f'<span class="muted"> · {esc(parent)} calendar</span></a></li>')

    groups_html = ""
    for cont in order:
        items = "".join(link(n, c) for n, c in sorted(grouped[cont]))
        groups_html += (f'<div class="link-group"><h3>{esc(cont)} ({len(grouped[cont])})</h3>'
                        f'<ul class="link-grid">{items}</ul></div>')
    body = (
        f'{head(title, description, "holidays/", 1)}\n<body>\n  {header(1, "holidays")}\n'
        f'  <main class="content-page">\n'
        f'    <p class="eyebrow">Public holidays</p>\n'
        f'    <h1>Public holidays by country</h1>\n'
        f'    <p class="lede">{esc(description)} Each page shows the weekday for every date, flags the '
        f'ones that land on a weekend, and marks dates whose final day is set by moon sighting.</p>\n'
        f'    <div class="filter-row"><label class="sr-only" for="filter">Filter countries</label>'
        f'<input id="filter" type="search" autocomplete="off" placeholder="Type to filter '
        f'{len(countries)} countries…"></div>\n'
        f'    <p class="filter-count" id="filter-count">{len(countries)} in total</p>\n'
        f'    <div id="filter-target">{groups_html}</div>\n'
        f'  </main>\n  {footer(1)}\n'
        f'  <script>{THEME_SCRIPT}{FILTER_SCRIPT}</script>{CF_BEACON}\n'
        f'</body>\n</html>\n'
    )
    return "index.html", body

def main():
    idx = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
    m = re.search(r"styles\.css\?v=([0-9A-Za-z\-]+)", idx)
    gen_city_pairs.VERSION = m.group(1) if m else "1"

    os.makedirs(OUT_DIR, exist_ok=True)
    for f in os.listdir(OUT_DIR):
        if f.endswith(".html"): os.remove(os.path.join(OUT_DIR, f))

    countries = country_list()
    by_code = {}
    for c in CITIES:
        by_code.setdefault(c[2], []).append(c)

    retired, followers = merge_plan(countries)
    pretty_of = {code: name for name, code in countries}

    for pretty, code in countries:
        if code in retired:
            parent = pretty_of[retired[code]]
            slug = f"{slugify(pretty)}.html"
            html = render_stub(pretty, slug, parent, f"{slugify(parent)}.html")
        else:
            slug, html = render_country(pretty, code, by_code.get(code, []),
                                        followers.get(code, ()))
        open(os.path.join(OUT_DIR, slug), "w", encoding="utf-8").write(html)

    slug, html = render_index(countries, retired)
    open(os.path.join(OUT_DIR, slug), "w", encoding="utf-8").write(html)

    total = write_sitemap()
    words = 0
    for f in os.listdir(OUT_DIR):
        t = open(os.path.join(OUT_DIR, f), encoding="utf-8").read()
        t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S | re.I)
        words += len(re.sub(r"<[^>]+>", " ", t).split())
    print(f"  countries:  {len(countries)}")
    print(f"  merged:     {len(retired)} territory page(s) retired into a sovereign's")
    for terr, sov in sorted(retired.items(), key=lambda kv: pretty_of[kv[0]]):
        print(f"                {pretty_of[terr]} -> {pretty_of[sov]}")
    print(f"  pages:      {len(countries) + 1 - len(retired)} content, {len(retired)} redirect")
    print(f"  sitemap:    {total} URLs (all sections)")
    print(f"  words:      {words:,}")

if __name__ == "__main__":
    main()
