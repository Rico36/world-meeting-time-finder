"""Territory-merge checks.

Guards the merge in tools/gen_holiday_pages.py, which the monthly workflow
re-runs unattended. The failure modes it exists to catch are all silent: a
stub that redirects to a page that no longer exists, a stub that acquires ad
code (ads on a body-less page violate AdSense policy), a retired URL leaking
back into the sitemap, or a territory vanishing from the index entirely
instead of pointing at the page that absorbed it.

Usage:  python -m http.server 8765    # from the repo root, in another shell
        python tests/merge_test.py
"""
import sys, os, re, glob
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

stubs, content = [], []
for f in sorted(glob.glob(os.path.join(REPO, "holidays", "*.html"))):
    h = open(f, encoding="utf-8").read()
    (stubs if "<!--redirect-stub-->" in h else content).append((os.path.basename(f), h))

print(f"{len(content)} content pages, {len(stubs)} redirect stubs")
check("a sensible number of stubs", 5 <= len(stubs) <= 40, len(stubs))

# --- stubs must not be monetised or indexed as content ---
check("no stub carries ad code",
      not [n for n, h in stubs if "adsbygoogle" in h or "ca-pub" in h],
      [n for n, h in stubs if "adsbygoogle" in h])
check("every stub has a canonical to its parent",
      all(re.search(r'<link rel="canonical" href="[^"]+/holidays/[a-z-]+\.html">', h) for n, h in stubs))
check("every stub has an instant meta refresh",
      all('http-equiv="refresh" content="0;' in h for n, h in stubs))
bad = [n for n, h in stubs
       if (m := re.search(r'canonical" href="[^"]*/holidays/([a-z-]+\.html)"', h))
       and not os.path.exists(os.path.join(REPO, "holidays", m.group(1)))]
check("every stub points at a page that exists", not bad, bad)
self_ref = [n for n, h in stubs if f'/holidays/{n}"' in h]
check("no stub redirects to itself", not self_ref, self_ref)

# --- content pages keep their ads ---
check("every content page keeps the ad loader",
      not [n for n, h in content if "ca-pub-4158152621897495" not in h],
      [n for n, h in content if "ca-pub" not in h][:3])

# --- the sitemap must list content only ---
sm = open(os.path.join(REPO, "sitemap.xml"), encoding="utf-8").read()
listed = [n for n, _ in stubs if f"/holidays/{n}<" in sm]
check("no stub appears in the sitemap", not listed, listed)
missing = [n for n, _ in content if n != "index.html" and f"/holidays/{n}<" in sm]
check("content pages are still in the sitemap", len(missing) == len(content) - 1,
      f"{len(missing)} of {len(content)-1}")

# --- parent pages must name the territories they absorbed ---
absorbed = []
for n, h in stubs:
    m = re.search(r'<p>([^<]+?) observes the ([^<]+?) public holiday calendar', h)
    if m: absorbed.append((m.group(1), m.group(2)))
check("each stub names its territory and parent", len(absorbed) == len(stubs))
unnamed = []
for terr, parent in absorbed:
    ph = dict(content).get(re.sub(r"[^a-z0-9]+", "-", parent.lower()).strip("-") + ".html", "")
    if terr not in ph: unnamed.append((terr, parent))
check("parent page names every territory it absorbed", not unnamed, unnamed)

# --- the browser actually follows the redirect ---
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    name = stubs[0][0]
    pg.goto(f"{BASE}/holidays/{name}", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(900)
    check(f"{name} redirects in a real browser",
          not pg.url.endswith(name), pg.url)
    check("lands on a page with holiday content",
          pg.eval_on_selector_all(".holiday-table div[data-date]", "e=>e.length") > 5)

    # a retired territory is still findable from the index
    pg.goto(f"{BASE}/holidays/", wait_until="networkidle", timeout=60000)
    terr = absorbed[0][0]
    loc = pg.locator(f"#filter-target li a:has-text('{terr}')").first
    check(f"'{terr}' still listed on the index", loc.count() > 0)
    if loc.count():
        href = loc.get_attribute("href")
        check(f"'{terr}' links to the surviving page",
              href and href not in (name,), href)
    check("no page errors", not errs, errs)
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All merge checks passed."))
sys.exit(1 if fails else 0)
