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

def render_country(pretty, code, hub_cities):
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

    def table(items):
        if not items:
            return '<p>No dates recorded for this year.</p>'
        out = ['<div class="holiday-table">']
        for d, name, est in items:
            tags = classify(d, name + (" (estimated)" if est else ""))
            tag_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)
            out.append(f'<div><span class="when">{WEEKDAY[d.weekday()]} {d.day} {M_LONG[d.month-1]}'
                       f'</span><span class="what">{esc(name)}</span>{tag_html}</div>')
        out.append('</div>')
        return "".join(out)

    if nxt:
        days_away = (nxt[0] - TODAY).days
        away = "today" if days_away == 0 else ("tomorrow" if days_away == 1 else f"in {days_away} days")
        glance = ('<div class="at-a-glance">'
                  f'<div><span class="label">Next public holiday</span>'
                  f'<strong>{nxt[0].day} {M_LONG[nxt[0].month-1]}</strong>'
                  f'<span class="sub">{esc(nxt[1])} — {away}</span></div>'
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
    # A short national list usually means the rest are set regionally (Switzerland
    # has 4 national days and the rest by canton). Saying so turns a sparse-looking
    # page into a useful one.
    short_note = (f" Only {len(this_year)} are set nationally — where the national list is this "
                  f"short, the remaining days are usually fixed by state, province or canton, so "
                  f"check the specific region."
                  if 0 < len(this_year) <= 6 else
                  " Dates below are national holidays; regions, states and individual companies "
                  "often add their own, so confirm with the person you are scheduling with.")
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
        f'{head(title, description, "holidays/" + slug, 1)}\n<body>\n  {header(1)}\n'
        f'  <main class="content-page">\n'
        f'    <p class="eyebrow">Public holidays</p>\n'
        f'    <h1>Public holidays in {esc(pretty)}</h1>\n'
        f'    <p class="lede">{esc(intro)}</p>\n'
        f'    {glance}\n'
        f'    <a class="primary-button" href="{SITE}/">Check a meeting time against these dates</a>\n'
        f'    <section><h2>{TODAY.year}</h2>{table(this_year)}</section>\n'
        f'    <section><h2>{TODAY.year + 1}</h2>{table(next_year)}</section>\n'
        f'    <section><h2>How to use this</h2><p>A public holiday does not always mean nobody is '
        f'working, and a clear calendar does not mean your colleague is free. Treat these dates as a '
        f'prompt to ask rather than an answer — especially the ones marked as set by moon sighting, '
        f'where the final date is confirmed only days ahead.</p></section>\n'
        f'    {related}\n'
        f'  </main>\n  {footer(1)}\n'
        f'  <script type="application/ld+json">{json.dumps(crumb_ld)}</script>\n'
        f'  <script type="application/ld+json">{json.dumps(faq_ld)}</script>\n'
        f'  <script>{THEME_SCRIPT}</script>{CF_BEACON}\n'
        f'</body>\n</html>\n'
    )
    return slug, body

def render_index(countries):
    title = f"Public Holidays by Country — {TODAY.year} and {TODAY.year+1} | Common Hours"
    description = (f"Public holiday dates for {len(countries)} countries, with weekdays and weekend "
                    f"clashes marked. Check before scheduling an international meeting.")
    cmap = continent_map()
    grouped = {}
    for name, code in countries:
        grouped.setdefault(cmap.get(code, "Other"), []).append((name, code))
    order = [c for c in CONTINENT_ORDER if c in grouped] + \
            [c for c in sorted(grouped) if c not in CONTINENT_ORDER]
    groups_html = ""
    for cont in order:
        items = "".join(f'<li><a href="{slugify(n)}.html">{esc(n)}</a></li>'
                        for n, _ in sorted(grouped[cont]))
        groups_html += (f'<div class="link-group"><h3>{esc(cont)} ({len(grouped[cont])})</h3>'
                        f'<ul class="link-grid">{items}</ul></div>')
    body = (
        f'{head(title, description, "holidays/", 1)}\n<body>\n  {header(1)}\n'
        f'  <main class="content-page">\n'
        f'    <p class="eyebrow">Public holidays</p>\n'
        f'    <h1>Public holidays by country</h1>\n'
        f'    <p class="lede">{esc(description)} Each page shows the weekday for every date, flags the '
        f'ones that land on a weekend, and marks dates whose final day is set by moon sighting.</p>\n'
        f'    <a class="primary-button" href="{SITE}/">Open the meeting planner</a>\n'
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

    for pretty, code in countries:
        slug, html = render_country(pretty, code, by_code.get(code, []))
        open(os.path.join(OUT_DIR, slug), "w", encoding="utf-8").write(html)

    slug, html = render_index(countries)
    open(os.path.join(OUT_DIR, slug), "w", encoding="utf-8").write(html)

    total = write_sitemap()
    words = 0
    for f in os.listdir(OUT_DIR):
        t = open(os.path.join(OUT_DIR, f), encoding="utf-8").read()
        t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S | re.I)
        words += len(re.sub(r"<[^>]+>", " ", t).split())
    print(f"  countries:  {len(countries)}")
    print(f"  pages:      {len(countries) + 1}")
    print(f"  sitemap:    {total} URLs (all sections)")
    print(f"  words:      {words:,}")

if __name__ == "__main__":
    main()
