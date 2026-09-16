#!/usr/bin/env python3
"""
einsatz.py — the two hand-written letters for Zeraq's first run (Kartbahn Wien + Notariat Lukanec).
Same sheet as tools/letters.py, but the copy is written per client instead of assembled from the scorer,
and the QR points at each client's own noindex document (never at the secret dashboard).
Writes data/einsatz/<slug>-brief.html + .pdf.

usage: python tools/einsatz.py
"""
import base64, html, io, pathlib, time
import segno
from PIL import Image
from common import ROOT, DATA, CFG
from letters import CSS

OUT = DATA / "einsatz"; OUT.mkdir(exist_ok=True)
KB = ROOT.parent / "kartbahn"

def img(path, w=520, crop=None):
    """Phone shot as an inline JPEG, optionally cropped to (w:h) ratio from the top."""
    im = Image.open(path).convert("RGB")
    if crop:
        h = int(im.width * crop)
        im = im.crop((0, 0, im.width, min(h, im.height)))
    im.thumbnail((w, 4000))
    b = io.BytesIO(); im.save(b, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

LETTERS = {
    "kartbahn": dict(
        addr=["Herrn Felix Sereinig", "Eko Kartbahn VIE GmbH", "Hosnedlgasse 18", "1220 Wien"],
        anrede="Guten Tag Herr Sereinig,",
        h1="Auf kartbahn-wien.at führen zwei Angebote ins Leere",
        body=[
            "ich habe die Website der In &amp; Outdoor Kartbahn Wien im September geprüft. Drei Punkte, die Sie am Handy selbst nachvollziehen können:",
        ],
        items=[
            "„Gutscheine“ und „Kindergeburtstage“ sind auf der Startseite verlinkt. Beide Seiten gibt es nicht.",
            "Der einzige Buchungslink steht 1.927 Pixel unter dem Seitenanfang.",
            "Auf der Wien-Seite steht der Streckentext aus dem Rosental (450 Meter, vier Hallenbereiche) und „ab 10. April“.",
        ],
        after="Ihr Google-Profil hatte Anfang September 4,5 Sterne aus 46 Bewertungen. Auf der Website steht davon nichts.",
        offer="<b>Was schon fertig ist:</b> eine neue Startseite mit vier Unterseiten (Preise, Kindergeburtstage, Gruppen, Gutscheine), auf Deutsch und Englisch, mit Ihren eigenen Fotos. Sie liegt nicht öffentlich unter <b>kartbahn-wien.vercel.app</b>. Fertigstellen, an rc-timing anbinden und live schalten: <b>4.600 – 6.900 €</b>, zwei bis drei Wochen ab Ihren Angaben. Domain, Seite und Dateien gehören Ihnen.",
        proof="<b>Alle 63 Befunde</b> mit Messwerten und Screenshots: QR-Code unten rechts.",
        nxt="<b>Nächster Schritt:</b> Mein Kollege Zeraq Popal kommt in den nächsten Tagen an der Bahn vorbei und lässt Ihnen eine gedruckte Kurzfassung da. Wenn Sie vorher sprechen möchten, erreichen Sie mich unter der Nummer unten.",
        qr="https://kartbahn-audit.vercel.app", qr_cap="Befund, Kurzfassung und Vorschlag",
        shots=[(KB / "audit/shots/m390-vp1.png", "heute"), (KB / "pitch/assets/redesign-hero-390.webp", "neu")],
    ),
    "lukanec": dict(
        addr=["Frau Mag. Sigrid Lukanec", "Notariat Lukanec", "Heinestraße 36/6", "1020 Wien"],
        anrede="Sehr geehrte Frau Mag. Lukanec,",
        h1="Ihre Startseite gibt Google keine Beschreibung mit",
        body=[
            "ich habe die Website Ihres Notariats geprüft. Drei Punkte, die Sie am Handy selbst nachvollziehen können:",
        ],
        items=[
            "Die Startseite hat weder eine Seitenbeschreibung noch eine Hauptüberschrift. Unter Ihrem Namen setzt Google deshalb einen Textausschnitt, den es selbst wählt.",
            "Am Handy erscheint der größte Inhalt nach 9,2 Sekunden (Messung vom 8. September, simuliertes Mobilnetz). Bis dahin deckt das Cookie-Fenster die halbe Ansicht.",
            "Das jüngste Datum auf der Seite ist „© 2020“, das Eröffnungsjahr Ihrer Kanzlei.",
        ],
        after="Diese Trefferliste sieht, wer zum ersten Mal einen Notar sucht, etwa für einen Kaufvertrag oder eine Vorsorgevollmacht.",
        offer="<b>Was ich vorschlage:</b> Seitenbeschreibungen und Überschriften für alle Seiten, ein schnellerer Aufbau am Handy, ein schlankeres Cookie-Fenster, Ihr Google-Unternehmensprofil und drei Leistungsseiten neu getextet. <b>690 – 1.290 €</b>, zwei Wochen. Ihre Website bleibt, wie sie ist.",
        proof="<b>Womit ich das belege:</b> " + CFG["references"]["S1-beratung"][1] + " loutati.at",
        nxt="<b>Nächster Schritt:</b> Die ganze Auswertung mit einem Vergleich zu Notariaten in Ihrer Nähe finden Sie über den QR-Code. Wenn Sie 20 Minuten darüber sprechen möchten, rufen Sie mich an oder schreiben Sie mir.",
        qr="https://lukanec-befund.vercel.app", qr_cap="Die ganze Auswertung",
        shots=[(DATA / "leads/lukanec/shots/m390-vp1.png", "heute am Handy")],
    ),
}

EXTRA = """
.shots{display:flex;gap:3mm;align-items:flex-start}.shots figure{margin:0;flex:1}
.shots img{width:100%;border:1px solid #ddd;border-radius:3.5mm;display:block}
.shots figcaption{font-size:7.5pt;color:#6b6b6b;margin-top:1.5mm}
.cols.two{grid-template-columns:1fr 54mm}
"""

def letter(slug, L):
    sender_addr = [x for x in CFG["address_lines"] if not x.startswith("⚠")]
    top_right = " · ".join(sender_addr + [CFG["phone"], CFG["email"]])
    qr = segno.make(L["qr"], error="m").svg_data_uri(scale=6, border=0, dark="#161616")
    two = len(L["shots"]) > 1
    figs = "".join(f'<figure><img src="{img(p, crop=1.8 if two else None)}" alt=""><figcaption>{html.escape(c)}</figcaption></figure>' for p, c in L["shots"])
    items = "".join(f"<li>{html.escape(i)}</li>" for i in L["items"])
    body = "".join(f"<p>{b}</p>" for b in L["body"])
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Brief {slug}</title><style>{CSS}{EXTRA}</style></head><body><div class="sheet">
<div class="top"><span><b>{CFG['sender_name']}</b> · {CFG['sender_role']} · {CFG['studio']}</span><span>{top_right}</span></div>
<div class="addr">{html.escape(chr(10).join(L['addr']))}</div>
<div class="date">Wien, {time.strftime('%d.%m.%Y')}</div>
<h1>{html.escape(L['h1'])}</h1>
<p>{html.escape(L['anrede'])}</p>
<div class="cols{' two' if two else ''}"><div>{body}<ol>{items}</ol><p>{html.escape(L['after'])}</p>
<p>{L['offer']}</p>
<p>{L['proof']}</p>
<p>{L['nxt']}</p>
<p>Mit freundlichen Grüßen</p>
<div class="sig"><div style="height:9mm"></div><div class="n">{CFG['sender_name']}</div><small>{CFG['sender_role']} · {CFG['phone']} · {CFG['email']}</small></div>
</div><div class="shots">{figs}</div></div>
<div class="foot">Ihre Daten stammen aus Ihrem Impressum. Wir speichern nur Firmenname, Adresse und was auf Ihrer Website steht. Ein Wort genügt, und wir löschen den Eintrag.</div>
<div class="qr"><img src="{qr}">{html.escape(L['qr_cap'])}</div>
</div></body></html>"""

def main():
    from playwright.sync_api import sync_playwright
    made = []
    for slug, L in LETTERS.items():
        p = OUT / f"{slug}-brief.html"; p.write_text(letter(slug, L), encoding="utf-8"); made.append(p)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 794, "height": 1123})
        for p in made:
            pg.goto(p.resolve().as_uri()); pg.wait_for_timeout(300)
            # a letter that spills past the sheet gets clipped in print: fail loudly instead
            over = pg.evaluate("() => { const s=document.querySelector('.sheet'); const foot=document.querySelector('.foot').getBoundingClientRect().top; const sig=document.querySelector('.sig').getBoundingClientRect().bottom; return {spill: s.scrollHeight > s.clientHeight + 1, gap_sig_to_foot_px: Math.round(foot - sig)} }")
            pg.pdf(path=str(p.with_suffix(".pdf")), format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            pg.screenshot(path=str(p.with_suffix(".png")), full_page=True)
            print(p.name, over)
        b.close()

if __name__ == "__main__":
    main()
