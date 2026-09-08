#!/usr/bin/env python3
"""
dashboard.py — static internal dashboard for the lead packages: one overview + one page per client with deck, dossier,
evidence, contacts, offer and the pre-contact checklist. Builds into dash/ (gitignored: third-party data) and is
deployed noindex under an unguessable path.

  python tools/dashboard.py            → dash/index.html (blank), dash/k-<secret>/… (the real thing)
  cd dash && npx vercel deploy --prod --yes --name akquise-dash

Register: tool, not editorial — ink/paper, hairlines, status chips, no metaphor (CLAUDE.md scope for apps/tools).
"""
import csv, html, io, json, pathlib, re, secrets, shutil, time
import markdown
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"; LEADS = DATA / "leads"; OUT = ROOT / "dash"
ORDER = ["lukanec", "kuhn", "roy-real", "novotny", "wiesinger"]
CFG = json.load(open(ROOT / "config.json", encoding="utf-8"))
FIVE = json.load(open(LEADS / "five.json", encoding="utf-8"))
SECRET_FILE = LEADS / "_dash_secret.txt"
if not SECRET_FILE.exists(): SECRET_FILE.write_text("k-" + secrets.token_hex(6), encoding="utf-8")
SEG = SECRET_FILE.read_text(encoding="utf-8").strip()
BASE = OUT / SEG
DATE = time.strftime("%d.%m.%Y")

def esc(s): return html.escape(str(s or ""))
MDMAP = {"OFFERS.md": "angebote.html", "OFFERS.de.md": "angebote.html", "HANDBUCH.md": "handbuch.html", "HANDBUCH.en.md": "handbuch.html",
         "PITCH-5.md": "verkaufsmappe.html", "TIERS.md": "tiers.html", "LEADS.md": "leads.html"}
REPO = "https://github.com/holemym/akquise/blob/main/"
def md(text, depth=0):
    h = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    h = h.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    def link(m):
        href = m.group(1); name = href.split("/")[-1]
        if href.startswith(("http", "mailto:", "#")): return m.group(0)
        if name in MDMAP: return f'href="{"../" * depth}{MDMAP[name]}"'
        lm = re.match(r"(?:\.\./)*leads/([^/]+)/(sources\.md|lead\.json|DOSSIER\.md|pitch\.html)$", href)
        if lm: return f'href="{"../" * depth}{lm.group(1)}/{ {"sources.md": "quellen.html", "lead.json": "dossier.html", "DOSSIER.md": "dossier.html", "pitch.html": "deck.html"}[lm.group(2)] }"'
        if href.rstrip("/").endswith("templates"): return f'href="{REPO}templates"'
        if name.endswith(".md"): return f'href="{REPO}{href.lstrip("./").replace("../", "")}"'
        return m.group(0)
    return re.sub(r'href="([^"]+)"', link, h)

