#!/usr/bin/env python3
"""
einsatz_site.py — the standalone hand-over site for Zeraq's two outreaches (Kartbahn Wien + Notariat Lukanec).
Separate from the Akquise dashboard on purpose: it shows these two clients, the offer list, and nothing else.
An internal tool: white working surface, one component per content type, no theme.

Content: data/einsatz/inhalt.json (gitignored — names, phones, prices)   Files: data/einsatz/*.pdf
Output:  data/public/einsatz-zeraq/<secret>/  → Vercel project einsatz-zeraq (noindex, git-disconnected)

usage: python tools/einsatz_site.py   then   cd data/public/einsatz-zeraq && npx vercel deploy --prod --yes --scope dvisionh
"""
import html, json, re, secrets, shutil
from urllib.parse import urlparse
from common import DATA

SRC = DATA / "einsatz"; OUT = DATA / "public" / "einsatz-zeraq"
SECRET_FILE = SRC / "_secret.txt"
if not SECRET_FILE.exists(): SECRET_FILE.write_text("e-" + secrets.token_hex(6), encoding="utf-8")
SEG = SECRET_FILE.read_text(encoding="utf-8").strip()
ABS = f"/{SEG}"   # root-absolute links: relative ones break under cleanUrls (the 2026-09-08 dashboard bug)
BASE = OUT / SEG
C = json.load(open(SRC / "inhalt.json", encoding="utf-8"))
NBSP_RANGE = re.compile(r"(\d) – (\d)")
def e(s):
    # a price range never breaks around its dash
    return NBSP_RANGE.sub(r"\1 – \2", html.escape(str(s or "")))

