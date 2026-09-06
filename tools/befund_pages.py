#!/usr/bin/env python3
"""
befund_pages.py — one static "Befund" page per selected prospect (the QR target on the letter).
Writes site/b/<slug>.html, site/index.html (blank, noindex), site/vercel.json, and data/befund_urls.csv (pid → url).

usage: python tools/befund_pages.py --segments S1,S4 --districts 1-9,18,19 --top 40
       python tools/befund_pages.py --pids P00012,P00034
Deploy: cd site && npx vercel deploy --prod --yes   (project "befund"; see HUB D7)
"""
import argparse, base64, csv, html, pathlib
from common import ROOT, DATA, CFG, OFFERS, slug, load_scored, select, befunde, domain, parse_districts

SITE = ROOT / "site"; (SITE / "b").mkdir(parents=True, exist_ok=True)

CSS = """
:root{--ink:#161616;--mute:#6b6b6b;--line:#e3e0da;--paper:#faf9f6;--acc:#1d4ed8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:720px;margin:0 auto;padding:40px 22px 80px}
header{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:34px;font-size:13px;color:var(--mute)}
header b{color:var(--ink);font-weight:600}
h1{font-size:clamp(26px,5vw,36px);line-height:1.15;letter-spacing:-.01em;margin:0 0 8px}
.lead{color:var(--mute);margin:0 0 30px}
.grid{display:grid;grid-template-columns:1fr;gap:28px}@media(min-width:640px){.grid{grid-template-columns:1.25fr .75fr}}
ol.bef{list-style:none;margin:0;padding:0;counter-reset:b}ol.bef li{counter-increment:b;padding:14px 0 14px 44px;border-top:1px solid var(--line);position:relative}
ol.bef li::before{content:counter(b,decimal-leading-zero);position:absolute;left:0;top:14px;font-size:13px;color:var(--mute);letter-spacing:.06em}
ol.bef li:last-child{border-bottom:1px solid var(--line)}
.shot{margin:0}.shot img{width:100%;max-width:300px;border:1px solid var(--line);border-radius:22px;display:block;margin:0 auto}
.shot figcaption{font-size:12px;color:var(--mute);text-align:center;margin-top:8px}
section{margin-top:40px}h2{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:0 0 10px;font-weight:600}
.offer{border:1px solid var(--ink);padding:20px 22px;border-radius:6px}.offer .price{font-size:22px;font-weight:600;margin:10px 0 2px}.offer .dur{color:var(--mute);font-size:14px}
.cta{display:inline-block;background:var(--ink);color:#fff;text-decoration:none;padding:13px 20px;border-radius:6px;font-weight:600;margin-top:8px}.cta.sec{background:transparent;color:var(--ink);border:1px solid var(--ink);margin-left:8px}
.proof{color:var(--mute)}.proof a{color:var(--ink)}
footer{margin-top:60px;padding-top:16px;border-top:1px solid var(--line);font-size:12px;color:var(--mute)}
"""

def page(r):
    d = domain(r); name = html.escape(r["name"]); bef = befunde(r)
    oid = r["offer"]; oname, ocontent, oprice, odur = OFFERS.get(oid, OFFERS["B1"])
    ref_url, ref_line = CFG["references"].get(r["segment"], CFG["references"]["S1-beratung"])
    shot = DATA / "shots" / f"{r['pid']}.png"
    if shot.exists():
        b64 = base64.b64encode(shot.read_bytes()).decode()
        fig = f'<figure class="shot"><img src="data:image/png;base64,{b64}" alt="{name} am Handy"><figcaption>So sieht {html.escape(d) or name} heute am Handy aus (390 px, {r.get("kontaktiert_am") or "Stand " + __import__("time").strftime("%d.%m.%Y")})</figcaption></figure>'
    elif not r["website"]:
        fig = '<figure class="shot"><figcaption>Bei der Suche nach Ihrem Namen erscheinen nur Adresse und Telefonnummer.</figcaption></figure>'
    else:
        fig = ""
    second = ""
    if r["segment"] == "S4-immobilien" and oid != "C1":
        c = OFFERS["C1"]; second = f'<p class="proof" style="margin-top:14px">Zweiter Gedanke für Hausverwaltungen: <b>{c[0]}</b> – {c[1]} ({c[2]}).</p>'
    title = (f"Drei Dinge zu {d}" if len(bef) >= 3 else f"Was uns an {d} aufgefallen ist") if d else f"Was man online über {name} findet"
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{html.escape(title)} · {CFG['studio']}</title><style>{CSS}</style></head><body><div class="wrap">
<header><span><b>{CFG['sender_name']}</b> · {CFG['sender_role']}</span><span>{CFG['studio']}</span></header>
<h1>{html.escape(title)}</h1>
<p class="lead">Für {name}, {html.escape(r['postcode'])} Wien. Beobachtungen, die Sie in einer Minute selbst nachprüfen können.</p>
<div class="grid"><div><ol class="bef">{''.join(f'<li>{html.escape(l)}</li>' for l in bef)}</ol></div><div>{fig}</div></div>
<section><h2>Was wir vorschlagen</h2><div class="offer"><b>{oname}</b> – {ocontent}.<div class="price">{oprice}</div><div class="dur">{odur} · Sie besitzen am Ende Domain, Seite und alle Dateien.</div></div>{second}</section>
<section><h2>Womit wir das belegen</h2><p class="proof">{ref_line} <a href="https://{ref_url}" rel="noopener">{ref_url}</a></p></section>
<section><h2>Nächster Schritt</h2><p>20 Minuten am Telefon oder bei Ihnen. Sie hören, was das bei Ihnen konkret bedeuten würde – ohne Verpflichtung.</p>
<a class="cta" href="{html.escape(CFG['booking_url'])}">Termin wählen</a><a class="cta sec" href="tel:{CFG['phone'].replace(' ', '')}">{CFG['phone']}</a></section>
<footer>{CFG['sender_name']} · {CFG['sender_role']} · {' · '.join(CFG['address_lines'])} · {CFG['email']}<br>Diese Seite ist nur über den Link in unserem Brief erreichbar und wird nicht von Suchmaschinen erfasst. Die Beobachtungen stammen von einer automatischen Prüfung Ihrer öffentlichen Website, die wir von Hand bestätigt haben. Ihre Daten: Firmenname, Adresse und was auf Ihrer Website steht – auf Wunsch löschen wir den Eintrag sofort.</footer>
</div></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", default=""); ap.add_argument("--districts", default=""); ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--pids", default=""); ap.add_argument("--min-score", type=int, default=3)
    a = ap.parse_args()
    rows = select(load_scored(), top=a.top, segments=[s for s in a.segments.split(",") if s], districts=parse_districts(a.districts),
                  min_score=a.min_score, pids=[p for p in a.pids.split(",") if p])
    urls = []
    for r in rows:
        s = slug(r); (SITE / "b" / f"{s}.html").write_text(page(r), encoding="utf-8")
        urls.append({"pid": r["pid"], "name": r["name"], "url": f"{CFG['befund_base_url']}/b/{s}"})
    (SITE / "index.html").write_text('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>befund</title>', encoding="utf-8")
    (SITE / "vercel.json").write_text('{"cleanUrls":true,"trailingSlash":false,"headers":[{"source":"/(.*)","headers":[{"key":"X-Robots-Tag","value":"noindex, nofollow"}]}]}', encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    with open(DATA / "befund_urls.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pid", "name", "url"]); w.writeheader(); w.writerows(urls)
    print(f"{len(urls)} pages → site/b/ · urls → data/befund_urls.csv")

if __name__ == "__main__":
    main()