CSS = """
:root{--paper:#faf9f6;--ink:#161616;--mute:#6b6b6b;--faint:#a9a59e;--line:#e3e0da;--line2:#efece6;--ok:#2f6f4f;--warn:#a05a1a;--bad:#a02020}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 Inter,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:inherit}img{max-width:100%;display:block}h1,h2,h3,p,ul,ol{margin:0}
.top{position:sticky;top:0;background:var(--paper);border-bottom:1px solid var(--line);z-index:5}
.top .in{max-width:1180px;margin:0 auto;padding:12px 24px;display:flex;gap:18px;align-items:center;flex-wrap:wrap;font-size:13px}
.top b{font-weight:600}.top a{text-decoration:none;color:var(--mute)}.top a:hover{color:var(--ink)}.top .sp{flex:1}
.wrap{max-width:1180px;margin:0 auto;padding:28px 24px 80px}
h1{font:400 34px/1.15 Fraunces,Georgia,serif;letter-spacing:-.01em}h1 small{font:400 15px Inter,sans-serif;color:var(--mute);display:block;margin-top:6px}
h2{font:600 12px/1 Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mute);margin:40px 0 12px}
h3{font:600 15px/1.3 Inter,sans-serif}
.chip{display:inline-block;font:600 11px/1 Inter,sans-serif;letter-spacing:.06em;text-transform:uppercase;padding:5px 8px;border:1px solid var(--line);border-radius:3px;background:#fff;color:var(--mute);white-space:nowrap}
.chip.hoch,.chip.bad{color:var(--bad);border-color:#e3b9b9}.chip.mittel,.chip.warn{color:var(--warn);border-color:#e8cdb0}.chip.niedrig,.chip.ok{color:var(--ok);border-color:#bcd8c8}
table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;font:600 11px/1 Inter,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--mute);padding:10px 8px;border-bottom:1px solid var(--ink)}
td{padding:12px 8px;border-bottom:1px solid var(--line);vertical-align:top}td.n{font-variant-numeric:tabular-nums;color:var(--mute)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:28px}@media(max-width:800px){.row{grid-template-columns:1fr}}
.card{border:1px solid var(--line);background:#fff;padding:18px 20px}.card+.card{margin-top:14px}
.kv{display:grid;grid-template-columns:160px 1fr;gap:6px 14px;font-size:14px}.kv dt{color:var(--mute)}.kv dd{margin:0;overflow-wrap:anywhere}
.files a{display:inline-block;margin:0 10px 8px 0;padding:9px 13px;border:1px solid var(--ink);text-decoration:none;font-weight:600;font-size:13px;background:#fff}.files a.sec{border-color:var(--line);font-weight:500;color:var(--mute)}
.files a.off{opacity:.4;pointer-events:none}
.find{display:grid;grid-template-columns:120px 1fr;gap:14px;padding:14px 0;border-top:1px solid var(--line)}.find:last-child{border-bottom:1px solid var(--line)}
.find img{border:1px solid var(--line);width:120px}.find dl{display:grid;grid-template-columns:90px 1fr;gap:4px 12px;font-size:13.5px;margin-top:6px}.find dt{color:var(--mute)}.find dd{margin:0}
.phones{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.phones img{border:1px solid var(--line);border-radius:14px}.phones figcaption{font-size:12px;color:var(--mute);margin-top:6px}
.score .r{display:grid;grid-template-columns:170px 1fr 40px;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line2);font-size:14px}.score .bar{height:6px;background:var(--line2)}.score .bar i{display:block;height:100%;background:var(--ink)}.score .why{grid-column:1/4;font-size:12.5px;color:var(--mute);margin-top:-4px}
.lh{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}.lh div{border-top:2px solid var(--ink);padding-top:8px}.lh b{font:400 26px Fraunces,Georgia,serif;display:block}.lh span{font-size:12px;color:var(--mute)}
.comps{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}@media(max-width:800px){.comps{grid-template-columns:1fr}}.comps img{border:1px solid var(--line);aspect-ratio:16/10;object-fit:cover;object-position:top}.comps p{font-size:13.5px;margin-top:6px}.comps .d{font-size:12px;color:var(--mute)}
.check label{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid var(--line2);cursor:pointer;font-size:14.5px}.check input{margin-top:4px;width:16px;height:16px}.check label.done{color:var(--faint);text-decoration:line-through}
.obj{padding:12px 0;border-bottom:1px solid var(--line2);font-size:14px}.obj b{display:block}.obj span{color:var(--mute)}
.src{font-size:12.5px;color:var(--mute);word-break:break-all}
.prose{max-width:820px;font-size:15px}.prose h1{font-size:30px;margin:8px 0 16px}.prose h2{font:600 18px/1.3 Inter,sans-serif;letter-spacing:0;text-transform:none;color:var(--ink);margin:32px 0 10px}.prose h3{margin:22px 0 6px}.prose p,.prose ul,.prose ol{margin:0 0 12px}.prose li{margin:4px 0 4px 18px}.prose table{margin:12px 0}.prose blockquote{margin:12px 0;padding:8px 16px;border-left:3px solid var(--ink);color:var(--mute)}.prose code{font-size:.9em;background:#fff;border:1px solid var(--line);padding:1px 5px}.prose img{border:1px solid var(--line);margin:8px 0}
.note{font-size:13px;color:var(--mute);margin-top:10px}
.warn-box{border:1px solid #e8cdb0;background:#fff8f0;padding:12px 16px;font-size:14px}
.tw{overflow-x:auto}.ov td:first-child{font-weight:600}.ov .hook{color:var(--mute);font-size:13.5px}
"""
JS = """
document.querySelectorAll('.check input').forEach((c,i)=>{const k=location.pathname+'#'+c.dataset.k;try{c.checked=localStorage.getItem(k)==='1'}catch(e){}
const l=c.closest('label');l.classList.toggle('done',c.checked);c.addEventListener('change',()=>{try{localStorage.setItem(k,c.checked?'1':'0')}catch(e){}l.classList.toggle('done',c.checked)})});
"""