CSS = """
:root{--bg:#fff;--ink:#0e0e10;--ink2:#3b3b40;--mute:#7a7a80;--line:#ebebee;--soft:#f5f5f7;--ok:#1d7a4a;--no:#b3261e;--r:10px}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 Inter,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;-webkit-font-smoothing:antialiased;font-feature-settings:"cv11","ss01"}
a{color:inherit}h1,h2,h3,p,ul,ol,dl,dd{margin:0}ul,ol{padding:0;list-style:none}
button{font:inherit;color:inherit;cursor:pointer}
:focus-visible{outline:2px solid var(--ink);outline-offset:2px;border-radius:4px}

/* shell: sticky sidebar on desktop, top bar with scrolling tabs on phones */
.app{display:grid;grid-template-columns:260px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;border-right:1px solid var(--line);padding:28px 16px;display:flex;flex-direction:column;gap:28px}
.brand{padding:0 10px}.brand b{display:block;font-size:15px;font-weight:600;letter-spacing:-.01em}.brand span{font-size:13px;color:var(--mute)}
.nav{display:flex;flex-direction:column;gap:2px}
.nav a{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:8px 10px;border-radius:8px;text-decoration:none;color:var(--ink2);font-size:14px;font-weight:500;white-space:nowrap}
.nav a:hover{background:var(--soft);color:var(--ink)}.nav a[aria-current]{background:var(--soft);color:var(--ink);font-weight:600}
.nav .p{font-size:12px;color:var(--mute);font-variant-numeric:tabular-nums;font-weight:500}.nav .p.done{color:var(--ok)}
.nav .sep{height:1px;background:var(--line);margin:10px}
.side .foot{margin-top:auto;padding:0 10px;font-size:12px;color:var(--mute)}
main{padding:56px 64px 120px;min-width:0}.page{max-width:800px;margin:0 auto}
@media(max-width:900px){
 .app{grid-template-columns:1fr}
 .side{height:auto;z-index:5;background:var(--bg);border-right:0;border-bottom:1px solid var(--line);padding:14px 0 0;gap:10px;min-width:0}
 .brand{padding:0 20px;display:flex;align-items:baseline;gap:8px}.side .foot{display:none}
 .nav{flex-direction:row;overflow-x:auto;gap:4px;padding:0 12px 10px;min-width:0;scrollbar-width:none}.nav::-webkit-scrollbar{display:none}
 .nav .sep{display:none}.nav a{padding:7px 10px}
 main{padding:32px 20px 96px}
}

/* page header */
.eyebrow{font-size:13px;color:var(--mute);margin-bottom:8px}
h1{font-size:34px;line-height:1.15;font-weight:650;letter-spacing:-.025em}
.lead{font-size:17px;color:var(--ink2);margin-top:12px;max-width:640px}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}
.btn{display:inline-flex;align-items:center;gap:8px;height:38px;padding:0 14px;border-radius:8px;border:1px solid var(--line);background:#fff;text-decoration:none;font-size:14px;font-weight:500;white-space:nowrap}
.btn:hover{border-color:#cfcfd4}.btn.primary{background:var(--ink);border-color:var(--ink);color:#fff}.btn.primary:hover{background:#2a2a2e}
.btn svg{width:15px;height:15px;flex:none}

/* sections */
section{margin-top:56px}section>h2{font-size:18px;font-weight:600;letter-spacing:-.01em}
section>.sub{font-size:14px;color:var(--mute);margin-top:2px}
section>h2+*,section>.sub+*{margin-top:16px}
.panel{border:1px solid var(--line);border-radius:var(--r)}
.page>section:first-of-type{margin-top:36px}

.facts{display:grid;grid-template-columns:1fr 1fr}
.facts div{padding:16px 18px;border-top:1px solid var(--line)}.facts div:nth-child(-n+2){border-top:0}.facts div:nth-child(even){border-left:1px solid var(--line)}
.facts dt{font-size:12.5px;color:var(--mute)}.facts dd{font-weight:500;margin-top:2px;overflow-wrap:anywhere}
@media(max-width:560px){.facts{grid-template-columns:1fr}.facts div{border-left:0!important;border-top:1px solid var(--line)!important}.facts div:first-child{border-top:0!important}}

.plain li{position:relative;padding-left:18px;margin:8px 0;color:var(--ink2)}.plain li:first-child{margin-top:0}
.plain li::before{content:"";position:absolute;left:2px;top:.72em;width:5px;height:5px;border-radius:50%;background:#bdbdc2}

/* progress checklist */
.prog-head{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 18px;border-bottom:1px solid var(--line);font-size:14px;color:var(--ink2)}
.prog-head b{font-weight:600;color:var(--ink)}.bar{height:4px;width:120px;background:var(--soft);border-radius:4px;overflow:hidden}.bar i{display:block;height:100%;width:0;background:var(--ok);transition:width .25s ease}
.task{display:grid;grid-template-columns:22px 1fr auto;gap:12px;align-items:start;padding:12px 18px;border-top:1px solid var(--line);cursor:pointer}
.prog-head+.task{border-top:0}.task:hover{background:#fbfbfc}
.task input{appearance:none;width:18px;height:18px;margin:2px 0 0;border:1.5px solid #c4c4ca;border-radius:5px;display:grid;place-content:center;cursor:pointer;background:#fff}
.task input:checked{background:var(--ok);border-color:var(--ok)}
.task input:checked::after{content:"";width:9px;height:5px;border:2px solid #fff;border-top:0;border-right:0;transform:translateY(-1px) rotate(-45deg)}
.task input:checked~.t{color:var(--mute);text-decoration:line-through;text-decoration-color:#c4c4ca}
.task .d{font-size:12.5px;color:var(--mute);font-variant-numeric:tabular-nums;white-space:nowrap;padding-top:2px}

.num{counter-reset:n}.num li{counter-increment:n;position:relative;padding:12px 0 12px 40px;border-top:1px solid var(--line)}.num li:first-child{border-top:0;padding-top:2px}
.num li::before{content:counter(n);position:absolute;left:0;top:10px;width:26px;height:26px;border-radius:50%;background:var(--soft);font-size:13px;font-weight:600;display:grid;place-items:center}
.num li:first-child::before{top:0}.num b{font-weight:600;display:block}.num span{color:var(--ink2)}

.quote{font-size:22px;line-height:1.4;font-weight:550;letter-spacing:-.015em;padding-left:18px;border-left:3px solid var(--ink)}

.rows>div{display:grid;grid-template-columns:180px 1fr;gap:4px 24px;padding:14px 0;border-top:1px solid var(--line)}.rows>div:first-child{border-top:0;padding-top:0}
.rows dt{font-weight:600}.rows dd{color:var(--ink2)}
@media(max-width:560px){.rows>div{grid-template-columns:1fr}}

.script{display:grid;gap:10px}.say{background:var(--soft);border-radius:var(--r);padding:14px 16px}
.say small{display:block;font-size:12.5px;color:var(--mute);margin-bottom:4px}.say p{font-size:16px}
.script+.plain{margin-top:18px}

.copybox{background:var(--soft);border-radius:var(--r);padding:16px 18px}
.copybox p{font-size:15.5px}.copybox .btn{margin-top:14px;height:34px;font-size:13px}
.hint{font-size:13.5px;color:var(--mute);margin-top:12px}

.tiers{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;align-items:stretch}
.tier{border:1px solid var(--line);border-radius:12px;padding:18px;display:flex;flex-direction:column}
.tier.main{border:1.5px solid var(--ink)}
.tier .lab{display:flex;justify-content:space-between;align-items:center;font-size:12.5px;color:var(--mute);height:22px}
.tag{font-size:11.5px;font-weight:600;color:#fff;background:var(--ink);border-radius:5px;padding:3px 7px}
.tier h3{font-size:16px;font-weight:600;margin-top:8px;line-height:1.3}
.price{font-size:22px;font-weight:650;letter-spacing:-.02em;margin-top:10px;font-variant-numeric:tabular-nums;line-height:1.2}
.price small{display:block;font-size:14px;font-weight:500;color:var(--ink2);letter-spacing:0;margin-top:2px}
.tier .time{font-size:13px;color:var(--mute);margin-top:4px}
.tier ul{margin-top:14px;padding-top:14px;border-top:1px solid var(--line);flex:1}
.tier li{position:relative;padding-left:20px;margin:7px 0;font-size:14px;color:var(--ink2)}.tier li:first-child{margin-top:0}
.tier li::before{content:"";position:absolute;left:1px;top:.42em;width:9px;height:5px;border:1.5px solid var(--ink);border-top:0;border-right:0;transform:rotate(-45deg)}
.tier .when{margin-top:14px;padding-top:12px;border-top:1px solid var(--line);font-size:13px;color:var(--ink2)}
@media(max-width:820px){.tiers{grid-template-columns:1fr}}

.cols2{columns:2;column-gap:32px}.cols2 li{break-inside:avoid}@media(max-width:560px){.cols2{columns:1}}

.qa>div{padding:14px 0;border-top:1px solid var(--line)}.qa>div:first-child{border-top:0;padding-top:0}
.qa dt{font-weight:600}.qa dd{color:var(--ink2);margin-top:3px}

.no li{position:relative;padding-left:26px;margin:10px 0;color:var(--ink2)}.no li:first-child{margin-top:0}
.no li::before,.no li::after{content:"";position:absolute;left:2px;top:.78em;width:12px;height:1.5px;background:var(--no);transform:rotate(45deg)}.no li::after{transform:rotate(-45deg)}

.links a{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:13px 18px;border-top:1px solid var(--line);text-decoration:none}
.links a:first-child{border-top:0;border-radius:var(--r) var(--r) 0 0}.links a:last-child{border-radius:0 0 var(--r) var(--r)}.links a:hover{background:var(--soft)}
.links .l{font-weight:500}.links .h{font-size:13.5px;color:var(--mute);overflow-wrap:anywhere;text-align:right}
@media(max-width:560px){.links a{flex-direction:column;align-items:flex-start;gap:2px}.links .h{text-align:left}}

.contact>div{display:flex;align-items:center;gap:12px;padding:10px 12px 10px 18px;border-top:1px solid var(--line)}.contact>div:first-child{border-top:0}
.contact dt{font-size:13px;color:var(--mute);width:64px;flex:none}.contact dd{flex:1;min-width:0;font-weight:500;overflow-wrap:anywhere}
.contact .btn{height:30px;font-size:12.5px;padding:0 10px}

/* overview */
.clients a{display:grid;grid-template-columns:1fr auto;gap:2px 16px;align-items:center;padding:16px 18px;border-top:1px solid var(--line);text-decoration:none}
.clients a:first-child{border-top:0;border-radius:var(--r) var(--r) 0 0}.clients a:last-child{border-radius:0 0 var(--r) var(--r)}.clients a:hover{background:var(--soft)}
.clients b{font-size:16px;font-weight:600}.clients span{font-size:14px;color:var(--mute);grid-column:1}
.clients .go{grid-column:2;grid-row:1/3;font-size:13px;color:var(--ink2);font-weight:500;white-space:nowrap}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r)}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}
th{text-align:left;font-size:12.5px;font-weight:500;color:var(--mute);padding:11px 16px;border-bottom:1px solid var(--line)}
td{padding:12px 16px;border-top:1px solid var(--line);vertical-align:top;color:var(--ink2)}tr:nth-child(2) td{border-top:0}
td:first-child{font-weight:600;color:var(--ink);white-space:nowrap;font-variant-numeric:tabular-nums}td.none{color:#c4c4ca}

/* offers */
.group+.group{margin-top:36px}.group h2{font-size:18px;font-weight:600;letter-spacing:-.01em;margin-bottom:14px}
.offer{padding:16px 18px;border-top:1px solid var(--line);display:grid;grid-template-columns:1fr auto;gap:2px 24px}
.offer:first-child{border-top:0}
.offer b{font-weight:600}.offer .for{grid-column:1;font-size:13.5px;color:var(--mute)}
.offer .pr{grid-column:2;grid-row:1/3;text-align:right;font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}
.offer .pr small{display:block;font-weight:400;font-size:13px;color:var(--mute)}
.offer p{grid-column:1/3;font-size:14px;color:var(--ink2);margin-top:8px}
@media(max-width:560px){.offer{grid-template-columns:1fr}.offer .pr{grid-column:1;grid-row:auto;text-align:left;margin-top:8px;white-space:normal}}
@media print{.side,.btn{display:none}.app{display:block}main{padding:0}}
"""

