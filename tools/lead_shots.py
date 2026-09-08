#!/usr/bin/env python3
"""
lead_shots.py — evidence screenshots + measured facts for one lead (or any URL).

  python tools/lead_shots.py --lead lukanec            # reads data/leads/five.json → data/leads/lukanec/shots/
  python tools/lead_shots.py --lead all
  python tools/lead_shots.py --url https://example.at --out data/leads/lukanec/shots --prefix comp-1   # competitor: hero + mobile only

Lead mode writes: desk-hero.png (1440×900) · desk-full.png (full page, capped) · m390-vp1..vp3.png (390×844, screens 1–3)
· impressum.png (if known) · facts.json (heights, screens, tap targets < 44 px, smallest font, horizontal overflow, requests, bytes,
console errors, cookie banner seen) · INDEX.md. Headless Chromium via Playwright; nothing is clicked except a reject/decline
cookie button when one is obvious (so screens 2–3 show the page, not the banner). Read-only, no forms.
"""
import argparse, json, pathlib, sys, time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEADS = ROOT / "data" / "leads"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
REJECT = ["button:has-text('Weiter ohne')", "button:has-text('Ohne Einwilligung')", "button:has-text('Ohne Zustimmung')", "button:has-text('Ablehnen')",
          "button:has-text('Alle ablehnen')", "button:has-text('Nur notwendige')", "button:has-text('Nur essenzielle')", "button:has-text('Nur Essenzielle')",
          "button:has-text('Essenzielle')", "button:has-text('Reject')", "button:has-text('Decline')", "a:has-text('Weiter ohne')", "a:has-text('Ablehnen')",
          "[id*='reject' i]", "[class*='reject' i]", "[id*='decline' i]", "button:has-text('Akzeptieren')", "button:has-text('Alle akzeptieren')", "button:has-text('Accept')", "button:has-text('OK')"]
HIDE_JS = """() => { let n=0; for (const e of document.querySelectorAll('body *')) { const s=getComputedStyle(e); if ((s.position==='fixed'||s.position==='sticky') && e.offsetHeight>120 && /cookie|consent|privacy|privatsph|borlabs|cmp|gdpr|dsgvo|usercentrics|cookiebot|klaro|complianz/i.test(e.className+' '+e.id+' '+(e.getAttribute('aria-label')||''))) { e.style.setProperty('display','none','important'); n++; } }
  for (const e of document.querySelectorAll('[class*=overlay],[class*=backdrop],[id*=overlay]')) { if (getComputedStyle(e).position==='fixed') { e.style.setProperty('display','none','important'); n++; } }
  document.documentElement.style.overflow='auto'; document.body.style.overflow='auto'; return n; }"""
MEASURE_JS = """() => {
  const els=[...document.querySelectorAll('a,button,input,select,textarea,[role=button]')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0});
  const small=els.filter(e=>{const r=e.getBoundingClientRect();return r.width<44||r.height<44}).length;
  const fonts=[...document.querySelectorAll('body *')].filter(e=>e.children.length===0&&e.textContent.trim().length>2).map(e=>parseFloat(getComputedStyle(e).fontSize)).filter(Boolean);
  return {docH:document.documentElement.scrollHeight, scrollW:document.documentElement.scrollWidth, innerW:innerWidth, tap:els.length, tapSmall:small,
          minFont: fonts.length?Math.min(...fonts):null, h1:document.querySelectorAll('h1').length, imgs:document.images.length,
          lang:document.documentElement.lang||'', title:document.title, viewport:!!document.querySelector('meta[name=viewport]')};
}"""

def dismiss(page):
    hit = ""
    for sel in REJECT:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(timeout=700):
                b.click(timeout=1500); time.sleep(0.7); hit = sel; break
        except Exception: pass
    try: hidden = page.evaluate(HIDE_JS)
    except Exception: hidden = 0
    return f"{hit or 'no button'}; hidden fixed overlays: {hidden}"

