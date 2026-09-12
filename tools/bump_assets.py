"""Bump the ?v= cache-busting query on styles.css, app.js and guides.js.

GitHub Pages serves with Cache-Control: max-age=600, so without a bump a
returning visitor keeps the cached files for ten minutes after a deploy.

Usage:  python tools/bump_assets.py [version]
Default version is today's date with a counter, e.g. 20261201-1. If the files
already carry today's date the counter increments instead of colliding.
"""
import os, re, sys, glob, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PATTERN = re.compile(r'(styles\.css|app\.js|guides\.js)\?v=([0-9A-Za-z\-]+)')

# The generated pages under time/ and holidays/ link the same three assets
# (as ../styles.css?v=...), so they must be bumped too. Leaving them out is a
# silent bug rather than a loud one: annual-content-refresh.yml runs the
# generators and *then* this script, so the generated pages would be written
# with the old version and never corrected, serving a stale stylesheet to 479
# of the site's 490 pages until the next regeneration happened to pick the new
# version up out of index.html.
files = sorted(glob.glob(os.path.join(REPO, "*.html")) +
               glob.glob(os.path.join(REPO, "time", "*.html")) +
               glob.glob(os.path.join(REPO, "holidays", "*.html")))
current = set()
for f in files:
    current.update(m.group(2) for m in PATTERN.finditer(open(f, encoding="utf-8").read()))

if len(sys.argv) > 1:
    version = sys.argv[1]
else:
    today = datetime.date.today().strftime("%Y%m%d")
    # Continue past the highest counter already used today. Merely avoiding a
    # collision is not enough: with 20260906-4 in place, picking -1 would move
    # the version backwards and could re-serve a build a visitor already cached.
    used = [int(m.group(1)) for m in
            (re.fullmatch(re.escape(today) + r"-(\d+)", v) for v in current) if m]
    version = "%s-%d" % (today, (max(used) + 1) if used else 1)

changed = []
for f in files:
    s = open(f, encoding="utf-8").read()
    out = PATTERN.sub(lambda m: "%s?v=%s" % (m.group(1), version), s)
    if out != s:
        open(f, "w", encoding="utf-8").write(out)
        changed.append(os.path.basename(f))

print("version:", version)
print("previous:", ", ".join(sorted(current)) or "none")
print("updated:", "%d file(s)" % len(changed) if changed else "nothing (already current)")