def page(title, body, depth=1, nav_extra=""):
    up = "../" * depth
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{esc(title)} · Akquise</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"><style>{CSS}</style></head>
<body><div class="top"><div class="in"><b>Akquise</b><a href="{up}index.html">Übersicht</a><a href="{up}verkaufsmappe.html">Verkaufsmappe</a><a href="{up}handbuch.html">Handbuch</a><a href="{up}angebote.html">Angebote</a><a href="{up}tiers.html">Tiers</a>{nav_extra}<span class="sp"></span><span style="color:var(--faint)">Stand {DATE} · intern</span></div></div>
<div class="wrap">{body}</div><script>{JS}</script></body></html>"""

def webp(src, dst, maxw=900):
    im = Image.open(src).convert("RGB")
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=78, method=6)

def crm_status():
    st = {}
    try:
        for r in csv.DictReader(open(DATA / "prospects_scored.csv", encoding="utf-8")): st[r["pid"]] = r.get("status") or "neu"
    except Exception: pass
    return st

def lead_page(slug, L, folder, status):
    d = BASE / slug; (d / "shots").mkdir(parents=True, exist_ok=True)
    for p in (folder / "shots").glob("*.png"): webp(p, d / "shots" / (p.stem + ".webp"))
    shutil.copy(folder / "pitch.html", d / "deck.html")
    pid = FIVE[slug]["pid"]; has = {}
    for src, dst in ((DATA / "letters" / f"{pid}.pdf", "brief.pdf"), (DATA / "letters" / f"{pid}.html", "brief.html")):
        if src.exists(): shutil.copy(src, d / dst); has[dst] = True
    bef = list((ROOT / "site" / "b").glob(f"*-{pid[-4:].lower()}.html"))
    if bef: shutil.copy(bef[0], d / "befund.html"); has["befund.html"] = True
    doss = md((folder / "DOSSIER.md").read_text(encoding="utf-8"), depth=1); doss = re.sub(r'(shots/[^"\s)]+)\.png', r"\1.webp", doss)
    (d / "dossier.html").write_text(page(f"Dossier · {L['name']}", f'<div class="prose">{doss}</div>', depth=1, nav_extra=f'<a href="index.html">← {esc(L["name"])}</a>'), encoding="utf-8")
    srcs = md((folder / "sources.md").read_text(encoding="utf-8"), depth=1) if (folder / "sources.md").exists() else ""
    (d / "quellen.html").write_text(page(f"Quellen · {L['name']}", f'<div class="prose">{srcs}</div>', depth=1, nav_extra=f'<a href="index.html">← {esc(L["name"])}</a>'), encoding="utf-8")
    c = L["contact"]; O = L["offer"]; lh = L.get("lighthouse") or {}
    def shot(rel): return f"shots/{pathlib.Path(rel).stem}.webp" if rel and (d / "shots" / (pathlib.Path(rel).stem + ".webp")).exists() else ""
    finds = "".join(f'<div class="find">{f"<a href=\"{shot(f.get('shot'))}\"><img src=\"{shot(f.get('shot'))}\" alt=\"\"></a>" if shot(f.get("shot")) else "<div></div>"}<div><span class="chip {esc(f["severity"])}">{esc(f["id"])} · {esc(f["severity"])}</span> <h3 style="display:inline;margin-left:8px">{esc(f["title"])}</h3><dl><dt>Beleg</dt><dd>{esc(f["evidence"])}</dd><dt>Folge</dt><dd>{esc(f["consequence"])}</dd><dt>Was wir tun</dt><dd>{esc(f["fix"])}</dd></dl></div></div>' for f in L["findings"])
    phones = "".join(f'<figure><a href="shots/{n}.webp"><img src="shots/{n}.webp" alt=""></a><figcaption>{cap}</figcaption></figure>' for n, cap in (("m390-vp1", "Bildschirm 1 (mit Banner)"), ("m390-vp2", "Bildschirm 2"), ("m390-vp3", "Bildschirm 3")) if (d / "shots" / f"{n}.webp").exists())
    score = "".join(f'<div class="r"><span>{esc(s["area"])}</span><span class="bar"><i style="width:{int(s["score"])*10}%"></i></span><span class="n">{int(s["score"])}</span><span class="why">{esc(s["why"])}</span></div>' for s in L["scorecard"])
    lhb = f'<div class="lh"><div><b>{esc(lh.get("performance","–"))}</b><span>Performance</span></div><div><b>{esc(lh.get("seo","–"))}</b><span>SEO</span></div><div><b>{esc(lh.get("accessibility","–"))}</b><span>Barrierefreiheit</span></div><div><b>{esc(lh.get("lcp","–"))}</b><span>LCP (Grenze 2,5 s)</span></div></div><p class="note">{esc(lh.get("source",""))}</p>' if lh else '<p class="note">Kein Lighthouse-Wert (Seite nicht direkt messbar).</p>'
    comps = "".join(f'<div>{f"<img src=\"{shot(x.get('shot'))}\" alt=\"\">" if shot(x.get("shot")) else ""}<h3 style="margin-top:8px">{esc(x["name"])}</h3><div class="d">{esc(x.get("district",""))} · <a href="{esc(x.get("website",""))}" rel="noopener">{esc(re.sub(r"^https?://(www\\.)?","",x.get("website","")).rstrip("/"))}</a></div><p>{esc(x["what_their_site_does"])}</p></div>' for x in L["competitors"])
    facts = "".join(f'<dt>{esc(f["label"])}</dt><dd>{esc(f["value"])}</dd>' for f in L["site_today"]["facts"])
    mkt = L["market"]; mf = "".join(f'<li>{esc(x["claim"])}<br><span class="src">{esc(x["source"])}</span></li>' for x in mkt["facts"])
    P = L["prognosis"]; qw = "".join(f'<tr><td class="n">{i+1:02d}</td><td>{esc(q["what"])}<br><span class="src">{esc(q.get("why",""))}</span></td><td><span class="chip">{esc(q.get("effort",""))}</span></td></tr>' for i, q in enumerate(L["quick_wins"]))
    pre = "".join(f'<label><input type="checkbox" data-k="pre{i}"><span>{esc(s)}</span></label>' for i, s in enumerate(L["pre_outreach"]))
    obj = "".join(f'<div class="obj"><b>„{esc(o["say"])}“</b><span>{esc(o["answer"])}</span></div>' for o in L["objections"])
    oq = "".join(f"<li>{esc(q)}</li>" for q in L["open_questions"])
    body = f"""<p><span class="chip">{esc(status)}</span> <span class="chip">{esc(L['category_label'])}</span> <span class="chip">{esc(L['district'])}</span> <span class="chip">{esc(O['lead'])} {esc(O['lead_price'])}</span></p>
