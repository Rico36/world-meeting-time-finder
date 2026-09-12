"""Feedback-form checks.

Rebuilt Sep 2026 after the original scratchpad copy was lost.

Two constraints shape this file, and both cost time to rediscover:

  * Turnstile is DOMAIN-BOUND to findcommonhours.com, and headless Chromium is
    never issued a token anyway - by design. So the real captcha hop cannot be
    driven from a test at all. Turnstile is stubbed here and the Worker is
    routed, which means this file proves the CLIENT contract only: what gets
    sent, when nothing gets sent, and what the visitor is told. The server side
    is covered by worker/feedback-worker.test.mjs, and the end-to-end hop was
    verified once by hand (issue #1, 6 Sep 2026).

  * Never assert on the checked-in state of index.html. The original suite
    assumed the form was unconfigured and broke the day it went live. Every
    check below either routes the request or reads configuration as data.

Usage:  python -m http.server 8765     # from the repo root, in another shell
        python tests/feedback_test.py
"""
import sys, json
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
fails = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    if not cond: fails.append(name)

# Stubs Turnstile before app.js runs: renders a hidden input with the name the
# real widget uses, so the submit path can be exercised without a live captcha.
STUB = """
window.__posted = [];
window.turnstile = {
  render: function(sel, opts){
    var el = document.querySelector(sel);
    var i = document.createElement('input');
    i.type = 'hidden'; i.name = 'cf-turnstile-response';
    i.value = window.__token === undefined ? 'stub-token' : window.__token;
    el.appendChild(i);
    return 'stub-widget';
  },
  reset: function(){}
};
"""

def open_dialog(pg):
    pg.click('a[data-i18n="navFeedback"]')
    pg.wait_for_timeout(250)

def new_page(b, token="stub-token", worker_status=200, worker_body='{"ok":true}'):
    ctx = b.new_context()
    pg = ctx.new_page()
    pg.add_init_script(f"window.__token = {json.dumps(token)};" + STUB)
    # Turnstile's own script must not load: it would replace the stub and, off
    # its bound domain, render nothing at all.
    pg.route("https://challenges.cloudflare.com/**",
             lambda r: r.fulfill(status=200, content_type="application/javascript",
                                 body="window.dispatchEvent(new Event('turnstile-stubbed'));"))

    posted = []
    def worker(route):
        req = route.request
        try:
            posted.append(json.loads(req.post_data or "{}"))
        except Exception:
            posted.append({"_unparsable": req.post_data})
        route.fulfill(status=worker_status, content_type="application/json",
                      headers={"Access-Control-Allow-Origin": "*"}, body=worker_body)
    pg.route("**findcommonhours-feedback**", worker)
    return ctx, pg, posted

