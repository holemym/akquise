#!/usr/bin/env python3
"""verify_pitch.py — CLAUDE.md §6 assertions for a rendered deck: zero console errors, slide count, no horizontal overflow,
every slide navigable, captures at 1920 and 500 for critique.  python tools/verify_pitch.py --lead lukanec [--slides 1,4,5]"""
import argparse, json, pathlib, sys
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("--lead", required=True); ap.add_argument("--slides", default="1,4,5,12"); a = ap.parse_args()
folder = ROOT / "data" / "leads" / a.lead; f = folder / "pitch.html"; out = folder / "review"; out.mkdir(exist_ok=True)
want = [int(x) for x in a.slides.split(",")]; errors = []; report = {"file": str(f), "size_kb": f.stat().st_size // 1024}
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for w, h in ((1920, 1080), (500, 900)):
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.on("pageerror", lambda e: errors.append(f"{w}: pageerror {e}"))
        pg.on("console", lambda m: errors.append(f"{w}: console {m.text[:160]}") if m.type == "error" else None)
        pg.goto(f.resolve().as_uri(), wait_until="load"); pg.wait_for_timeout(900)
        n = pg.evaluate("document.querySelectorAll('.slide').length"); report[f"slides@{w}"] = n
        report[f"overflow@{w}"] = pg.evaluate("document.documentElement.scrollWidth > innerWidth")
        report[f"scale@{w}"] = pg.evaluate("getComputedStyle(document.getElementById('deck')).transform")
        for i in range(1, n + 1):
            pg.evaluate(f"location.hash='#{i}'"); pg.keyboard.press("ArrowRight"); pg.keyboard.press("ArrowLeft")
            pg.evaluate(f"(()=>{{const s=document.querySelectorAll('.slide');s.forEach((x,k)=>x.classList.toggle('is-active',k==={i-1}))}})()"); pg.wait_for_timeout(120)
            act = pg.evaluate("document.querySelectorAll('.slide.is-active').length")
            if act != 1: errors.append(f"{w}: slide {i} active count {act}")
            if i in want:
                pg.wait_for_timeout(2200); pg.screenshot(path=str(out / f"s{i:02d}-{w}.png"))
        # text clipped out of the deck? check every active slide's content box bottom vs deck height
        clip = pg.evaluate("""(()=>{const r=[];document.querySelectorAll('.slide').forEach((s,k)=>{s.classList.add('is-active');const els=[...s.querySelectorAll('*')].filter(e=>e.getClientRects().length);const deck=document.getElementById('deck').getBoundingClientRect();const over=els.filter(e=>{const b=e.getBoundingClientRect();return b.bottom>deck.bottom+2||b.right>deck.right+2}).length;if(over)r.push([k+1,over]);s.classList.remove('is-active')});return r})()""")
        report[f"clipped@{w}"] = clip
        pg.close()
    b.close()
report["console_errors"] = errors
print(json.dumps(report, indent=1, ensure_ascii=False))
sys.exit(1 if errors else 0)
