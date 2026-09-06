#!/usr/bin/env python3
"""
letters.py — print-ready A4 Befund letters (HTML, optional PDF via Chromium) from prospects_scored.csv,
following templates/brief-befund.md. Embeds the phone screenshot (data/shots) and a QR to the Befund page.
Writes data/letters/<pid>.html (+ .pdf with --pdf) and data/letters/BATCH.md (checklist for the helper).

usage: python tools/letters.py --segments S1,S4 --districts 1-9,18,19 --top 25 [--pdf]
"""
import argparse, base64, csv, html, pathlib, time
import segno
from common import ROOT, DATA, CFG, OFFERS, slug, load_scored, select, befunde, domain, parse_districts

OUT = DATA / "letters"; OUT.mkdir(exist_ok=True)
CSS = """
@page{size:A4;margin:0}*{box-sizing:border-box}
body{margin:0;font:10.5pt/1.45 Inter,system-ui,Segoe UI,Roboto,sans-serif;color:#161616}
.sheet{width:210mm;height:297mm;padding:16mm 20mm 16mm;position:relative;background:#fff;overflow:hidden}
.top{display:flex;justify-content:space-between;gap:10mm;font-size:8.5pt;color:#6b6b6b;border-bottom:1px solid #161616;padding-bottom:4mm;margin-bottom:9mm}
.top b{color:#161616}.top span:last-child{text-align:right}
.addr{white-space:pre-line;font-size:10.5pt;margin-bottom:7mm}.date{text-align:right;font-size:9.5pt;color:#6b6b6b;margin-bottom:6mm}
h1{font-size:15pt;line-height:1.25;margin:0 0 4mm;letter-spacing:-.01em}
.cols{display:grid;grid-template-columns:1fr 46mm;gap:8mm;align-items:start}
ol{margin:2mm 0 4mm;padding-left:5.5mm}ol li{margin-bottom:1.5mm}
.shot img{width:46mm;border:1px solid #ddd;border-radius:4.5mm;display:block}.shot small{display:block;font-size:7.5pt;color:#6b6b6b;margin-top:2mm;line-height:1.3}
p{margin:0 0 3mm}
.sig{margin-top:5mm}.sig .n{font-weight:600}.sig small{color:#6b6b6b;font-size:9pt}
.qr{position:absolute;right:20mm;bottom:16mm;text-align:center;font-size:7.5pt;color:#6b6b6b;width:34mm}.qr img{width:26mm;display:block;margin:0 auto 1.5mm}
.foot{position:absolute;left:20mm;bottom:16mm;width:118mm;font-size:7pt;color:#8a8a8a;line-height:1.35}
"""