JS = """
const K=p=>'ez:'+p;
function load(p){try{return JSON.parse(localStorage.getItem(K(p))||'[]')}catch(e){return[]}}
function save(p,v){try{localStorage.setItem(K(p),JSON.stringify(v))}catch(e){}}
function paint(el,p){const n=load(p).filter(Boolean).length,t=+el.dataset.t;el.textContent=n+'/'+t;el.classList.toggle('done',n===t)}
document.querySelectorAll('[data-prog]').forEach(list=>{const p=list.dataset.prog,boxes=[...list.querySelectorAll('input')],st=load(p);
 const upd=()=>{const n=boxes.filter(b=>b.checked).length;list.querySelector('.n').textContent=n;list.querySelector('.bar i').style.width=(n/boxes.length*100)+'%';
  save(p,boxes.map(b=>b.checked));const nav=document.querySelector('.nav [data-p="'+p+'"]');if(nav)paint(nav,p)};
 boxes.forEach((b,i)=>{b.checked=!!st[i];b.addEventListener('change',upd)});upd()});
document.querySelectorAll('.nav [data-p]').forEach(el=>paint(el,el.dataset.p));
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{
 const l=b.querySelector('span'),o=l.textContent;
 try{await navigator.clipboard.writeText(b.dataset.copy);l.textContent='Kopiert'}catch(e){l.textContent='Nicht möglich'}
 setTimeout(()=>l.textContent=o,1600)}));
"""

