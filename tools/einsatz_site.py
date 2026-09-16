#!/usr/bin/env python3
"""
einsatz_site.py — the standalone hand-over site for Zeraq's two outreaches (Kartbahn Wien + Notariat Lukanec).
Separate from the Akquise dashboard on purpose: it shows these two clients and nothing else from the pipeline.
Reuses the dashboard's stylesheet so both tools look like one studio system.

Sources: data/einsatz/UEBERSICHT.md · KARTBAHN.md · LUKANEC.md · *-brief.pdf · leave-behind PDFs
Output:  data/public/einsatz-zeraq/<secret>/  → Vercel project einsatz-zeraq (noindex)

usage: python tools/einsatz_site.py   then   cd data/public/einsatz-zeraq && npx vercel deploy --prod --yes --scope dvisionh
"""
import html, json, secrets, shutil, time
from common import DATA
from dashboard import CSS, JS, md

SRC = DATA / "einsatz"; OUT = DATA / "public" / "einsatz-zeraq"
SECRET_FILE = SRC / "_secret.txt"
if not SECRET_FILE.exists(): SECRET_FILE.write_text("e-" + secrets.token_hex(6), encoding="utf-8")
SEG = SECRET_FILE.read_text(encoding="utf-8").strip()
ABS = f"/{SEG}"   # root-absolute links: relative ones break under cleanUrls (the 2026-09-08 dashboard bug)
BASE = OUT / SEG
DATE = time.strftime("%d.%m.%Y")
def esc(s): return html.escape(str(s or ""))

CLIENTS = {
    "kartbahn": dict(
        name="In & Outdoor Kartbahn Wien", short="Kartbahn Wien",
        line="Eko Kartbahn VIE GmbH · Hosnedlgasse 18, 1220 Wien · Felix Sereinig",
        chips=["Website fertig gebaut", "4.600 – 6.900 €", "Brief + Besuch"],
        files=[("kartbahn-brief.pdf", "Brief"), ("kartbahn-kurzfassung.pdf", "Kurzfassung zum Dalassen")],
        links=[("https://kartbahn-wien.vercel.app", "Neue Website (Demo)"), ("https://kartbahn-audit.vercel.app", "Kunden-Link (QR im Brief)"),
               ("https://kartbahn-audit.vercel.app/befund", "Befund, 17 Seiten"), ("https://kartbahn-audit.vercel.app/vorschlag", "Vorschlag, 15 Seiten"),
               ("https://www.kartbahn-wien.at", "Ihre Seite heute")],
        steps=["Befunde am Handy nachgeprüft", "Brief abgeschickt (David)", "Kurzfassung gedruckt", "Besuch an der Bahn, Kurzfassung abgegeben",
               "Name der Ansprechperson notiert", "LinkedIn-Notiz an Felix Sereinig (Tag 14)", "Antwort erhalten", "Termin mit David vereinbart"],
        md="KARTBAHN.md"),
    "lukanec": dict(
        name="Notariat Lukanec", short="Notariat Lukanec",
        line="Mag. Sigrid Lukanec · Heinestraße 36/6, 1020 Wien",
        chips=["Google-Sichtbarkeit", "690 – 1.290 € + 290 €/Monat", "Brief + LinkedIn"],
        files=[("lukanec-brief.pdf", "Brief"), ("lukanec-auswertung.pdf", "Auswertung zum Dalassen")],
        links=[("https://lukanec-befund.vercel.app", "Kunden-Link (QR im Brief)"), ("https://www.notar-lukanec.at", "Ihre Seite heute")],
        steps=["Befunde am Handy nachgeprüft", "Google-Suche als Screenshot an David geschickt", "Brief abgeschickt (David)", "LinkedIn-Profil gesucht",
               "LinkedIn-Notiz oder Auswertung abgegeben (Tag 10)", "Antwort erhalten", "Termin mit David vereinbart"],
        md="LUKANEC.md"),
}

