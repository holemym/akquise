#!/usr/bin/env python3
"""
pitch.py — render the per-lead pitch deck (German, single self-contained HTML) from data/leads/<slug>/lead.json.

  python tools/pitch.py --lead lukanec        → data/leads/lukanec/pitch.html
  python tools/pitch.py --lead all

Brief block (CLAUDE.md §2), fixed for every deck in this project:
  positioning  — "Wir haben Ihre Website angesehen. Hier ist, was wir gesehen haben, was es Sie kostet, und was wir tun würden."
  audience     — one owner/partner of a small Vienna practice, reading on a laptop in a 20-minute call or alone on a phone
  register     — quiet legal paper: ink on paper, hairlines, a serif display, one accent taken from THEIR own brand colour
  signature    — the phone slide: their site on a real 390-px phone, three findings pinned to it. Everything else stays calm.
  kill list    — no tile grids, no glow, no gradient text, no stacked entrance animation, no marketing pills, no "Digitalisierung"
  palette      — paper #faf9f6 · ink #161616 · lead accent from lead.json (their logo/site), never a default blue

Mechanics reuse the studio deck stage (fixed 1600×900, scaled to the window, ← → keys, progress line). Images are inlined
as WebP data URIs (≤ 1400 px) so the file travels as one attachment. Google Fonts are inlined when the network allows.
"""
import argparse, base64, html, io, json, pathlib, re, sys, time, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEADS = ROOT / "data" / "leads"
CFG = json.load(open(ROOT / "config.json", encoding="utf-8"))
OFFERS_MD = (ROOT / "OFFERS.de.md").read_text(encoding="utf-8")
FONT_CSS = "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&display=swap"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def esc(s): return html.escape(str(s or ""))

def img_uri(path, maxw=1400, q=80):
    """WebP data URI, downscaled. Missing file → '' (the slide hides the figure)."""
    p = pathlib.Path(path)
    if not p.exists(): return ""
    im = Image.open(p).convert("RGB")
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=q, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()

FONT_CACHE = LEADS / "_fonts.css"
def fonts_css():
    if FONT_CACHE.exists() and FONT_CACHE.stat().st_size > 10000: return FONT_CACHE.read_text(encoding="utf-8")
    css = _fonts_css_fetch()
    if css: FONT_CACHE.write_text(css, encoding="utf-8")
    return css

def _fonts_css_fetch():
    try:
        req = urllib.request.Request(FONT_CSS, headers={"User-Agent": UA}); css = urllib.request.urlopen(req, timeout=15).read().decode()
        def repl(m):
            data = urllib.request.urlopen(urllib.request.Request(m.group(1), headers={"User-Agent": UA}), timeout=15).read()
            return f"url(data:font/woff2;base64,{base64.b64encode(data).decode()})"
        return re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", repl, css)
    except Exception as e:
        print("  fonts not inlined:", type(e).__name__, file=sys.stderr); return ""