<h1 style="margin-top:14px">{esc(L['name'])}<small>{esc(L['one_liner'])}</small></h1>
<h2>Dateien</h2><div class="files"><a href="deck.html">Pitch-Deck</a><a href="dossier.html">Dossier</a><a href="brief.pdf" class="{'' if has.get('brief.pdf') else 'off'}">Brief (PDF)</a><a href="befund.html" class="{'' if has.get('befund.html') else 'off'}">Befund-Seite (QR-Ziel)</a><a href="quellen.html" class="sec">Quellen</a><a href="{esc(L['website'])}" class="sec" rel="noopener">Website des Betriebs ↗</a></div>
<div class="row" style="margin-top:28px"><div class="card"><h3>Kontakt</h3><dl class="kv" style="margin-top:10px"><dt>Person</dt><dd>{esc(c.get('person') or '—')}</dd><dt>Rolle</dt><dd>{esc(c.get('role') or '—')}</dd><dt>Adresse</dt><dd>{esc(c.get('address') or '—')}</dd><dt>Telefon</dt><dd>{esc(c.get('phone') or '—')} <span class="src">(nur für Rückruf nach Antwort)</span></dd><dt>E-Mail</dt><dd>{esc(c.get('email') or '—')} <span class="src">(nie kalt)</span></dd><dt>Website</dt><dd><a href="{esc(L['website'])}" rel="noopener">{esc(L['website'])}</a></dd></dl></div>
<div class="card"><h3>Angebot</h3><dl class="kv" style="margin-top:10px"><dt>Hauptangebot</dt><dd><b>{esc(O['lead'])}</b> · {esc(O['lead_price'])} · {esc(O['lead_duration'])}</dd><dt>Warum</dt><dd>{esc(O['why_this_one'])}</dd><dt>Zweiter Akt</dt><dd>{esc(O.get('second') or '—')}<br><span class="src">{esc(O.get('second_why',''))}</span></dd><dt>Realistisch</dt><dd>{esc(O.get('realistic_total',''))}</dd></dl></div></div>
<h2>Vor dem Kontakt — Checkliste</h2><div class="card check">{pre}</div><p class="note">Häkchen werden nur in diesem Browser gespeichert. Der Status im CRM (`prospects_scored.csv`) bleibt die Wahrheit.</p>
<h2>Kurzprofil</h2><div class="card"><p>{esc(L['profile'])}</p></div>
<h2>Die Website heute</h2><div class="row"><div class="card"><p>{esc(L['site_today']['summary'])}</p><dl class="kv" style="margin-top:14px">{facts}</dl></div><div class="card score"><h3>Bewertung 0–10</h3><div style="margin-top:8px">{score}</div>{lhb}</div></div>
<h2>Am Handy</h2><div class="phones">{phones}</div>
<h2>Befunde</h2><div>{finds}</div>
<h2>Markt und Nische</h2><div class="row"><div class="card"><p>{esc(mkt['summary'])}</p><p class="note"><b>Suchbegriffe:</b> {esc(', '.join(mkt.get('search_terms', [])))}</p><p class="note">{esc(mkt.get('how_clients_find_them',''))}</p></div><div class="card"><ul style="padding-left:18px">{mf}</ul></div></div>
<h2>Wettbewerb</h2><div class="comps">{comps}</div>
<h2>Prognose · {esc(P.get('horizon','12 Monate'))}</h2><div class="row"><div class="card"><h3>Wenn nichts passiert</h3><p style="margin-top:8px">{esc(P['if_nothing_changes'])}</p></div><div class="card" style="border-color:var(--ink)"><h3>Wenn wir es umsetzen</h3><p style="margin-top:8px">{esc(P['if_fixed'])}</p></div></div><p class="note">Annahmen: {esc('; '.join(P.get('assumptions', [])))}</p>
<h2>Sofort machbar</h2><div class="tw"><table><tr><th></th><th>Was</th><th>Aufwand</th></tr>{qw}</table></div>
<h2>Einwände</h2><div>{obj}</div>
<h2>Offen (°)</h2><ul style="padding-left:18px">{oq}</ul>
<h2>Referenz im Gespräch</h2><div class="card">{''.join(f'<p><b>{esc(r["name"])}</b> — {esc(r["line"])}</p>' for r in L['references'])}</div>"""
    (d / "index.html").write_text(page(L["name"], body, depth=1), encoding="utf-8")
    return has

def build():
    if OUT.exists(): shutil.rmtree(OUT)
    BASE.mkdir(parents=True)
    st = crm_status(); rows = []
    for i, s in enumerate(ORDER, 1):
        f = LEADS / s / "lead.json"
        if not f.exists(): continue
        L = json.load(open(f, encoding="utf-8")); has = lead_page(s, L, LEADS / s, st.get(FIVE[s]["pid"], "neu"))
        rows.append(f'<tr><td class="n">{i}</td><td><a href="{s}/index.html">{esc(L["name"])}</a><br><span class="hook">{esc(L["one_liner"])}</span></td><td>{esc(L["category_label"])}<br><span class="hook">{esc(L["district"])}</span></td><td><b>{esc(L["offer"]["lead"])}</b> {esc(L["offer"]["lead_price"])}<br><span class="hook">→ {esc(L["offer"].get("second",""))}</span></td><td><span class="chip">{esc(st.get(FIVE[s]["pid"], "neu"))}</span></td><td class="files"><a href="{s}/deck.html" class="sec">Deck</a><a href="{s}/dossier.html" class="sec">Dossier</a><a href="{s}/brief.pdf" class="sec {"" if has.get("brief.pdf") else "off"}">Brief</a></td></tr>')
    warn = [k for k, v in CFG.items() if isinstance(v, str) and v.startswith("⚠")] + [k for k, v in CFG.items() if isinstance(v, list) and any(str(x).startswith("⚠") for x in v)]
    wb = f'<div class="warn-box"><b>Noch offen in config.json, bevor Briefe rausgehen:</b> {esc(", ".join(warn))}. Dazu: Befund-Seiten deployen (QR-Ziel).</div>' if warn else ""
    body = f"""<h1>Die ersten fünf<small>Verkaufsmappe, Dossiers, Decks und Belege je Betrieb · Reihenfolge = Kontaktreihenfolge</small></h1>