ICON_DOC = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 1.75h5.5L13 5.25v9H4z"/><path d="M9.25 1.75V5.5H13"/></svg>'
ICON_COPY = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M11 5V3.5A1.5 1.5 0 0 0 9.5 2h-6A1.5 1.5 0 0 0 2 3.5v6A1.5 1.5 0 0 0 3.5 11H5"/></svg>'

def copy_btn(text, label="Kopieren"):
    return f'<button class="btn" type="button" data-copy="{e(text)}">{ICON_COPY}<span>{e(label)}</span></button>'

def sec(title, inner, sub=""):
    return f'<section><h2>{e(title)}</h2>{f"<p class=sub>{e(sub)}</p>" if sub else ""}{inner}</section>'

def bullets(items, cls="plain"):
    return f'<ul class="{cls}">' + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>"

def checklist(key, rows):
    tasks = "".join(f'<label class="task"><input type="checkbox"><span class="t">{e(t)}</span><span class="d">{e(d)}</span></label>' for d, t in rows)
    return f'<div class="panel" data-prog="{key}"><div class="prog-head"><span><b class="n">0</b> von {len(rows)} erledigt</span><span class="bar"><i></i></span></div>{tasks}</div>'

def shell(slug, title, body):
    def item(s, label, prog=False):
        cur = ' aria-current="page"' if s == slug else ""
        p = f'<span class="p" data-p="{s}" data-t="{len(C["clients"][s]["steps"])}"></span>' if prog else ""
        return f'<a href="{ABS}{"/" + s if s else ""}"{cur}><span>{e(label)}</span>{p}</a>'
    nav = item("", "Übersicht") + "".join(item(s, c["short"], True) for s, c in C["clients"].items())
    nav += '<div class="sep"></div>' + item("angebote", "Angebote")
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{e(title)} · Einsatz</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;550;600;650&display=swap" rel="stylesheet"><style>{CSS}</style></head>
<body><div class="app"><aside class="side"><div class="brand"><b>Einsatz</b><span>für {e(C['for'])}</span></div>
<nav class="nav" aria-label="Seiten">{nav}</nav><div class="foot">Stand {e(C['stand'])}</div></aside>
<main><div class="page">{body}</div></main></div><script>{JS}</script></body></html>"""

def tiers_html(tiers, note):
    cards = ""
    for t in tiers:
        tag = '<span class="tag">Im Brief</span>' if t.get("main") else ""
        extra = f'<small>{e(t["extra"])}</small>' if t.get("extra") else ""
        lis = "".join(f"<li>{e(x)}</li>" for x in t["items"])
        cards += (f'<div class="tier{" main" if t.get("main") else ""}"><div class="lab"><span>{e(t["label"])}</span>{tag}</div>'
                  f'<h3>{e(t["name"])}</h3><div class="price">{e(t["price"])}{extra}</div><div class="time">{e(t["time"])}</div>'
                  f'<ul>{lis}</ul><p class="when">{e(t["when"])}</p></div>')
    return f'<div class="tiers">{cards}</div>' + (f'<p class="hint">{e(note)}</p>' if note else "")

def client_page(slug, c):
    files = "".join(f'<a class="btn{" primary" if i == 0 else ""}" href="{ABS}/dateien/{f}">{ICON_DOC}{e(label)}</a>' for i, (f, label) in enumerate(c["files"]))
    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in c["facts"])
    body = f"""<p class="eyebrow">{e(c['place'])}</p><h1>{e(c['name'])}</h1>
