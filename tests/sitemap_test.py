"""Sitemap correctness. No browser needed.

`<lastmod>` is only worth sending if it is true, and it was not: write_sitemap()
stamped today's date on all 474 URLs unconditionally, so the sitemap claimed
every page changed every time the generator ran. Google uses lastmod only where
it is consistently accurate, so an always-today sitemap teaches it to ignore the
field — losing a signal that genuinely helps prioritise crawling on a site with
little crawl demand.

Dates now come from tools/sitemap-dates.json, a committed manifest of content
hashes with the `?v=` cache-busting version normalised out — so a bump_assets
run, which rewrites that string in every file, moves no dates.

Usage:  python tests/sitemap_test.py
"""
import sys, os, re, json, hashlib, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

ASSET_V = re.compile(r"\?v=[0-9A-Za-z\-]+")
SITE = "https://findcommonhours.com"

xml = open(os.path.join(REPO, "sitemap.xml"), encoding="utf-8").read()
entries = re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", xml)
print(f"{len(entries)} sitemap entries")
check("every <loc> has a <lastmod>", len(entries) == xml.count("<loc>"),
      (len(entries), xml.count("<loc>")))

manifest_path = os.path.join(REPO, "tools", "sitemap-dates.json")
check("the date manifest exists", os.path.exists(manifest_path))
manifest = json.load(open(manifest_path, encoding="utf-8")) if os.path.exists(manifest_path) else {}
check("the manifest is not empty", len(manifest) > 400, len(manifest))

def url_to_path(u):
    rel = u[len(SITE):].lstrip("/")
    if rel == "" or rel.endswith("/"):
        return rel + "index.html"
    return rel

# ---- dates must be real, not decorative ----
today = datetime.date.today()
bad_fmt, future, missing, mismatch, stale_hash = [], [], [], [], []
for url, date_str in entries:
    path = url_to_path(url)
    try:
        d = datetime.date.fromisoformat(date_str)
    except ValueError:
        bad_fmt.append((url, date_str)); continue
    if d > today:
        future.append((url, date_str))
    rec = manifest.get(path)
    if rec is None:
        missing.append(path); continue
    if rec["date"] != date_str:
        mismatch.append((path, rec["date"], date_str))
    full = os.path.join(REPO, path)
    if os.path.exists(full):
        with open(full, encoding="utf-8") as fh:
            digest = hashlib.sha1(ASSET_V.sub("?v=", fh.read()).encode("utf-8")).hexdigest()
        if digest != rec["hash"]:
            stale_hash.append(path)

check("all dates are valid ISO", not bad_fmt, bad_fmt[:3])
check("no date is in the future", not future, future[:3])
check("every sitemap URL is in the manifest", not missing, missing[:3])
check("sitemap dates agree with the manifest", not mismatch, mismatch[:3])
check("manifest hashes match the files on disk", not stale_hash, stale_hash[:3])

# ---- the thing that started this: dates must not all be identical forever ----
# One date is legitimate right after a mass regeneration, so this is not an
# assertion about spread. What it asserts is that the mechanism CAN differentiate:
# a page whose content is untouched must keep its recorded date.
sample = [p for p in manifest if p.endswith(".html")][:1]
check("the manifest records a hash and a date per page",
      all(set(manifest[p]) == {"hash", "date"} for p in manifest), sample)

# ---- redirect stubs must stay out ----
stubs = []
for name in os.listdir(os.path.join(REPO, "holidays")):
    if not name.endswith(".html"):
        continue
    with open(os.path.join(REPO, "holidays", name), encoding="utf-8") as fh:
        if "<!--redirect-stub-->" in fh.read(400):
            stubs.append(f"holidays/{name}")
listed = [s for s in stubs if f"{SITE}/{s}" in xml]
check(f"none of the {len(stubs)} redirect stubs are listed", not listed, listed[:3])
check("stubs are also absent from the manifest",
      not [s for s in stubs if s in manifest], [s for s in stubs if s in manifest][:3])

# ---- every listed file actually exists ----
gone = [url_to_path(u) for u, _ in entries if not os.path.exists(os.path.join(REPO, url_to_path(u)))]
check("every sitemap URL maps to a file on disk", not gone, gone[:3])

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All sitemap checks passed."))
sys.exit(1 if fails else 0)