def offer_block(oid):
    """Pull the row for an offer id out of OFFERS.de.md → (name, contents, price, duration)."""
    for line in OFFERS_MD.splitlines():
        if line.startswith(f"| **{oid}**"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 6:
                return (cells[1].replace("**", "").strip(), cells[3], cells[4].replace("**", ""), cells[5])
    return (oid, "", "", "")

CSS = """
:root{--paper:#faf9f6;--ink:#161616;--mute:#6b6b6b;--faint:#a9a59e;--line:#e3e0da;--line2:#efece6;--acc:ACCENT;--ease:cubic-bezier(.16,1,.3,1);
--fd:'Fraunces',Georgia,'Times New Roman',serif;--fb:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
*{box-sizing:border-box}html,body{height:100%;margin:0;background:#e9e6e0;overflow:hidden}
body{font-family:var(--fb);color:var(--ink);-webkit-font-smoothing:antialiased}
img{display:block;max-width:100%}a{color:inherit}h1,h2,h3,p,ul,ol,figure{margin:0}ul,ol{padding:0;list-style:none}
button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer}
.stage{position:fixed;inset:0}
.deck{position:absolute;left:50%;top:50%;width:1600px;height:900px;background:var(--paper);transform:translate(-50%,-50%);transform-origin:center;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.18)}
.bar{position:absolute;left:0;right:0;top:0;height:64px;display:flex;align-items:center;justify-content:space-between;padding:0 64px;z-index:20;font:500 12px/1 var(--fb);letter-spacing:.04em;color:var(--mute)}
.bar b{color:var(--ink);font-weight:600}.bar .acc{display:inline-block;width:10px;height:10px;background:var(--acc);margin-right:10px;vertical-align:-1px}
.counter{font-variant-numeric:tabular-nums}
.progress{position:absolute;left:0;bottom:0;height:2px;width:0;background:var(--acc);transition:width .6s var(--ease);z-index:20}
.nav{position:absolute;right:64px;bottom:30px;display:flex;gap:6px;z-index:20}
.nav button{width:40px;height:40px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;transition:background .25s,border-color .25s}
.nav button:hover{background:var(--ink);color:var(--paper);border-color:var(--ink)}.nav button[disabled]{opacity:.25;pointer-events:none}
.foot{position:absolute;left:64px;bottom:40px;font:400 12px var(--fb);color:var(--faint);z-index:19}
.slide{position:absolute;inset:0;padding:96px 64px 84px;opacity:0;visibility:hidden;transform:translateY(14px);transition:opacity .45s ease,transform .8s var(--ease),visibility 0s linear .45s}
.slide.is-active{opacity:1;visibility:visible;transform:none;transition:opacity .5s ease .05s,transform .8s var(--ease),visibility 0s}
[data-reveal]{opacity:0;transform:translateY(10px);transition:opacity .5s ease,transform .8s var(--ease);transition-delay:calc(var(--i,0)*50ms + 120ms)}
.is-active [data-reveal]{opacity:1;transform:none}
.no-motion .slide,.no-motion [data-reveal]{transition:none!important;transform:none!important}
.eyebrow{font:500 11px/1 var(--fb);letter-spacing:.2em;text-transform:uppercase;color:var(--mute);margin-bottom:16px}
.eyebrow i{display:inline-block;width:22px;height:2px;background:var(--acc);vertical-align:3px;margin-right:10px}
h2{font:400 46px/1.08 var(--fd);letter-spacing:-.015em;max-width:1200px;font-variation-settings:'opsz' 96}
h2 em{font-style:italic;color:var(--acc)}
.sub{font:400 17px/1.55 var(--fb);color:var(--mute);margin-top:14px;max-width:880px}
h3{font:600 15px/1.35 var(--fb)}
.hair{border-top:1px solid var(--line)}
/* cover */
.cover{padding:0;display:grid;grid-template-columns:1fr 560px}
.cover .l{padding:120px 64px 84px;display:flex;flex-direction:column;justify-content:space-between}
.cover h1{font:400 66px/1.05 var(--fd);letter-spacing:-.02em;max-width:900px;font-variation-settings:'opsz' 144}
.cover h1 em{font-style:italic;color:var(--acc)}
.cover .meta{font:400 14px/1.6 var(--fb);color:var(--mute)}.cover .meta b{color:var(--ink);font-weight:600}
.cover .r{background:var(--ink);position:relative;overflow:hidden}
.cover .r img{position:absolute;left:50%;top:50%;width:300px;transform:translate(-50%,-50%);border-radius:28px;border:6px solid #2a2a2a;box-shadow:0 30px 70px rgba(0,0,0,.5)}
.cover .r .cap{position:absolute;left:40px;bottom:40px;right:150px;font:400 12px/1.5 var(--fb);color:rgba(250,249,246,.55)}
/* two-col */
.cols{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}.cols.w{grid-template-columns:1.2fr .8fr}.cols.n{grid-template-columns:.8fr 1.2fr}
/* fact rows */
.facts{margin-top:8px}.fact{display:grid;grid-template-columns:230px 1fr;gap:20px;padding:13px 0;border-top:1px solid var(--line);font-size:15px;line-height:1.45}
.fact:last-child{border-bottom:1px solid var(--line)}.fact .k{color:var(--mute)}.fact .v{font-weight:500}
/* shots */
.shot{border:1px solid var(--line);background:#fff;overflow:hidden}.shot img{width:100%}.cap{font:400 12px/1.5 var(--fb);color:var(--mute);margin-top:8px}
.scroller{height:640px;overflow:hidden;position:relative}.scroller img{width:100%}
.scroller::after{content:"";position:absolute;left:0;right:0;bottom:0;height:120px;background:linear-gradient(transparent,var(--paper))}
/* phone slide */
.phones{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;align-items:start}
.phone{position:relative;border-radius:26px;border:5px solid #1e1e1e;background:#000;overflow:hidden;width:300px;margin:0 auto;box-shadow:0 24px 50px rgba(0,0,0,.22)}
.phone img{width:100%}
.pin{position:absolute;left:0;right:0;bottom:0;background:var(--ink);color:var(--paper);padding:12px 14px;font:400 13px/1.4 var(--fb)}
.pin b{display:block;font-weight:600;color:var(--paper)}.pin .n{position:absolute;right:12px;top:-14px;width:28px;height:28px;border-radius:50%;background:var(--acc);color:#fff;display:grid;place-items:center;font:600 13px var(--fb)}
/* scorecard */
.score{margin-top:10px}.srow{display:grid;grid-template-columns:200px 1fr 60px;gap:18px;align-items:center;padding:12px 0;border-top:1px solid var(--line)}
.srow:last-child{border-bottom:1px solid var(--line)}.srow .a{font-weight:500}.srow .bar2{height:8px;background:var(--line2);position:relative}
.srow .bar2 i{position:absolute;left:0;top:0;bottom:0;background:var(--acc);width:0;transition:width 1s var(--ease) .3s}.is-active .srow .bar2 i{width:var(--w)}
.srow .n{font:600 18px var(--fd);text-align:right;font-variant-numeric:tabular-nums}.srow .why{grid-column:2/4;font-size:13px;color:var(--mute);margin-top:-6px}
.lh{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:26px}
.lh div{border-top:2px solid var(--acc);padding-top:10px}.lh .v{font:400 40px/1 var(--fd);letter-spacing:-.01em}.lh .l{font-size:13px;color:var(--mute);margin-top:6px}
/* findings */
.finding{padding:20px 0;border-top:1px solid var(--line)}.finding:last-child{border-bottom:1px solid var(--line)}
.finding .t{display:flex;align-items:baseline;gap:14px}.finding .id{font:600 11px var(--fb);letter-spacing:.14em;color:var(--acc)}
.finding h3{font:500 20px/1.3 var(--fd)}.finding .sev{margin-left:auto;font:500 11px var(--fb);letter-spacing:.12em;text-transform:uppercase;color:var(--mute)}
.finding .sev.hoch{color:var(--acc)}
.finding dl{display:grid;grid-template-columns:110px 1fr;gap:6px 16px;margin-top:12px;font-size:14px;line-height:1.5}
.finding dt{color:var(--mute)}.finding dd{margin:0}.finding dd.fix{font-weight:500}
/* market / competitors / prognosis */
.src{display:block;font-size:12px;color:var(--faint);margin-top:4px;word-break:break-all}
.terms{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.terms span{font:500 13px var(--fb);padding:6px 10px;border:1px solid var(--line);background:#fff}
.comps{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}.comp .shot img{aspect-ratio:16/10;object-fit:cover;object-position:top}
.comp h3{margin-top:12px}.comp .d{font-size:13px;color:var(--mute)}.comp p{font-size:14px;line-height:1.5;margin-top:8px}
.prog{display:grid;grid-template-columns:1fr 1fr;gap:40px}.prog div{padding:26px 28px;border:1px solid var(--line);background:#fff;font-size:16px;line-height:1.6}
.prog div.b{border-color:var(--acc)}.prog h3{font:400 24px/1.2 var(--fd);margin-bottom:12px}
.assump{font-size:12.5px;color:var(--mute);margin-top:18px;line-height:1.5}
/* quick wins / pre / objections */
.list{margin-top:6px}.list li{display:grid;grid-template-columns:44px 1fr auto;gap:16px;padding:14px 0;border-top:1px solid var(--line);font-size:15px;line-height:1.5}
.list li:last-child{border-bottom:1px solid var(--line)}.list .n{font:400 22px/1 var(--fd);color:var(--acc)}.list .e{font:600 11px var(--fb);letter-spacing:.1em;color:var(--mute);align-self:start;padding-top:4px}
.list .why{color:var(--mute);display:block;font-size:13.5px;margin-top:3px}
/* offer */
.offer{display:grid;grid-template-columns:1.1fr .9fr;gap:56px}.obox{border:1px solid var(--ink);padding:30px 32px;background:#fff}
.obox .n{font:400 32px/1.15 var(--fd)}.obox .p{font:400 44px/1 var(--fd);margin:18px 0 6px;letter-spacing:-.01em}.obox .d{color:var(--mute);font-size:14px}
.obox p{font-size:15px;line-height:1.55;margin-top:16px}
.second{margin-top:22px;padding:20px 24px;border-left:3px solid var(--acc);background:#fff;font-size:15px;line-height:1.55}
.second b{display:block;margin-bottom:4px}
.cond{font-size:13.5px;line-height:1.6;color:var(--mute)}.cond li{padding:6px 0;border-top:1px solid var(--line2)}
.total{margin-top:22px;font-size:15px}.total b{font:400 26px var(--fd);display:block;margin-top:4px}
/* close */
.close{display:grid;grid-template-columns:1fr 1fr;gap:56px}
.ref{padding:18px 0;border-top:1px solid var(--line);font-size:15px;line-height:1.5}.ref b{display:block;font-weight:600}
.cta{margin-top:26px;display:flex;gap:12px;flex-wrap:wrap}.cta a{display:inline-block;padding:14px 22px;font:600 15px var(--fb);text-decoration:none;background:var(--ink);color:var(--paper)}
.cta a.sec{background:transparent;color:var(--ink);border:1px solid var(--ink)}
.small{font-size:12.5px;color:var(--mute);line-height:1.55;margin-top:20px}
"""

JS = """
(()=>{const deck=document.getElementById('deck'),slides=[...deck.querySelectorAll('.slide')],counter=deck.querySelector('.counter'),prog=document.getElementById('progress'),prev=document.getElementById('prev'),next=document.getElementById('next');
const R=matchMedia('(prefers-reduced-motion: reduce)').matches||new URLSearchParams(location.search).has('static');if(R)document.documentElement.classList.add('no-motion');
let cur=-1;function go(i){i=Math.max(0,Math.min(slides.length-1,i));if(i===cur)return;slides.forEach((s,k)=>s.classList.toggle('is-active',k===i));cur=i;counter.textContent=String(i+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');prog.style.width=((i+1)/slides.length*100)+'%';prev.disabled=i===0;next.disabled=i===slides.length-1;history.replaceState(null,'','#'+(i+1))}
function fit(){const s=Math.min(innerWidth/1600,innerHeight/900);deck.style.transform='translate(-50%,-50%) scale('+s+')'}
addEventListener('resize',fit);fit();prev.onclick=()=>go(cur-1);next.onclick=()=>go(cur+1);
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();go(cur+1)}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(cur-1)}if(e.key==='Home')go(0);if(e.key==='End')go(slides.length-1)});
let tx=null;addEventListener('touchstart',e=>tx=e.touches[0].clientX,{passive:true});addEventListener('touchend',e=>{if(tx==null)return;const d=e.changedTouches[0].clientX-tx;if(Math.abs(d)>50)go(cur+(d<0?1:-1));tx=null});
go(Math.max(0,(parseInt(location.hash.slice(1))||1)-1))})();
"""

def slide(inner, cls=""):
    return f'<section class="slide {cls}">{inner}</section>'

def render(L, folder):
    acc = L.get("accent") or "#161616"
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", acc): acc = "#161616"
    sh = lambda rel: img_uri(folder / rel) if rel else ""
    date = time.strftime("%d.%m.%Y")
    name, dom = esc(L["name"]), esc(re.sub(r"^https?://(www\.)?", "", L["website"]).rstrip("/"))
    S = []
    # 1 cover
    vp1 = sh("shots/m390-vp1b.png") or sh("shots/m390-vp1.png")   # banner dismissed if we managed to
    S.append(f'''<section class="slide cover"><div class="l"><div><div class="eyebrow"><i></i>{name} · {esc(L.get("district",""))}</div>
<h1>{esc(L["pitch_title"]).replace(dom, f"<em style=\"white-space:nowrap\">{dom}</em>")}</h1></div>
<div class="meta"><b>{esc(CFG["sender_name"])}</b> · {esc(CFG["sender_role"])} · {esc(CFG["studio"])}<br>Befund und Vorschlag · {date} · vertraulich, nur für {esc(L["contact"].get("person") or name)}</div></div>
<div class="r">{f'<img src="{vp1}" alt="">' if vp1 else ''}<div class="cap">{dom} am Handy, {date}, 390 px breit. So sieht die Seite aus, wenn jemand Sie unterwegs sucht.</div></div></section>''')
    # 2 profile + why
    facts = "".join(f'<div class="fact" data-reveal style="--i:{i}"><span class="k">{esc(f["label"])}</span><span class="v">{esc(f["value"])}</span></div>' for i, f in enumerate(L["site_today"]["facts"][:8]))
    S.append(slide(f'''<div class="eyebrow"><i></i>Warum wir Ihnen schreiben</div><h2>{esc(L["one_liner"])}</h2>
<div class="cols" style="margin-top:40px"><div><h3>Was wir über Sie gelesen haben</h3><p class="sub" style="margin-top:10px">{esc(L["profile"])}</p></div>
<div><h3>{dom} in Zahlen</h3><div class="facts">{facts}</div></div></div>'''))
    # 3 site today (desktop)
    full = sh("shots/desk-full.png")
    S.append(slide(f'''<div class="eyebrow"><i></i>Die Website heute · Desktop</div><h2>Was ein Besucher am Laptop sieht</h2>
<div class="cols n" style="margin-top:28px"><div><p class="sub" style="margin-top:0">{esc(L["site_today"]["summary"])}</p></div>
<figure><div class="shot scroller">{f'<img src="{full}" alt="">' if full else ''}</div><figcaption class="cap">{dom} bei 1.440 px Breite, {date}. Ausschnitt der gesamten Startseite.</figcaption></figure></div>'''))
    # 4 phone (signature)
    F = L["findings"]
    phones = ""
    for i, vp in enumerate(("m390-vp1.png", "m390-vp2.png", "m390-vp3.png")):
        u = sh(f"shots/{vp}"); f = F[i] if i < len(F) else None
        ev = f["evidence"] if f else ""
        if len(ev) > 130: ev = ev[:130].rsplit(" ", 1)[0].rstrip(",;:") + " …"   # cut at a word, never mid-word
        pin = f'<div class="pin"><span class="n">{i+1}</span><b>{esc(f["title"])}</b>{esc(ev)}</div>' if f else ""
        phones += f'<div data-reveal style="--i:{i}"><div class="phone">{f"<img src=\"{u}\" alt=\"\">" if u else ""}{pin}</div></div>'
    S.append(slide(f'''<div class="eyebrow"><i></i>Die Website heute · Handy</div><h2>Bildschirm 1, 2 und 3 auf einem Handy <em>— und was uns dort auffällt</em></h2>
<div class="phones" style="margin-top:26px">{phones}</div>'''))
    # 5 scorecard
    rows = "".join(f'<div class="srow" data-reveal style="--i:{i}"><span class="a">{esc(s["area"])}</span><span class="bar2"><i style="--w:{int(s["score"])*10}%"></i></span><span class="n">{int(s["score"])}</span><span class="why">{esc(s["why"])}</span></div>' for i, s in enumerate(L["scorecard"][:6]))
    lh = L.get("lighthouse") or {}
    lhb = ""
    if lh:
        lhb = f'''<div class="lh"><div><div class="v">{esc(lh.get("performance","–"))}</div><div class="l">Tempo (Lighthouse, Handy)</div></div><div><div class="v">{esc(lh.get("seo","–"))}</div><div class="l">SEO-Basis</div></div><div><div class="v">{esc(lh.get("accessibility","–"))}</div><div class="l">Barrierefreiheit</div></div><div><div class="v">{esc(lh.get("lcp","–"))}</div><div class="l">bis der größte Inhalt sichtbar ist (Google-Grenze: 2,5 s)</div></div></div><p class="cap">{esc(lh.get("source",""))}</p>'''
    S.append(slide(f'''<div class="eyebrow"><i></i>Bewertung</div><h2>Sechs Bereiche, <em>0 bis 10</em></h2>
<div class="cols w" style="margin-top:28px"><div class="score">{rows}</div><div>{lhb}<p class="small">Bewertet am {date}. Jede Zeile lässt sich in einer Minute am eigenen Handy nachprüfen.</p></div></div>'''))
    # 6-7 findings detail (2 per slide)
    for k in range(0, min(len(F), 6), 2):
        pair = F[k:k+2]; items = ""
        for i, f in enumerate(pair):
            u = sh(f.get("shot", ""))
            items += f'''<div class="finding" data-reveal style="--i:{i}"><div class="t"><span class="id">{esc(f["id"])}</span><h3>{esc(f["title"])}</h3><span class="sev {esc(f.get("severity",""))}">{esc(f.get("severity",""))}</span></div>
<dl><dt>Beleg</dt><dd>{esc(f["evidence"])}</dd><dt>Folge</dt><dd>{esc(f["consequence"])}</dd><dt>Was wir tun</dt><dd class="fix">{esc(f["fix"])}</dd></dl></div>'''
        u = sh(pair[0].get("shot", ""))
        S.append(slide(f'''<div class="eyebrow"><i></i>Befund {k+1}{"–"+str(k+len(pair)) if len(pair)>1 else ""} von {min(len(F),6)}</div><h2>{esc(pair[0]["title"])}{(" <em>und</em> " + esc(pair[1]["title"])) if len(pair)>1 else ""}</h2>
<div class="cols w" style="margin-top:24px"><div>{items}</div><figure><div class="shot" style="max-height:600px;overflow:hidden">{f'<img src="{u}" alt="">' if u else ''}</div><figcaption class="cap">{esc(pair[0].get("shot","")).replace("shots/","")} · {date}</figcaption></figure></div>'''))
    # 8 market
    M = L["market"]
    mf = "".join(f'<li data-reveal style="--i:{i}"><span class="n">{i+1:02d}</span><span>{esc(x["claim"])}<span class="src">{esc(x["source"])}</span></span><span></span></li>' for i, x in enumerate(M["facts"][:5]))
    terms = "".join(f"<span>{esc(t)}</span>" for t in M.get("search_terms", [])[:8])
    S.append(slide(f'''<div class="eyebrow"><i></i>Markt und Nische</div><h2>Wie Kund:innen heute {esc(L["category_label"])}en in Wien finden</h2>
<div class="cols" style="margin-top:28px"><div><p class="sub" style="margin-top:0">{esc(M["summary"])}</p><h3 style="margin-top:22px">Was gesucht wird</h3><div class="terms">{terms}</div><p class="sub" style="font-size:15px">{esc(M.get("how_clients_find_them",""))}</p></div>
<ul class="list">{mf}</ul></div>'''))
    # 9 competitors
    comps = ""
    for i, c in enumerate(L["competitors"][:3]):
        u = sh(c.get("shot", ""))
        comps += f'''<div class="comp" data-reveal style="--i:{i}"><div class="shot">{f'<img src="{u}" alt="">' if u else ''}</div><h3>{esc(c["name"])}</h3><div class="d">{esc(c.get("district",""))} · {esc(re.sub(r"^https?://(www\\.)?","",c.get("website","")).rstrip("/"))}</div><p>{esc(c["what_their_site_does"])}</p></div>'''
    S.append(slide(f'''<div class="eyebrow"><i></i>Wettbewerb</div><h2>Was die Websites in Ihrer Nähe <em>heute können</em></h2>
<div class="comps" style="margin-top:28px">{comps}</div><p class="small">Beschrieben wird nur, was die jeweilige Website tut, {date}. Keine Bewertung der Kanzleien oder Betriebe.</p>'''))
    # 10 prognosis
    P = L["prognosis"]
    ass = "".join(f"<li>· {esc(a)}</li>" for a in P.get("assumptions", [])[:4])
    S.append(slide(f'''<div class="eyebrow"><i></i>Prognose · {esc(P.get("horizon","12 Monate"))}</div><h2>Zwei Wege, <em>ein Jahr</em></h2>
<div class="prog" style="margin-top:32px"><div data-reveal style="--i:0"><h3>Wenn nichts passiert</h3>{esc(P["if_nothing_changes"])}</div><div class="b" data-reveal style="--i:1"><h3>Wenn wir es umsetzen</h3>{esc(P["if_fixed"])}</div></div>
<ul class="assump">{ass}<li>· Einschätzung aus den gezeigten Fakten, keine Garantie. Mit ° markierte Angaben sind nicht bestätigt.</li></ul>'''))
    # 11 quick wins
    qw = "".join(f'<li data-reveal style="--i:{i}"><span class="n">{i+1:02d}</span><span>{esc(q["what"])}<span class="why">{esc(q.get("why",""))}</span></span><span class="e">{esc(q.get("effort",""))}</span></li>' for i, q in enumerate(L["quick_wins"][:5]))
    S.append(slide(f'''<div class="eyebrow"><i></i>Sofort machbar</div><h2>Was in einer Woche geht, <em>ohne alles neu zu bauen</em></h2><ul class="list" style="margin-top:22px">{qw}</ul><p class="small">Aufwand: S = Stunden, M = Tage. Diese Punkte sind in jedem Paket enthalten.</p>'''))
    # 12 offer
    O = L["offer"]; oname, ocont, oprice, odur = offer_block(O["lead"])
    second = f'<div class="second" data-reveal style="--i:1"><b>Zweiter Schritt: {esc(O.get("second",""))}</b>{esc(O.get("second_why",""))}</div>' if O.get("second") else ""
    third = f'<div class="second" data-reveal style="--i:2"><b>{esc(O["third"])}</b></div>' if O.get("third") else ""
    S.append(slide(f'''<div class="eyebrow"><i></i>Vorschlag</div><h2>Ein Paket, <em>ein Preis</em>, ein Zeitrahmen</h2>
<div class="offer" style="margin-top:28px"><div><div class="obox" data-reveal style="--i:0"><div class="n">{esc(O["lead"])} · {esc(oname)}</div><div class="p">{esc(O.get("lead_price") or oprice)}</div><div class="d">{esc(O.get("lead_duration") or odur)} · Sie besitzen am Ende Domain, Seite und alle Dateien</div><p>{esc(ocont)}</p><p><b>Warum dieses Paket:</b> {esc(O["why_this_one"])}</p></div>{second}{third}
<div class="total">Realistisch im ersten Jahr<b>{esc(O.get("realistic_total",""))}</b></div></div>
<div><h3>Bedingungen</h3><ul class="cond"><li>50 % bei Auftrag, 50 % bei Go-live. Laufende Leistungen monatlich im Voraus. Zahlungsziel 14 Tage.</li><li>Zwei Korrekturrunden je Stufe. Übergabe mit 30 Minuten Einschulung.</li><li>Nicht enthalten: Fotografie, finale Rechtstexte (Vorlagen ja), Werbebudget, Hosting/Domain (10–25 € im Monat, direkt an den Anbieter).</li><li>Der Zeitplan beginnt, sobald Inhalte und Zugänge da sind.</li><li>Derzeit ohne Umsatzsteuer (Kleinunternehmerregelung).</li></ul></div></div>'''))
    # 13 references + next step
    refs = "".join(f'<div class="ref" data-reveal style="--i:{i}"><b>{esc(r["name"])}</b>{esc(r["line"])}</div>' for i, r in enumerate(L["references"][:3]))
    book = CFG.get("booking_url", ""); book_ok = book.startswith("http")
    S.append(slide(f'''<div class="eyebrow"><i></i>Womit wir das belegen · nächster Schritt</div><h2>Zwanzig Minuten, <em>dann wissen Sie, was es bei Ihnen bedeutet</em></h2>
<div class="close" style="margin-top:28px"><div>{refs}</div>
<div><p class="sub" style="margin-top:0">Am Telefon oder bei Ihnen. Sie hören, was die Befunde konkret für {name} heißen und was der erste Schritt wäre. Ohne Verpflichtung.</p>
<div class="cta">{f'<a href="{esc(book)}">Termin wählen</a>' if book_ok else ''}<a class="sec" href="tel:{esc(CFG["phone"].replace(" ",""))}">{esc(CFG["phone"])}</a><a class="sec" href="mailto:{esc(CFG["email"])}">{esc(CFG["email"])}</a></div>
<p class="small">{esc(CFG["sender_name"])} · {esc(CFG["sender_role"])} · {esc(CFG["studio"])} · {esc(" · ".join(CFG["address_lines"]))}<br>Die Beobachtungen stammen aus einer Prüfung Ihrer öffentlichen Website am {date}, von Hand bestätigt. Wir speichern nur Firmenname, Adresse und was auf Ihrer Website steht; auf Wunsch löschen wir den Eintrag sofort.</p></div></div>'''))
    body = "\n".join(S)
    return f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{esc(L["pitch_title"])} · {esc(CFG["studio"])}</title><style>{fonts_css()}{CSS.replace("ACCENT", acc)}</style></head>
<body><div class="stage"><div class="deck" id="deck">
<div class="bar"><span><span class="acc"></span><b>{esc(CFG["sender_name"])}</b> · {esc(CFG["studio"])}</span><span>{name}</span><span class="counter">01 / {len(S):02d}</span></div>
{body}
<div class="foot">{dom} · Befund und Vorschlag · {date}</div>
<div class="nav"><button id="prev" aria-label="Zurück">←</button><button id="next" aria-label="Weiter">→</button></div>
<div class="progress" id="progress"></div></div></div><script>{JS}</script></body></html>'''

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--lead", required=True); a = ap.parse_args()
    slugs = [p.name for p in LEADS.iterdir() if p.is_dir() and (p / "lead.json").exists()] if a.lead == "all" else [a.lead]
    for s in slugs:
        folder = LEADS / s; L = json.load(open(folder / "lead.json", encoding="utf-8"))
        out = folder / "pitch.html"; out.write_text(render(L, folder), encoding="utf-8")
        print(f"{s}: pitch.html {out.stat().st_size//1024} KB")

if __name__ == "__main__":
    main()