def shoot(pw, url, out, prefix="", full=True, impressum=""):
    out.mkdir(parents=True, exist_ok=True); facts = {"url": url, "errors": [], "requests": 0, "bytes": 0}
    b = pw.chromium.launch(); p = prefix + ("-" if prefix else "")
    try:
        # ---- desktop ----
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA, locale="de-AT", ignore_https_errors=True)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: facts["errors"].append(str(e)[:160]))
        pg.on("console", lambda m: facts["errors"].append("console: " + m.text[:160]) if m.type == "error" else None)
        def on_resp(r):
            facts["requests"] += 1
            try: facts["bytes"] += int(r.headers.get("content-length") or 0)
            except Exception: pass
        pg.on("response", on_resp)
        t0 = time.time()
        try: pg.goto(url, wait_until="networkidle", timeout=45000)
        except PWTimeout: facts["errors"].append("networkidle timeout (kept going)")
        facts["load_s"] = round(time.time() - t0, 1); time.sleep(1.2)
        facts["final_url"] = pg.url
        pg.screenshot(path=str(out / f"{p}desk-hero.png"))
        facts["cookie_banner_dismissed"] = dismiss(pg)
        facts["desktop"] = pg.evaluate(MEASURE_JS)
        if full:
            h = min(facts["desktop"]["docH"], 7000)
            pg.screenshot(path=str(out / f"{p}desk-full.png"), full_page=True, clip={"x": 0, "y": 0, "width": 1440, "height": h})
        if impressum:
            try:
                pg.goto(impressum, wait_until="domcontentloaded", timeout=30000); time.sleep(1.0); dismiss(pg)
                pg.screenshot(path=str(out / f"{p}impressum.png"))
            except Exception as e: facts["errors"].append("impressum: " + type(e).__name__)
        ctx.close()
        # ---- mobile ----
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, user_agent=UA.replace("Windows NT 10.0; Win64; x64", "Linux; Android 13; Pixel 7"), locale="de-AT", ignore_https_errors=True)
        pg = ctx.new_page()
        try: pg.goto(url, wait_until="networkidle", timeout=45000)
        except PWTimeout: pass
        time.sleep(1.0)
        pg.screenshot(path=str(out / f"{p}m390-vp1.png"))          # what a visitor sees first, banner included
        facts["cookie_banner_dismissed_mobile"] = dismiss(pg); time.sleep(0.5)
        pg.screenshot(path=str(out / f"{p}m390-vp1b.png"))       # first screen with the banner out of the way
        m = pg.evaluate(MEASURE_JS); facts["mobile"] = m
        facts["mobile"]["screens"] = round(m["docH"] / 844, 1); facts["mobile"]["h_overflow"] = m["scrollW"] > m["innerW"]
        if full:
            for i in (2, 3):
                pg.evaluate(f"window.scrollTo(0,{(i-1)*844})"); time.sleep(0.5)
                pg.screenshot(path=str(out / f"{p}m390-vp{i}.png"))
        ctx.close()
    finally:
        b.close()
    facts["errors"] = facts["errors"][:12]
    return facts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead"); ap.add_argument("--url"); ap.add_argument("--out"); ap.add_argument("--prefix", default="")
    a = ap.parse_args()
    with sync_playwright() as pw:
        if a.url:
            out = pathlib.Path(a.out or ".")
            f = shoot(pw, a.url, out, prefix=a.prefix, full=False)
            (out / f"{a.prefix or 'site'}-facts.json").write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
            print(a.prefix or a.url, "→", out, "| load", f.get("load_s"), "s | mobile screens", f.get("mobile", {}).get("screens")); return
        five = json.load(open(LEADS / "five.json", encoding="utf-8"))
        slugs = list(five) if a.lead == "all" else [a.lead]
        for s in slugs:
            L = five[s]; out = LEADS / s / "shots"
            print(f"[{s}] {L['website']}", flush=True)
            try:
                f = shoot(pw, L["website"], out, impressum=L.get("impressum_url", ""))
            except Exception as e:
                f = {"url": L["website"], "errors": [f"FAILED {type(e).__name__}: {e}"]}
            (out / "facts.json").write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
            files = sorted(x.name for x in out.glob("*.png"))
            (out / "INDEX.md").write_text(f"# Screenshots — {L['name']}\n\nAufgenommen {time.strftime('%Y-%m-%d')} mit Playwright/Chromium. Desktop 1440×900, Handy 390×844 (@2x).\n\n" +
                                          "\n".join(f"- `{n}`" for n in files) + f"\n\nMesswerte in `facts.json`: Desktop-Höhe {f.get('desktop',{}).get('docH')} px · Handy {f.get('mobile',{}).get('screens')} Bildschirme · Tap-Ziele < 44 px: {f.get('mobile',{}).get('tapSmall')} von {f.get('mobile',{}).get('tap')} · kleinste Schrift {f.get('mobile',{}).get('minFont')} px · horizontaler Overflow: {f.get('mobile',{}).get('h_overflow')} · Requests {f.get('requests')} · Ladezeit {f.get('load_s')} s · Konsolenfehler {len(f.get('errors',[]))}\n", encoding="utf-8")
            print(f"   {len(files)} shots · load {f.get('load_s')} s · mobile {f.get('mobile',{}).get('screens')} screens · errors {len(f.get('errors',[]))}", flush=True)

if __name__ == "__main__":
    main()
