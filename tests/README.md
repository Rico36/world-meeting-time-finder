# Tests

Browser tests for findcommonhours.com. Playwright drives a real Chromium
against a served copy of the site, so they check what a visitor actually gets
rather than what the source says they should.

```bash
pip install playwright && playwright install chromium
python -m http.server 8765          # from the repo root, in another shell
python tests/run_all.py             # ~2 minutes
```

Against production (no server needed, and a good check after a deploy):

```bash
python tests/run_all.py https://findcommonhours.com
```

Each suite also runs alone, and takes the same optional base URL:

```bash
python tests/detect_test.py
```

| Suite | Covers |
|---|---|
| `clock_test.py` | One clock format per screen, the 12/24h toggle, locale defaults |
| `detect_test.py` | Visitor-city detection, legacy zone aliases, the geo upgrade and its refusals |
| `feedback_test.py` | Feedback dialog: what leaves the browser, what does not, what the visitor is told |
| `freshness_test.py` | Dates that recompute on load, map visibility |
| `holiday_test.py` | Holiday pages as a tool: weekdays, weekend flags, estimate markers, index filter |
| `map_test.py` | Land outlines, city pins, solar terminator vs an independent Python computation |
| `merge_test.py` | Retired territory pages, redirect stubs, sitemap exclusion |
| `regional_test.py` | Subdivision holidays, collapsed by default |
| `slot_test.py` | Slot selection, and that the heading never claims more than the code knows |
| `ux_test.py` | Homepage structure, grids, CTA placement |

Server-side tests are separate and need Node, not a browser:

```bash
node worker/feedback-worker.test.mjs
node worker/geo-worker.test.mjs
```

## Why these live in the repo

They used to live in a temporary scratchpad directory. Three of them —
detection, holiday and feedback, about 56 checks — were lost when it was
cleaned, and had to be rewritten from the source they covered. Anything worth
running twice belongs here.

## Two things that will waste your time otherwise

**Turnstile cannot be exercised for real.** It is domain-bound to
findcommonhours.com, and headless Chromium is never issued a token anyway — by
design. `feedback_test.py` stubs the widget and routes the Worker, so it proves
the *client* contract only. The server side is `worker/feedback-worker.test.mjs`;
the full hop to a filed issue was verified once by hand and is not automatable.

**Never assert on the checked-in state of `index.html`.** An earlier version of
the feedback suite assumed the form was unconfigured, and broke the day it went
live. Route the request or read configuration as data instead.
