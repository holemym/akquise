#!/usr/bin/env python3
"""
shots.py — phone screenshot (390×844, DPR 2) of each selected prospect's homepage.
The picture that goes on the Befund letter. Writes data/shots/<pid>.png (skips existing).

usage: python tools/shots.py --segments S1,S4 --districts 1-9,18,19 --top 40   |   --pids P...,P...
"""
import argparse
from playwright.sync_api import sync_playwright
from common import DATA, load_scored, select, parse_districts

SHOTS = DATA / "shots"; SHOTS.mkdir(exist_ok=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", default=""); ap.add_argument("--districts", default=""); ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--pids", default=""); ap.add_argument("--min-score", type=int, default=3)
    a = ap.parse_args()
    rows = select(load_scored(), top=a.top, segments=[s for s in a.segments.split(",") if s], districts=parse_districts(a.districts),
                  min_score=a.min_score, pids=[p for p in a.pids.split(",") if p])
    rows = [r for r in rows if r["website"]]
    todo = [r for r in rows if not (SHOTS / f"{r['pid']}.png").exists()]
    print(f"{len(rows)} selected with website, {len(todo)} to shoot", flush=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                            locale="de-AT", ignore_https_errors=True)
        for i, r in enumerate(todo, 1):
            pg = ctx.new_page()
            try:
                pg.goto(r["website"], wait_until="load", timeout=25000)
                pg.wait_for_timeout(1800)
                pg.screenshot(path=str(SHOTS / f"{r['pid']}.png"), full_page=False)
                print(f"  {i}/{len(todo)} {r['pid']} ok", flush=True)
            except Exception as e:
                print(f"  {i}/{len(todo)} {r['pid']} FAILED {type(e).__name__}", flush=True)
            finally:
                pg.close()
        b.close()

if __name__ == "__main__":
    main()