with sync_playwright() as b_sp:
    b = b_sp.chromium.launch()
    errs = []

    # ---- configuration is present and sane ----
    ctx, pg, posted = new_page(b)
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)

    cfg = pg.evaluate("""()=>{const d=document.getElementById('feedback-dialog');
        return d ? {endpoint:d.dataset.endpoint||'', sitekey:d.dataset.sitekey||''} : null;}""")
    check("the dialog exists", cfg is not None)
    check("an endpoint is configured", bool(cfg and cfg["endpoint"]), cfg)
    check("the endpoint is https", bool(cfg and cfg["endpoint"].startswith("https://")), cfg)
    check("a Turnstile site key is configured", bool(cfg and cfg["sitekey"]), cfg)

    # ---- the footer link opens the dialog instead of navigating to GitHub ----
    check("the dialog starts closed", not pg.eval_on_selector("#feedback-dialog", "e=>e.open"))
    before = pg.url
    open_dialog(pg)
    check("the footer link opens the dialog", pg.eval_on_selector("#feedback-dialog", "e=>e.open"))
    check("it does not navigate away to GitHub", pg.url == before, pg.url)

    # ---- the honeypot must be invisible to a human but present for a bot ----
    # The honeypot is positioned off-screen rather than display:none, and that is
    # deliberate - display:none is the first thing a bot checks for and skips, so
    # it would defeat the trap. That also means offsetParent is NOT null here:
    # the test has to ask where the element actually is, not whether it renders.
    hp = pg.evaluate("""()=>{const i=document.querySelector('[name=website]');
        if(!i) return null;
        const wrap=i.closest('.feedback-honeypot');
        const r=wrap.getBoundingClientRect(), s=getComputedStyle(wrap);
        const offscreen = r.right < 0 || r.bottom < 0
                       || r.left > innerWidth || r.top > innerHeight;
        return {exists:true, offscreen:offscreen,
                hiddenOutright:s.display==='none'||s.visibility==='hidden',
                rect:[Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)],
                ariaHidden:wrap&&wrap.getAttribute('aria-hidden')==='true',
                tabindex:i.getAttribute('tabindex')};}""")
    check("the honeypot field exists", bool(hp and hp["exists"]))
    check("the honeypot is out of sight for a person",
          hp and (hp["offscreen"] or hp["hiddenOutright"]), hp)
    # A visitor who could see and fill it would have their feedback silently
    # dropped: honeypot rejections deliberately return a fake success.
    check("the honeypot cannot be filled by accident",
          hp and hp["rect"][2] <= 1 or hp["offscreen"], hp)
    check("the honeypot is hidden from assistive tech", hp and hp["ariaHidden"], hp)
    check("the honeypot is not reachable by keyboard", hp and hp["tabindex"] == "-1", hp)

    # ---- a privacy line, since the form takes an optional email ----
    check("the privacy note is shown",
          pg.eval_on_selector(".feedback-privacy", "e=>e.innerText.trim().length") > 10)

    # ---- an empty message sends nothing ----
    pg.fill("[name=message]", "")
    pg.click(".feedback-form button[type=submit]")
    pg.wait_for_timeout(400)
    check("an empty message posts nothing", len(posted) == 0, posted)
    check("the dialog stays open on an empty message",
          pg.eval_on_selector("#feedback-dialog", "e=>e.open"))

    # ---- cancel closes without sending ----
    pg.click("[data-feedback-cancel]")
    pg.wait_for_timeout(250)
    check("cancel closes the dialog", not pg.eval_on_selector("#feedback-dialog", "e=>e.open"))
    check("cancel posts nothing", len(posted) == 0, posted)
    ctx.close()

    # ---- no captcha token: tell the visitor, send nothing ----
    ctx, pg, posted = new_page(b, token="")
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    open_dialog(pg)
    pg.fill("[name=message]", "The map does not load on my phone.")
    pg.click(".feedback-form button[type=submit]")
    pg.wait_for_timeout(500)
    check("a missing captcha token posts nothing", len(posted) == 0, posted)
    status = pg.inner_text(".feedback-status").strip()
    check("a missing captcha token tells the visitor", len(status) > 0, repr(status))
    check("the failure message offers the GitHub fallback", "GitHub" in status, status)
    ctx.close()

    # ---- a real submission: check exactly what leaves the browser ----
    ctx, pg, posted = new_page(b)
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    open_dialog(pg)
    pg.fill("[name=message]", "Tokyo shows the wrong offset in October.")
    pg.fill("[name=cities]", "Tokyo, London")
    pg.fill("[name=contact]", "someone@example.com")
    pg.wait_for_timeout(150)
    pg.click(".feedback-form button[type=submit]")
    pg.wait_for_timeout(700)

    check("a complete submission posts exactly once", len(posted) == 1, len(posted))
    body = posted[0] if posted else {}
    check("the message is sent", body.get("message", "").startswith("Tokyo shows"), body)
    check("the cities field is sent", body.get("cities") == "Tokyo, London", body)
    check("the contact field is sent", body.get("contact") == "someone@example.com", body)
    check("the honeypot is sent empty", body.get("website") == "", body)
    check("an elapsed time is sent for the timing floor",
          isinstance(body.get("elapsed"), int) and body["elapsed"] >= 0, body)
    check("the language is sent", bool(body.get("language")), body)
    check("no browsing history or extra data is attached",
          set(body) <= {"message", "cities", "contact", "website", "elapsed",
                        "page", "language", "token"}, sorted(body))
    status = pg.inner_text(".feedback-status").strip()
    check("success is confirmed to the visitor", "Thanks" in status or len(status) > 0, repr(status))
    ctx.close()

    # ---- the Worker refuses: say so, do not pretend it worked ----
    ctx, pg, posted = new_page(b, worker_status=400, worker_body='{"error":"captcha"}')
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(f"{BASE}/", wait_until="networkidle", timeout=60000)
    open_dialog(pg)
    pg.fill("[name=message]", "Testing a rejection path.")
    pg.click(".feedback-form button[type=submit]")
    pg.wait_for_timeout(700)
    status = pg.inner_text(".feedback-status").strip()
    check("a rejected submission is reported, not swallowed",
          "GitHub" in status or "Couldn" in status, repr(status))
    check("the dialog stays open so the text is not lost",
          pg.eval_on_selector("#feedback-dialog", "e=>e.open"))
    check("the send button is re-enabled after a failure",
          not pg.eval_on_selector(".feedback-form button[type=submit]", "e=>e.disabled"))
    ctx.close()

    check("no page errors", not errs, errs[:3])
    b.close()

print("\n" + ("%d check(s) FAILED" % len(fails) if fails else "All feedback checks passed."))
sys.exit(1 if fails else 0)