def page(title, body):
    nav = "".join(f'<a href="{ABS}/{s}">{esc(c["short"])}</a>' for s, c in CLIENTS.items())
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{esc(title)} · Einsatz</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"><style>{CSS}
.prose ul li.check{{margin-left:0}}
.clients{{border-top:1px solid var(--ink);margin-top:26px}}.cl{{display:grid;grid-template-columns:1fr auto;gap:10px 24px;padding:20px 0;border-bottom:1px solid var(--line);align-items:start}}
.cl h3{{font:400 26px/1.2 Fraunces,Georgia,serif}}.cl p{{color:var(--mute);font-size:14px;margin-top:4px}}.cl .files{{margin-top:4px}}
@media(max-width:700px){{.cl{{grid-template-columns:1fr}}}}</style></head>
<body><div class="top"><div class="in"><b>Einsatz</b><a href="{ABS}">Übersicht</a>{nav}<span class="sp"></span><span style="color:var(--faint)">Stand {DATE} · intern</span></div></div>
<div class="wrap">{body}</div><script>{JS}</script></body></html>"""

def client_page(slug, c):
    files = "".join(f'<a href="{ABS}/dateien/{f}">{esc(label)}</a>' for f, label in c["files"])
    links = "".join(f'<a href="{u}" class="sec" rel="noopener">{esc(label)} ↗</a>' for u, label in c["links"])
    chips = " ".join(f'<span class="chip">{esc(x)}</span>' for x in c["chips"])
    steps = "".join(f'<label><input type="checkbox" data-k="s{i}"><span>{esc(s)}</span></label>' for i, s in enumerate(c["steps"]))
    guide = md((SRC / c["md"]).read_text(encoding="utf-8"))
    body = f"""<p>{chips}</p>
<h1 style="margin-top:14px">{esc(c['name'])}<small>{esc(c['line'])}</small></h1>
<h2>Zum Drucken</h2><div class="files">{files}</div>
<h2>Links</h2><div class="files">{links}</div>
<h2>Verlauf</h2><div class="card check">{steps}</div><p class="note">Häkchen bleiben nur in diesem Browser gespeichert. Was zählt, ist deine Nachricht an David.</p>
<h2>Leitfaden</h2><div class="prose">{guide}</div>"""
    (BASE / f"{slug}.html").write_text(page(c["name"], body), encoding="utf-8")

def build():
    if BASE.exists(): shutil.rmtree(BASE)
    (BASE / "dateien").mkdir(parents=True)
    for c in CLIENTS.values():
        for f, _ in c["files"]: shutil.copy(SRC / f, BASE / "dateien" / f)
    for s, c in CLIENTS.items(): client_page(s, c)
    rows = "".join(f'''<div class="cl"><div><h3><a href="{ABS}/{s}" style="text-decoration:none">{esc(c["name"])}</a></h3><p>{esc(c["line"])}</p><p>{" · ".join(esc(x) for x in c["chips"])}</p></div>
<div class="files"><a href="{ABS}/{s}">Leitfaden</a><a href="{ABS}/dateien/{c["files"][0][0]}" class="sec">Brief</a></div></div>''' for s, c in CLIENTS.items())
    body = f"""<h1>Kartbahn Wien und Notariat Lukanec<small>Für Zeraq Popal · Briefe, Unterlagen und Gesprächsleitfaden für beide Kontakte</small></h1>
<div class="clients">{rows}</div>
<div class="prose" style="margin-top:32px">{md((SRC / "UEBERSICHT.md").read_text(encoding="utf-8"))}</div>"""
    (BASE / "index.html").write_text(page("Übersicht", body), encoding="utf-8")
    (OUT / "index.html").write_text('<!DOCTYPE html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>·</title><body style="background:#faf9f6"></body>', encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (OUT / "vercel.json").write_text(json.dumps({"cleanUrls": True, "trailingSlash": False, "headers": [{"source": "/(.*)", "headers": [
        {"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive"}, {"key": "Cache-Control", "value": "private, max-age=0, must-revalidate"}]}]}, indent=1), encoding="utf-8")
    n = sum(1 for p in BASE.rglob("*") if p.is_file())
    print(f"einsatz-zeraq built: {n} files · entry /{SEG}")

if __name__ == "__main__":
    build()
