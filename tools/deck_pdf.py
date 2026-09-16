#!/usr/bin/env python3
"""
deck_pdf.py — turn a keyboard-driven HTML deck into a landscape PDF for printing and leaving behind.
Steps through the deck with ArrowRight, waits for each slide's motion to settle, and captures it at 1600x900.

usage: python tools/deck_pdf.py <deck.html> <out.pdf> [--wait 2600]
"""
import argparse, base64, pathlib
from playwright.sync_api import sync_playwright

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck"); ap.add_argument("out"); ap.add_argument("--wait", type=int, default=2600)
    a = ap.parse_args()
    deck = pathlib.Path(a.deck).resolve(); out = pathlib.Path(a.out).resolve()
    shots = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--use-angle=d3d11"])
        pg = b.new_page(viewport={"width": 1600, "height": 900})
        pg.goto(deck.as_uri()); pg.wait_for_timeout(a.wait)
        n = pg.evaluate("document.querySelectorAll('.slide').length")
        for i in range(n):
            shots.append(pg.screenshot(type="jpeg", quality=86))
            if i < n - 1:
                pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(a.wait)
        # one page per slide, no margins, so the printout is the deck as seen
        pages = "".join(f'<img src="data:image/jpeg;base64,{base64.b64encode(s).decode()}">' for s in shots)
        doc = b.new_page()
        doc.set_content(f"<style>@page{{size:297mm 167.06mm;margin:0}}body{{margin:0}}img{{width:297mm;height:167.06mm;display:block;page-break-after:always}}</style>{pages}")
        doc.pdf(path=str(out), width="297mm", height="167.06mm", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    print(f"{out.name}: {n} slides, {out.stat().st_size // 1024} KB")

if __name__ == "__main__":
    main()
