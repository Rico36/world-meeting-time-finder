"""Checks the new index filter + homepage restructure. Usage: python ux_test.py [base]"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:140]))

    # ---- holidays index: grouping + filter ----
    pg.goto(f"{BASE}/holidays/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(600)
    groups = pg.eval_on_selector_all("#filter-target .link-group h3", "e=>e.map(x=>x.textContent)")
    check("holidays: grouped by continent", len(groups) >= 5, groups)
    total = pg.eval_on_selector_all("#filter-target .link-grid li", "e=>e.length")
    check("holidays: 246 countries listed", total == 246, total)
    check("holidays: count reads total", "246" in pg.inner_text("#filter-count"), pg.inner_text("#filter-count"))
    pg.fill("#filter", "jap"); pg.wait_for_timeout(300)
    vis = pg.eval_on_selector_all("#filter-target .link-grid li:not([hidden])", "e=>e.map(x=>x.textContent)")
    check("holidays: filter narrows to Japan", vis == ["Japan"], vis)
    vg = pg.eval_on_selector_all("#filter-target .link-group:not([hidden]) h3", "e=>e.map(x=>x.textContent)")
    check("holidays: empty continent groups hide", len(vg) == 1, vg)
    check("holidays: count updates", "of 246" in pg.inner_text("#filter-count"), pg.inner_text("#filter-count"))
    pg.fill("#filter", ""); pg.wait_for_timeout(300)
    check("holidays: clearing restores all",
          pg.eval_on_selector_all("#filter-target .link-grid li:not([hidden])", "e=>e.length") == 246)

    # ---- time index ----
    pg.goto(f"{BASE}/time/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(600)
    t = pg.eval_on_selector_all("#filter-target .link-grid li", "e=>e.length")
    check("time: 210 pairs in filter scope", t == 210, t)
    pg.fill("#filter", "tokyo"); pg.wait_for_timeout(300)
    vis = pg.eval_on_selector_all("#filter-target .link-grid li:not([hidden])", "e=>e.length")
    check("time: filtering 'tokyo' gives 20 pairs", vis == 20, vis)

    # ---- homepage ----
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(800)
    check("homepage: tools section present", pg.eval_on_selector_all("#tools .resource-card", "e=>e.length") == 3,
          pg.eval_on_selector_all("#tools .resource-card", "e=>e.map(x=>x.textContent.slice(0,20))"))
    check("homepage: guides section has 3 article cards",
          pg.eval_on_selector_all("#guides .resource-card", "e=>e.length") == 3,
          pg.eval_on_selector_all("#guides .resource-card", "e=>e.map(x=>x.getAttribute('href'))"))
    check("homepage: methodology is now a stub with a link",
          pg.eval_on_selector_all('#holiday-methodology a[href="holiday-data-accuracy.html"]', "e=>e.length") == 1)
    check("homepage: planner anchor exists", pg.eval_on_selector_all("#planner", "e=>e.length") == 1)

    # ---- top-bar nav: Holidays and City pairs ----
    # Both sections were reachable only from the footer. The nav is on every
    # page, not just here, so clicking through does not strand the reader.
    nav = pg.eval_on_selector_all(".site-nav a", "e=>e.map(a=>[a.textContent.trim(),a.getAttribute('href')])")
    check("homepage: top nav has exactly two links", len(nav) == 2, nav)
    check("homepage: nav links to Holidays and City pairs",
          [n[0] for n in nav] == ["Holidays", "City pairs"], nav)
    check("homepage: nav hrefs resolve to the section indexes",
          [n[1] for n in nav] == ["holidays/", "time/"], nav)
    check("homepage: nav links are a real tap target",
          min(pg.eval_on_selector_all(".site-nav a", "e=>e.map(a=>a.getBoundingClientRect().height)")) >= 40)
    check("homepage: header does not overflow",
          not pg.eval_on_selector(".site-header", "e=>e.scrollWidth>e.clientWidth+1"))

    # the nav must actually go somewhere, and mark where you are when it does
    pg.click('.site-nav a[href="holidays/"]')
    pg.wait_for_load_state("networkidle", timeout=60000)
    check("nav: Holidays opens the holiday index", pg.url.rstrip("/").endswith("/holidays"), pg.url)
    check("nav: the current section is marked on arrival",
          pg.eval_on_selector_all('.site-nav a[aria-current="page"]', "e=>e.map(a=>a.textContent.trim())") == ["Holidays"])
    pg.click('.site-nav a:has-text("City pairs")')
    pg.wait_for_load_state("networkidle", timeout=60000)
    check("nav: City pairs is reachable from Holidays", pg.url.rstrip("/").endswith("/time"), pg.url)
    check("nav: City pairs marks itself current",
          pg.eval_on_selector_all('.site-nav a[aria-current="page"]', "e=>e.map(a=>a.textContent.trim())") == ["City pairs"])
    # and from a leaf page, not just the indexes
    pg.goto(f"{BASE}/holidays/japan.html", wait_until="networkidle", timeout=60000)
    check("nav: present on a country page", pg.eval_on_selector_all(".site-nav a", "e=>e.length") == 2)
    check("nav: a country page marks Holidays current",
          pg.eval_on_selector_all('.site-nav a[aria-current="page"]', "e=>e.map(a=>a.textContent.trim())") == ["Holidays"])
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    # The site is English-only by decision, not by omission. The selector
    # translated index.html and nothing else - 1 page of 485, with no hreflang -
    # so picking Spanish gave a Spanish homepage that led only into English.
    # These checks exist so it is not reintroduced by accident.
    check("homepage: no language selector",
          pg.eval_on_selector_all("#language, .language-field", "e=>e.length") == 0)
    check("homepage: declares itself English",
          pg.eval_on_selector("html", "e=>e.lang") == "en")
    check("homepage: copy is in English",
          "Three ways" in pg.inner_text("#tools") or "ways" in pg.inner_text("#tools").lower(),
          pg.inner_text("#tools")[:60])
    check("homepage: a stale saved language does not resurface",
          pg.evaluate("""()=>{localStorage.setItem('commonHoursLanguage','es');return true;}"""))
    pg.reload(wait_until="networkidle", timeout=60000); pg.wait_for_timeout(900)
    check("homepage: still English after a stale 'es' in storage",
          pg.eval_on_selector("html", "e=>e.lang") == "en"
          and pg.evaluate("()=>localStorage.getItem('commonHoursLanguage')") is None)

    # ---- new accuracy page ----
    pg.goto(f"{BASE}/holiday-data-accuracy.html", wait_until="networkidle", timeout=60000)
    words = len(pg.inner_text("main").split())
    check("accuracy page: substantive", words > 350, words)
    check("accuracy page: mentions the 7 uncovered countries", "Pakistan" in pg.inner_text("main"))
    check("no page errors", not errs, errs)
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All UX checks passed."))
sys.exit(1 if fails else 0)