<div class="actions">{files}</div>
<section><dl class="panel facts">{facts}</dl></section>
{sec("Die Lage", bullets(c["situation"]))}
{sec("Fortschritt", checklist(slug, c["steps"]), "Wird nur in diesem Browser gespeichert.")}
{sec("Vorher prüfen", '<ol class="num">' + "".join(f"<li>{e(x)}</li>" for x in c["checks"]) + "</ol>", "Am Handy, bevor du jemanden kontaktierst.")}
{sec("Der Aufhänger", f'<p class="quote">„{e(c["hook"])}“</p>')}
{sec("Die Argumente", '<dl class="rows">' + "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in c["arguments"]) + "</dl>")}"""
    v = c.get("visit")
    if v:
        says = "".join(f'<div class="say"><small>{e(k)}</small><p>„{e(t)}“</p></div>' for k, t in v["lines"])
        body += sec(v["title"], f'<div class="script">{says}</div>' + bullets(v["notes"]), v["when"])
    f = c["followup"]
    body += sec(f["title"], f'<div class="copybox"><p>{e(f["text"])}</p>{copy_btn(f["text"], "Text kopieren")}</div><p class="hint">{e(f["note"])}</p>')
    body += sec("Angebote", tiers_html(c["tiers"], c.get("tiers_note")), "Nenne nur die Spanne. Den genauen Preis schreibt David.")
    if c.get("needs"):
        body += sec(c["needs_title"], bullets(c["needs"], "plain cols2"), "Falls gefragt wird, was der Betrieb beitragen muss.")
    body += sec("Einwände", '<dl class="qa">' + "".join(f"<div><dt>„{e(q)}“</dt><dd>{e(a)}</dd></div>" for q, a in c["objections"]) + "</dl>")
    body += sec("Nicht sagen", bullets(c["dont"], "no"))
    def host(u):
        p = urlparse(u); return p.netloc.removeprefix("www.") + p.path.rstrip("/")
    links = "".join(f'<a href="{e(u)}" target="_blank" rel="noopener"><span class="l">{e(l)}</span><span class="h">{e(host(u))} ↗</span></a>' for l, u in c["links"])
    body += sec("Links", f'<div class="panel links">{links}</div>')
    contact = "".join(f'<div><dt>{e(k)}</dt><dd>{e(val)}</dd>{copy_btn(val)}</div>' for k, val in c["contact"])
    body += sec("Kontaktdaten", f'<dl class="panel contact">{contact}</dl>', "Nur für den Rückruf, nachdem sich der Betrieb gemeldet hat.")
    (BASE / f"{slug}.html").write_text(shell(slug, c["name"], body), encoding="utf-8")

def overview():
    o = C["overview"]; cl = C["clients"]
    rows = "".join(f'<a href="{ABS}/{s}"><b>{e(c["name"])}</b><span>{e(c["facts"][-1][1])}</span><span class="go">Öffnen →</span></a>' for s, c in cl.items())
    names = [c["short"] for c in cl.values()]
    trs = "".join("<tr>" + "".join(f'<td class="{"none" if x == "–" else ""}">{e(x)}</td>' for x in r) + "</tr>" for r in o["timeline"])
    body = f"""<h1>{e(o['title'])}</h1><p class="lead">{e(o['lead'])}</p>
{sec("Kontakte", f'<div class="panel clients">{rows}</div>')}
{sec("Vorbereitung", checklist("prep", [("", x) for x in o["prep"]]))}
{sec("Zeitplan", f'<div class="tw"><table><tr><th></th><th>{e(names[0])}</th><th>{e(names[1])}</th></tr>{trs}</table></div>')}
{sec("Regeln", '<ol class="num">' + "".join(f"<li><b>{e(t)}</b><span>{e(d)}</span></li>" for t, d in o["rules"]) + "</ol>")}
{sec("Rückmeldung", bullets(o["report"]), o["report_note"])}"""
    (BASE / "index.html").write_text(shell("", "Übersicht", body), encoding="utf-8")

def offers():
    o = C["offers"]
    groups = ""
    for g in o["groups"]:
        items = "".join(f'<div class="offer"><b>{e(x["name"])}</b><span class="for">{e(x["for"])}</span><span class="pr">{e(x["price"])}<small>{e(x["time"])}</small></span><p>{e(x["what"])}</p></div>' for x in g["items"])
        groups += f'<div class="group"><h2>{e(g["name"])}</h2><div class="panel">{items}</div></div>'
    terms = '<dl class="rows">' + "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in o["terms"]) + "</dl>"
    body = f"""<h1>{e(o['title'])}</h1><p class="lead">{e(o['lead'])}</p>
<section>{groups}</section>
{sec("Bedingungen", terms)}"""
    (BASE / "angebote.html").write_text(shell("angebote", "Angebote", body), encoding="utf-8")

def build():
    if BASE.exists(): shutil.rmtree(BASE)
    (BASE / "dateien").mkdir(parents=True)
    for c in C["clients"].values():
        for f, _ in c["files"]: shutil.copy(SRC / f, BASE / "dateien" / f)
    for s, c in C["clients"].items(): client_page(s, c)
    overview(); offers()
    (OUT / "index.html").write_text('<!DOCTYPE html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>·</title><body style="background:#fff"></body>', encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (OUT / "vercel.json").write_text(json.dumps({"cleanUrls": True, "trailingSlash": False, "headers": [{"source": "/(.*)", "headers": [
        {"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive"}, {"key": "Cache-Control", "value": "private, max-age=0, must-revalidate"}]}]}, indent=1), encoding="utf-8")
    print(f"einsatz-zeraq built: {sum(1 for p in BASE.rglob('*') if p.is_file())} files · entry /{SEG}")

if __name__ == "__main__":
    build()