def letter(r, url):
    d = domain(r); bef = befunde(r); name = html.escape(r["name"])
    oid = r["offer"]; oname, ocontent, oprice, odur = OFFERS.get(oid, OFFERS["B1"])
    ref_url, ref_line = CFG["references"].get(r["segment"], CFG["references"]["S1-beratung"])
    ref_short = {"S1-beratung": "eine Steuerberatungskanzlei in Wien", "S2-gesundheit": "einen internationalen Beratungsdienst", "S3-gastro": "fünf Wiener Lokale",
                 "S4-immobilien": "eine Wiener Hausverwaltung", "S5-vereine": "einen Wiener Kulturverein", "S6-studios": "fünf Wiener Lokale", "S7-bildung-kultur": "eine Wiener Sprachschule"}.get(r["segment"], "einen Wiener Betrieb")
    contact = (r.get("names") or "").split(";")[0].strip()
    anrede = f"Guten Tag {html.escape(contact)}," if contact else "Guten Tag,"
    addr = "\n".join(x for x in [contact, r["name"], r["street"], f"{r['postcode']} Wien"] if x)
    qr = segno.make(url, error="m").svg_data_uri(scale=6, border=0, dark="#161616")
    shot = DATA / "shots" / f"{r['pid']}.png"
    fig = f'<div class="shot"><img src="data:image/png;base64,{base64.b64encode(shot.read_bytes()).decode()}"><small>So sieht {html.escape(d)} heute am Handy aus.</small></div>' if shot.exists() else '<div class="shot"><small>[Screenshot am Handy – T2-6]</small></div>'
    if r["website"]:
        h1 = f"Drei Dinge, die uns an {html.escape(d)} aufgefallen sind" if len(bef) >= 3 else f"Was uns an {html.escape(d)} aufgefallen ist"
        opener = f"wir haben uns Ihre Website angesehen, weil wir für {ref_short} gerade genau diese Arbeit gemacht haben. {'Drei Beobachtungen' if len(bef) >= 3 else 'Beobachtungen'}, die Sie in einer Minute selbst nachprüfen können:"
        items = "".join(f"<li>{html.escape(l)}</li>" for l in bef)
        after = "Rechts sehen Sie, was jemand sieht, der Sie am Handy sucht."
    else:
        h1 = "Wer Sie googelt, findet nur eine Adresse"
        opener = f"wenn jemand „{name}“ sucht, erscheinen Ihre Adresse und Ihre Telefonnummer – und sonst nichts: kein Bild, keine Öffnungszeiten, kein Weg, Sie außerhalb der Bürozeiten zu erreichen."
        items = ""; after = ""
    second = ""
    if r["segment"] == "S4-immobilien" and oid != "C1":
        second = f" Für Hausverwaltungen bieten wir außerdem einen <b>{OFFERS['C1'][0]}</b> an ({OFFERS['C1'][2]}): {OFFERS['C1'][1]}."
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Brief {r['pid']} {name}</title><style>{CSS}</style></head><body><div class="sheet">
<div class="top"><span><b>{CFG['sender_name']}</b> · {CFG['sender_role']} · {CFG['studio']}</span><span>{' · '.join(CFG['address_lines'])} · {CFG['phone']} · {CFG['email']}</span></div>
<div class="addr">{html.escape(addr)}</div>
<div class="date">Wien, {time.strftime('%d.%m.%Y')}</div>
<h1>{h1}</h1>
<p>{anrede}</p>
<div class="cols"><div><p>{opener}</p>{'<ol>' + items + '</ol>' if items else ''}<p>{after}</p>
<p><b>Was wir vorschlagen:</b> {oname} – {ocontent}. {oprice}, {odur}. Sie besitzen am Ende Domain, Seite und alle Dateien.{second}</p>
<p><b>Womit wir das belegen:</b> {ref_line} {ref_url}</p>
<p><b>Nächster Schritt:</b> 20 Minuten am Telefon oder bei Ihnen. Termin über den QR-Code unten, oder Sie schreiben mir kurz zurück – dann melde ich mich.</p>
<p>Mit freundlichen Grüßen</p>
<div class="sig"><div style="height:9mm"></div><div class="n">{CFG['sender_name']}</div><small>{CFG['sender_role']} · {CFG['phone']} · {CFG['email']}</small></div>
</div>{fig}</div>
<div class="foot">Ihre Daten stammen aus Ihrem Impressum und öffentlichen Verzeichnissen. Wir speichern nur Firmenname, Adresse und was auf Ihrer Website steht. Ein Wort genügt, und wir löschen den Eintrag.</div>
<div class="qr"><img src="{qr}">Ihre Seite mit Screenshot und Termin</div>
</div></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", default=""); ap.add_argument("--districts", default=""); ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--pids", default=""); ap.add_argument("--min-score", type=int, default=3); ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args()
    rows = select(load_scored(), top=a.top, segments=[s for s in a.segments.split(",") if s], districts=parse_districts(a.districts),
                  min_score=a.min_score, pids=[p for p in a.pids.split(",") if p])
    urls = {x["pid"]: x["url"] for x in csv.DictReader(open(DATA / "befund_urls.csv", encoding="utf-8"))} if (DATA / "befund_urls.csv").exists() else {}
    made = []
    for r in rows:
        url = urls.get(r["pid"]) or f"{CFG['befund_base_url']}/b/{slug(r)}"
        p = OUT / f"{r['pid']}.html"; p.write_text(letter(r, url), encoding="utf-8"); made.append((r, p, url))
    if a.pdf:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch(); pg = b.new_page()
            for r, p, _ in made:
                pg.goto(p.resolve().as_uri()); pg.pdf(path=str(p.with_suffix(".pdf")), format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            b.close()
    with open(OUT / "BATCH.md", "w", encoding="utf-8") as f:
        f.write(f"# Batch — {time.strftime('%Y-%m-%d')} · {len(made)} Briefe\n\nCheckliste je Brief: Befund am Handy geprüft · Name im Impressum bestätigt · Adresse bestätigt · gedruckt · unterschrieben · versendet → `status = gesendet`, `kanal = brief`, `kontaktiert_am`.\n\n| pid | Betrieb | PLZ | Angebot | Ansprechperson | Befund-Seite | ✓ |\n|---|---|---|---|---|---|---|\n")
        for r, p, url in made:
            f.write(f"| {r['pid']} | {r['name']} | {r['postcode']} | {r['offer']} | {(r.get('names') or '').split(';')[0]} | {url} | ☐ |\n")
    print(f"{len(made)} letters → data/letters/ (+pdf: {a.pdf}) · BATCH.md written")

if __name__ == "__main__":
    main()
