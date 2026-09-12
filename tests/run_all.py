"""Run every browser test suite against a local server or production.

    python -m http.server 8765      # from the repo root, in another shell
    python tests/run_all.py

    python tests/run_all.py https://findcommonhours.com

These suites live in the repo on purpose. They previously lived in a temporary
scratchpad directory and three of them were lost when it was cleaned, taking
the only coverage of visitor-city detection and the feedback form with them.
"""
import os, subprocess, sys, time

SUITES = [
    ("detect",    "Visitor-city detection, zone aliases, geo upgrade"),
    ("feedback",  "Feedback dialog: what is sent, and what is not"),
    ("freshness", "Self-correcting dates and the map's visibility"),
    ("holiday",   "Holiday pages as a tool: weekdays, flags, the index filter"),
    ("map",       "Day/night map, pins and the solar terminator"),
    ("merge",     "Retired territory pages and their redirect stubs"),
    ("regional",  "Subdivision holidays and the collapsed section"),
    ("ux",        "Homepage structure, grids, CTA placement"),
]

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
here = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, PYTHONIOENCODING="utf-8")

print(f"Running {len(SUITES)} suites against {base}\n")
results, t0 = [], time.time()
for name, blurb in SUITES:
    path = os.path.join(here, f"{name}_test.py")
    if not os.path.exists(path):
        results.append((name, None, "missing")); continue
    started = time.time()
    proc = subprocess.run([sys.executable, path, base], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env)
    out = (proc.stdout or "") + (proc.stderr or "")
    tail = [l for l in out.strip().splitlines() if l.strip()]
    summary = tail[-1] if tail else "no output"
    ok = proc.returncode == 0
    results.append((name, ok, summary))
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<10} {time.time()-started:5.1f}s  {summary}")
    if not ok:
        for line in tail:
            if line.lstrip().startswith("FAIL"):
                print("          " + line.strip())

bad = [r for r in results if r[1] is not True]
print(f"\n{len(results)-len(bad)}/{len(results)} suites passed in {time.time()-t0:.0f}s")
if bad:
    print("failing: " + ", ".join(n for n, _, _ in bad))
sys.exit(1 if bad else 0)