<div style="margin-top:18px">{wb}</div>
<div class="tw" style="margin-top:24px"><table class="ov"><tr><th></th><th>Betrieb</th><th>Kategorie</th><th>Angebot</th><th>Status</th><th>Dateien</th></tr>{''.join(rows)}</table></div>
<h2>Regeln, kurz</h2><div class="card"><ol style="padding-left:18px"><li>Jeden Befund selbst am Handy prüfen; stimmt er nicht, streichen.</li><li>Brief, Vorbeigehen, einzelne LinkedIn-Notiz. Kein Kaltanruf, keine Kalt-E-Mail, kein Kontaktformular (§ 174 TKG).</li><li>Preisspannen nennen, nie Fixpreise. Ziel jedes Kontakts: 20 Minuten mit David.</li><li>Alles, was zurückkommt, ins CRM (`status/kanal/kontaktiert_am/antwort/notiz`) und in INBOX.</li></ol></div>
<h2>Dokumente</h2><div class="files"><a href="verkaufsmappe.html">Verkaufsmappe (PITCH-5)</a><a href="handbuch.html">Handbuch</a><a href="angebote.html">Angebote v1</a><a href="tiers.html">Tiers A–X</a><a href="leads.html" class="sec">Link-Index</a></div>"""
    (BASE / "index.html").write_text(page("Übersicht", body, depth=0), encoding="utf-8")
    for name, src in (("verkaufsmappe", DATA / "PITCH-5.md"), ("handbuch", ROOT / "HANDBUCH.md"), ("angebote", ROOT / "OFFERS.de.md"), ("tiers", DATA / "TIERS.md"), ("leads", DATA / "LEADS.md")):
        if src.exists():
            h = md(src.read_text(encoding="utf-8")); h = re.sub(r'href="(\.\./)+([^"]+)"', r'href="\2"', h); h = re.sub(r'href="leads/([^/"]+)/DOSSIER\.md"', r'href="\1/dossier.html"', h); h = re.sub(r'href="leads/([^/"]+)/pitch\.html"', r'href="\1/deck.html"', h)
            (BASE / f"{name}.html").write_text(page(name.capitalize(), f'<div class="prose">{h}</div>', depth=0), encoding="utf-8")
    (OUT / "index.html").write_text('<!DOCTYPE html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>·</title><body style="background:#faf9f6"></body>', encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (OUT / "vercel.json").write_text(json.dumps({"cleanUrls": True, "trailingSlash": False, "headers": [{"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive"}, {"key": "Cache-Control", "value": "private, max-age=0, must-revalidate"}]}]}, indent=1), encoding="utf-8")
    n = sum(1 for _ in OUT.rglob("*") if _.is_file()); size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) // 1024 // 1024
    print(f"dash/ built: {n} files, {size} MB · entry: /{SEG}/index.html")

if __name__ == "__main__":
    build()
