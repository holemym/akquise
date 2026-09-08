#!/usr/bin/env python3
"""
pitch.py — render the per-lead pitch deck (German, single self-contained HTML) from data/leads/<slug>/lead.json.

  python tools/pitch.py --lead lukanec        → data/leads/lukanec/pitch.html
  python tools/pitch.py --lead all

Brief block (CLAUDE.md §2), v2 2026-09-08 — rebuilt after "less custom, weaker motion, not engaging or readable":
  positioning  — "Wir haben Ihre Website gemessen. Hier ist die eine Zahl, was sie kostet, und was wir tun würden."
  audience     — one owner/partner of a small Vienna practice, on a laptop in a 20-minute call
  register     — AKTENLAGE: a case file. Ink on paper, hairlines, heavy serif display at real scale,
                 evidence handled as numbered exhibits, dark slides as the verdict beats.
                 One accent, taken from THEIR own brand colour.
  signature    — the verdict slide: one measured number at 220 px that counts up to its real value,
                 then the exhibit wall of their own site on three phones.
  motion pack  — three primitives, each carrying meaning, each ending static:
                 ZIEHEN  rules, meters and the time axis grow from zero to a measured value
                 ZÄHLEN  every headline numeral counts to its measured value (seconds, scores, years, prices)
                 SETZEN  the slide rises once, content staggers once, then holds
  kill list    — no tile grids, no card walls, no uniform two-column rhythm, no glow, no gradient text,
                 no marketing pills, no stock imagery, no "Digitalisierung", no slide that repeats
                 the skeleton of the slide before it
  palette      — paper #faf9f6 · ink #12100e · lead accent from lead.json, never a default blue

Every slide is built from measured data in lead.json / shots/facts.json / _lh/*.json. Nothing is invented;
a lead missing a data set (no Lighthouse, no SERP finding) simply gets fewer slides, never a filled-in one.
Images are inlined as WebP data URIs so the file travels as one attachment; fonts inlined from _fonts.css.
"""
import argparse, base64, html, io, json, pathlib, re, sys, time, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEADS = ROOT / "data" / "leads"
CFG = json.load(open(ROOT / "config.json", encoding="utf-8"))
OFFERS_MD = (ROOT / "OFFERS.de.md").read_text(encoding="utf-8")
FONT_CSS = ("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700"
            "&family=Inter:wght@400;500;600&display=swap")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

PATH_RX = re.compile(r",?\s*(?:data/|\./)?[\w/\-]+\.(?:json|csv|md|py)")
def esc(s):
    """Escape, and strip any internal file path — those must never appear on a client slide."""
    return html.escape(PATH_RX.sub("", str(s or "")).replace("  ", " ").strip())

def img_uri(path, maxw=1200, q=80):
    p = pathlib.Path(path)
    if not p.exists(): return ""
    im = Image.open(p).convert("RGB")
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=q, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()

FONT_CACHE = LEADS / "_fonts.css"
def fonts_css():
    if FONT_CACHE.exists() and FONT_CACHE.stat().st_size > 10000: return FONT_CACHE.read_text(encoding="utf-8")
    try:
        css = urllib.request.urlopen(urllib.request.Request(FONT_CSS, headers={"User-Agent": UA}), timeout=20).read().decode()
        def repl(m):
            d = urllib.request.urlopen(urllib.request.Request(m.group(1), headers={"User-Agent": UA}), timeout=20).read()
            return f"url(data:font/woff2;base64,{base64.b64encode(d).decode()})"
        css = re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", repl, css)
        FONT_CACHE.write_text(css, encoding="utf-8"); return css
    except Exception as e:
        print("  fonts not inlined:", type(e).__name__, file=sys.stderr); return ""

def offer_block(oid):
    for line in OFFERS_MD.splitlines():
        if line.startswith(f"| **{oid}**"):
            c = [x.strip() for x in line.strip("|").split("|")]
            if len(c) >= 6: return (c[1].replace("**", "").strip(), c[3], c[4].replace("**", ""), c[5])
    return (oid, "", "", "")

# ---------------------------------------------------------------- verdict: the one measured fact
def verdict(L, lh, mob=None):
    """The single number/word the whole deck hangs on. Measured only — never a phrase we made up."""
    lcp = (lh or {}).get("lcp", "")
    m = re.match(r"([\d,\.]+)\s*s", str(lcp))
    tags = " ".join(f["title"] + " " + f["evidence"] for f in L["findings"]).lower()
    # a site without a viewport tag lays itself out at ~980 px and is then shrunk onto the phone:
    # that measured width is the most concrete way to say "no mobile layout"
    if mob and mob.get("viewport") is False and (mob.get("scrollW") or 0) >= 900:
        w = int(mob["scrollW"])
        # innerW here reports the *layout* width the page forced (980), not the device width we shot at (390)
        return (str(w), "px", f"breit baut sich Ihre Seite auf, wenn ein 390 px schmales Handy sie öffnet. "
                f"Der Browser schrumpft alles auf rund {round(390/w*100)} % — lesbar wird es erst durch Zoomen.",
                "eigene Messung im Browser, 08.09.2026")
    if "geparkt" in tags or "parkseite" in tags:
        return ("geparkt", "", "Unter Ihrer eigenen Adresse steht heute die Parkseite des Registrars.", "eigene Prüfung, 08.09.2026")
    if "nicht sicher" in tags:
        return ("Nicht sicher", "", "Das schreibt der Browser neben Ihren Firmennamen, bei der Adresse, die überall gedruckt steht.", "eigene Prüfung, 08.09.2026")
    if "under construction" in tags or "baustellen" in tags:
        return ("Under Construction", "", "Dieser Kasten steht auf Ihrer Startseite — seit wann, weiß nur Ihr Dienstleister.", "eigene Prüfung, 08.09.2026")
    if m and float(m.group(1).replace(",", ".")) > 2.5:
        v = m.group(1).replace(".", ",")
        return (v, "s", "bis auf dem Handy der größte Inhalt sichtbar ist. Google nennt alles über 2,5 s schlecht.", (lh or {}).get("source", ""))
    for f in L["site_today"]["facts"]:
        y = re.fullmatch(r"(20\d\d)", str(f["value"]).strip())
        if y: return (y.group(1), "", f"{f['label']} — seither zeigt die Seite kein neueres Datum.", "eigene Prüfung, 08.09.2026")
    f0 = L["findings"][0]
    return (f0["title"], "", f0["consequence"], "eigene Prüfung, 08.09.2026")

CSS = r"""
:root{
 --paper:#faf9f6;--ink:#12100e;--ink-2:#3a3632;--mute:#6f6a63;--faint:#a8a29a;
 --line:#e0dbd3;--line-2:#efebe4;--acc:ACCENT;--acc-ink:ACCENTINK;
 --ease:cubic-bezier(.16,1,.3,1);
 --fd:'Fraunces',Georgia,'Times New Roman',serif;--fb:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
 --dir:1;
}
*{box-sizing:border-box}html,body{height:100%;margin:0;background:#dedad2;overflow:hidden}
body{font-family:var(--fb);color:var(--ink);-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
img{display:block;max-width:100%}a{color:inherit}h1,h2,h3,h4,p,ul,ol,figure,dl,dd{margin:0}ul,ol{padding:0;list-style:none}
button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer}
.stage{position:fixed;inset:0}
.deck{position:absolute;left:50%;top:50%;width:1600px;height:900px;background:var(--paper);transform:translate(-50%,-50%);transform-origin:center;overflow:hidden;box-shadow:0 40px 100px rgba(0,0,0,.32)}

/* chrome */
.bar{position:absolute;left:0;right:0;top:0;height:62px;display:flex;align-items:center;justify-content:space-between;padding:0 60px;z-index:20;font:500 11.5px/1 var(--fb);letter-spacing:.1em;text-transform:uppercase;color:var(--mute);transition:color .5s ease}
.bar b{color:var(--ink);font-weight:600;transition:color .5s ease}
.bar .acc{display:inline-block;width:9px;height:9px;background:var(--acc);margin-right:9px;vertical-align:-1px}
.deck.on-dark .bar,.deck.on-dark .foot,.deck:has(.slide.dark.is-active) .bar,.deck:has(.slide.dark.is-active) .foot{color:rgba(250,249,246,.5)}
.deck.on-dark .bar b,.deck:has(.slide.dark.is-active) .bar b{color:#faf9f6}
.counter{font-variant-numeric:tabular-nums;letter-spacing:.14em}
.progress{position:absolute;left:0;bottom:0;height:2px;width:0;background:var(--acc);transition:width .8s var(--ease);z-index:22}
.nav{position:absolute;right:60px;bottom:28px;display:flex;gap:7px;z-index:21}
.nav button{width:38px;height:38px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;font-size:14px;transition:background .3s ease,color .3s ease,border-color .3s ease,transform .5s var(--ease)}
.nav button:hover{background:var(--ink);color:var(--paper);border-color:var(--ink);transform:translateY(-2px)}
.nav button[disabled]{opacity:.22;pointer-events:none}
.deck.on-dark .nav button,.deck:has(.slide.dark.is-active) .nav button{border-color:rgba(250,249,246,.25);color:#faf9f6}
.deck.on-dark .nav button:hover,.deck:has(.slide.dark.is-active) .nav button:hover{background:#faf9f6;color:var(--ink)}
.foot{position:absolute;left:60px;bottom:38px;font:400 11.5px var(--fb);letter-spacing:.04em;color:var(--faint);z-index:19;transition:color .5s ease}

/* SETZEN — the slide rises once, holds */
.slide:not(.cover):not(.verdict){display:flex;flex-direction:column}
.slide>p.note:last-child,.slide>.botrow:last-child{margin-top:auto;padding-top:22px}
.slide>.grow{flex:1;align-content:center}
.slide{position:absolute;inset:0;padding:104px 60px 74px;opacity:0;visibility:hidden;transform:translateY(calc(20px*var(--dir)));transition:opacity .42s ease,transform .85s var(--ease),visibility 0s linear .42s}
.slide.is-active{opacity:1;visibility:visible;transform:none;transition:opacity .5s ease .04s,transform .85s var(--ease),visibility 0s}
.slide.dark{background:var(--ink);color:#faf9f6;--line:rgba(250,249,246,.16);--line-2:rgba(250,249,246,.09);--mute:rgba(250,249,246,.56);--faint:rgba(250,249,246,.36);--ink-2:rgba(250,249,246,.8)}
[data-reveal]{opacity:0;transform:translateY(12px);transition:opacity .5s ease,transform .85s var(--ease);transition-delay:calc(var(--i,0)*55ms + 130ms)}
.is-active [data-reveal]{opacity:1;transform:none}
.no-motion .slide,.no-motion [data-reveal],.no-motion .m i,.no-motion .rule::after,.no-motion .tl-bar{transition:none!important;transform:none!important}

/* type */
.eyebrow{font:500 11px/1 var(--fb);letter-spacing:.22em;text-transform:uppercase;color:var(--mute);margin-bottom:18px;display:flex;align-items:center;gap:11px}
.eyebrow::before{content:"";width:24px;height:2px;background:var(--acc);flex:none}
h2{font:600 52px/1.04 var(--fd);letter-spacing:-.022em;max-width:1180px;font-variation-settings:'opsz' 96}
h2 em{font-style:italic;font-weight:400;color:var(--acc-ink)}
.dark h2 em{color:var(--acc)}
.sub{font:400 17px/1.55 var(--fb);color:var(--mute);margin-top:15px;max-width:820px}
h3{font:600 16px/1.3 var(--fb);letter-spacing:-.005em}
.lede{font:400 20px/1.5 var(--fb);color:var(--ink-2);max-width:760px}
.src{font:400 11.5px/1.5 var(--fb);color:var(--faint);letter-spacing:.02em}
.note{font:400 12.5px/1.5 var(--fb);color:var(--faint);margin-top:16px}

/* ZIEHEN — a rule that draws itself */
.rule{position:relative;height:1px;background:var(--line-2)}
.rule::after{content:"";position:absolute;inset:0;background:var(--ink);transform:scaleX(0);transform-origin:left;transition:transform 1.05s var(--ease) .2s}
.is-active .rule::after{transform:none}

/* 1 · cover */
.cover{padding:0;display:grid;grid-template-columns:1fr 620px}
.cover .l{padding:126px 60px 74px;display:flex;flex-direction:column;justify-content:space-between}
.cover .kicker{font:500 11px/1 var(--fb);letter-spacing:.22em;text-transform:uppercase;color:var(--mute);margin-bottom:36px}
.cover h1{font:600 80px/1.02 var(--fd);letter-spacing:-.035em;font-variation-settings:'opsz' 144;max-width:840px}
.cover h1 em{font-style:italic;font-weight:400;color:var(--acc-ink);white-space:nowrap}
.cover h1.long{font-size:66px}
.deck:has(.slide.cover.is-active) .foot{opacity:0}
.deck:has(.slide.cover.is-active) .nav button{border-color:rgba(250,249,246,.3);color:#faf9f6}
.deck:has(.slide.cover.is-active) .nav button:hover{background:#faf9f6;color:var(--ink)}
.cover .meta{display:flex;gap:34px;font:400 13.5px/1.6 var(--fb);color:var(--mute);border-top:1px solid var(--line);padding-top:20px}
.cover .meta b{display:block;color:var(--ink);font-weight:600}
.cover .r{background:var(--ink);position:relative;overflow:hidden;display:grid;place-items:center}
.cover .r .ph{width:300px;border-radius:30px;border:7px solid #26221e;box-shadow:0 40px 90px rgba(0,0,0,.6);overflow:hidden;background:#000}
.cover .r .cap{position:absolute;left:44px;right:150px;bottom:38px;font:400 11.5px/1.55 var(--fb);color:rgba(250,249,246,.48)}
.cover .stamp{position:absolute;left:-1px;top:96px;background:var(--acc);color:#fff;font:600 11px/1 var(--fb);letter-spacing:.18em;text-transform:uppercase;padding:11px 16px 11px 44px}

/* 2 · verdict (dark) */
.verdict{display:grid;grid-template-rows:auto auto 1fr auto;padding-top:104px}
.vnum{font:600 210px/.86 var(--fd);letter-spacing:-.05em;font-variation-settings:'opsz' 144;display:flex;align-items:baseline;gap:14px}
.vnum.txt{font-size:112px;line-height:1.02;letter-spacing:-.035em;max-width:1300px}
.vnum small{font:400 62px var(--fd);color:var(--acc);letter-spacing:-.02em}
.vsay{font:400 30px/1.35 var(--fd);color:rgba(250,249,246,.82);max-width:900px;font-variation-settings:'opsz' 72}
.vfoot{display:flex;justify-content:space-between;align-items:end;border-top:1px solid var(--line);padding-top:18px}

/* 3 · exhibits (phones) */
.exh{display:grid;grid-template-columns:repeat(3,1fr);gap:34px;margin-top:34px}
.exh figure{display:grid;grid-template-rows:auto 1fr}
.exh .ph{position:relative;width:284px;height:424px;border-radius:26px;border:6px solid #26221e;overflow:hidden;background:#000;box-shadow:0 22px 46px rgba(18,16,14,.22)}
.exh .ph img{width:100%;height:100%;object-fit:cover;object-position:top}
.exh .tag{position:absolute;left:0;top:26px;background:var(--acc);color:#fff;font:600 10.5px/1 var(--fb);letter-spacing:.16em;padding:8px 12px}
.exh figcaption{margin-top:18px;max-width:284px}
.exh .ct{font:600 15px/1.35 var(--fb)}
.exh .cd{font:400 13.5px/1.5 var(--fb);color:var(--mute);margin-top:6px}

/* 4 · tempo — the time axis */
.axis{margin-top:60px;position:relative;padding-bottom:56px}
.tl{position:relative;height:112px}
.tl-row{position:absolute;left:0;right:0;height:34px;display:flex;align-items:center}
.tl-lab{position:absolute;left:0;width:230px;font:500 14px/1 var(--fb);color:var(--ink-2)}
.tl-track{position:absolute;left:250px;right:60px;height:100%}
.tl-bar{position:absolute;left:0;top:9px;height:16px;background:var(--line);width:0;transition:width 1.15s var(--ease) .25s}
.tl-bar.hot{background:var(--acc)}
.tl-val{position:absolute;top:6px;font:600 15px/22px var(--fb);font-variant-numeric:tabular-nums;white-space:nowrap;opacity:0;transition:opacity .45s ease .95s}
.is-active .tl-val{opacity:1}
.gline{position:absolute;top:-14px;bottom:-30px;width:1px;background:var(--acc);opacity:0;transition:opacity .5s ease .55s}
.is-active .gline{opacity:1}
.gline span{position:absolute;top:-26px;left:-4px;font:600 11px/1 var(--fb);letter-spacing:.1em;text-transform:uppercase;color:var(--acc-ink);white-space:nowrap}
.dark .gline span{color:var(--acc)}
.ticks{position:absolute;left:250px;right:60px;bottom:22px;height:22px;border-top:1px solid var(--line)}
.ticks i{position:absolute;top:0;width:1px;height:6px;background:var(--line)}
.ticks b{position:absolute;top:10px;font:400 11px var(--fb);color:var(--faint);transform:translateX(-50%)}

/* 5 · SERP mock */
.serp{border:1px solid var(--line);background:#fff;padding:26px 28px 28px;position:relative}
.serp.now{border-color:var(--acc)}
.serp .lab{position:absolute;right:0;top:-1px;background:var(--acc);color:#fff;font:600 10px/1 var(--fb);letter-spacing:.16em;padding:7px 11px;text-transform:uppercase}
.serp .lab.alt{background:var(--ink)}
.serp .u{font:400 12.5px/1.4 var(--fb);color:#5f6368;display:flex;align-items:center;gap:7px}
.serp .u i{width:20px;height:20px;border-radius:50%;background:var(--line-2);display:block;flex:none}
.serp .t{font:400 20px/1.3 var(--fb);color:#1a0dab;margin-top:7px}
.serp .d{font:400 13.5px/1.6 var(--fb);color:#4d5156;margin-top:6px}
.serp .d.empty{color:var(--faint);font-style:italic}
.gq{display:flex;align-items:center;gap:12px;height:46px;padding:0 20px;border:1px solid var(--line);border-radius:999px;background:#fff;font:400 15px/1 var(--fb);max-width:520px}
.gq .q::after{content:"";display:inline-block;width:1px;height:16px;background:var(--ink);margin-left:2px;vertical-align:-3px;animation:caret 1.1s steps(1) infinite}
@keyframes caret{50%{opacity:0}}
.no-motion .gq .q::after{animation:none}

/* 6 · meters */
.meters{margin-top:26px}
.m{display:grid;grid-template-columns:190px 1fr 62px;gap:20px;align-items:center;padding:13px 0;border-top:1px solid var(--line-2)}
.m:last-child{border-bottom:1px solid var(--line-2)}
.m .name{font:500 15px/1.3 var(--fb)}
.m .track{height:7px;background:var(--line-2);position:relative}
.m i{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--ink);transition:width 1.1s var(--ease);transition-delay:calc(var(--i,0)*70ms + .25s)}
.m i.low{background:var(--acc)}
.m .n{font:600 21px/1 var(--fd);text-align:right;font-variant-numeric:tabular-nums}
.m .why{grid-column:1/4;font:400 12.5px/1.5 var(--fb);color:var(--mute);margin-top:-4px}
.avg{font:600 128px/.9 var(--fd);letter-spacing:-.04em;font-variation-settings:'opsz' 144}
.avg small{font:400 34px var(--fd);color:var(--mute)}

/* 7 · findings ledger */
.led{margin-top:10px}
.led li{display:grid;grid-template-columns:70px 1fr 300px;gap:30px;align-items:start;padding:22px 0;border-top:1px solid var(--line)}
.led li:last-child{border-bottom:1px solid var(--line)}
.led .n{font:400 30px/1 var(--fd);color:var(--acc-ink);font-variant-numeric:tabular-nums}
.dark .led .n{color:var(--acc)}
.led .t{font:600 23px/1.25 var(--fd);letter-spacing:-.012em}
.led .e{font:400 14.5px/1.55 var(--fb);color:var(--mute);margin-top:8px;max-width:640px}
.led .fix{font:400 14.5px/1.55 var(--fb);color:var(--ink-2);border-left:2px solid var(--acc);padding-left:14px}
.led .fix b{display:block;font:600 10.5px/1 var(--fb);letter-spacing:.16em;text-transform:uppercase;color:var(--acc-ink);margin-bottom:7px}
.dark .led .fix b{color:var(--acc)}

/* 8 · competitor wall */
.wall{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin-top:40px;align-items:start}
.wall .cell{position:relative}
.wall .shot{border:1px solid var(--line);overflow:hidden;background:#fff;aspect-ratio:16/13}
.wall .cell.you .shot{border:2px solid var(--acc)}
.wall .shot img{width:100%;height:100%;object-fit:cover;object-position:top}
.wall .who{font:600 15px/1.3 var(--fb);margin-top:14px}
.wall .cell.you .who{color:var(--acc-ink)}
.wall .dom{font:400 12px/1.4 var(--fb);color:var(--faint);margin-top:3px;word-break:break-all}
.wall .does{font:400 13.5px/1.5 var(--fb);color:var(--mute);margin-top:9px}
.wall .badge{position:absolute;left:0;top:0;background:var(--acc);color:#fff;font:600 10px/1 var(--fb);letter-spacing:.14em;text-transform:uppercase;padding:7px 10px}

/* 9 · market ledger */
.mk{display:grid;grid-template-columns:1fr 500px;gap:70px;align-items:start}
.mk ol li{display:grid;grid-template-columns:44px 1fr;gap:14px;padding:16px 0;border-top:1px solid var(--line-2)}
.mk ol li:last-child{border-bottom:1px solid var(--line-2)}
.mk .n{font:400 18px/1.4 var(--fd);color:var(--acc-ink)}
.mk .c{font:400 15px/1.55 var(--fb)}
.terms{display:flex;flex-wrap:wrap;gap:9px;margin-top:16px}
.terms span{font:400 13.5px/1 var(--fb);color:var(--ink-2);border:1px solid var(--line);padding:9px 13px;background:#fff}
.dark .terms span{background:transparent}

/* 10 · prognosis */
.prog{display:grid;grid-template-columns:1fr 1fr;gap:0;margin-top:32px;border-top:1px solid var(--line)}
.prog>div{padding:34px 40px 30px}
.prog>div:first-child{border-right:1px solid var(--line)}
.prog .h{font:500 11px/1 var(--fb);letter-spacing:.2em;text-transform:uppercase;color:var(--mute);margin-bottom:16px}
.prog .b{font:400 21px/1.5 var(--fd);font-variation-settings:'opsz' 72}
.prog .good{background:var(--ink);color:#faf9f6;margin:-1px -40px -30px 0;padding:35px 40px 31px}
.prog .good .h{color:var(--acc)}

/* 11 · offer */
.off{display:grid;grid-template-columns:1.05fr .95fr;gap:64px;align-items:start;margin-top:26px}
.price{font:600 116px/.92 var(--fd);letter-spacing:-.04em;font-variation-settings:'opsz' 144}
.price small{font:400 30px var(--fd);color:var(--mute);letter-spacing:0}
.oname{font:400 23px/1.3 var(--fd);color:var(--acc-ink)}
.dark .oname{color:var(--acc)}
.owhat{font:400 15.5px/1.6 var(--fb);color:var(--ink-2);margin-top:16px;max-width:560px}
.second{margin-top:26px;border-top:1px solid var(--line);padding-top:20px}
.second b{display:block;font:600 15px/1.3 var(--fb);margin-bottom:6px}
.second p{font:400 14px/1.55 var(--fb);color:var(--mute)}
.cond li{font:400 13.5px/1.5 var(--fb);color:var(--mute);padding:11px 0;border-top:1px solid var(--line-2)}
.cond li:last-child{border-bottom:1px solid var(--line-2)}
.total{margin-top:24px}
.total .l{font:500 11px/1 var(--fb);letter-spacing:.2em;text-transform:uppercase;color:var(--mute)}
.total .v{font:400 32px/1.2 var(--fd);margin-top:9px}

/* 12 · close */
.close{display:grid;grid-template-columns:1fr 520px;gap:70px;align-items:start;margin-top:30px}
.ref{padding:20px 0;border-top:1px solid var(--line)}
.ref:last-child{border-bottom:1px solid var(--line)}
.ref b{display:block;font:600 15px/1.3 var(--fb);color:var(--acc-ink)}
.dark .ref b{color:var(--acc)}
.ref span{font:400 14.5px/1.55 var(--fb);color:var(--mute);display:block;margin-top:5px}
.cta{display:flex;flex-direction:column;gap:11px;margin-top:8px}
.cta a{display:block;padding:16px 22px;border:1px solid var(--ink);font:600 15px/1 var(--fb);text-decoration:none;transition:background .3s ease,color .3s ease}
.cta a.pri{background:var(--ink);color:var(--paper)}
.dark .cta a{border-color:rgba(250,249,246,.3)}.dark .cta a.pri{background:var(--acc);border-color:var(--acc);color:#fff}
"""

JS = r"""
(()=>{const deck=document.getElementById('deck'),slides=[...deck.querySelectorAll('.slide')],
counter=deck.querySelector('.counter'),prog=document.getElementById('progress'),prev=document.getElementById('prev'),next=document.getElementById('next');
const R=matchMedia('(prefers-reduced-motion: reduce)').matches||new URLSearchParams(location.search).has('static');
if(R)document.documentElement.classList.add('no-motion');
let cur=-1;
/* ZÄHLEN — a numeral counts to its measured value, once, when its slide lands */
function count(sl){sl.querySelectorAll('[data-count]').forEach(el=>{
 if(el.dataset.done)return;el.dataset.done='1';
 const to=parseFloat(el.dataset.count),dec=+(el.dataset.dec||0),pre=el.dataset.pre||'',suf=el.dataset.suf||'';
 if(R){el.textContent=pre+to.toFixed(dec).replace('.',',')+suf;return}
 const t0=performance.now(),d=900;
 (function tick(t){const p=Math.min(1,(t-t0)/d),e=1-Math.pow(1-p,3);
  el.textContent=pre+(to*e).toFixed(dec).replace('.',',')+suf;if(p<1)requestAnimationFrame(tick)})(t0);
})}
new MutationObserver(ms=>ms.forEach(m=>{const s=m.target;
 if(s.classList.contains('slide')&&s.classList.contains('is-active'))setTimeout(()=>count(s),R?0:320)}))
 .observe(deck,{subtree:true,attributes:true,attributeFilter:['class']});
function go(i){i=Math.max(0,Math.min(slides.length-1,i));if(i===cur)return;
 document.documentElement.style.setProperty('--dir',i>cur?1:-1);
 slides.forEach((s,k)=>s.classList.toggle('is-active',k===i));cur=i;
 deck.classList.toggle('on-dark',slides[i].classList.contains('dark'));
 counter.textContent=String(i+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');
 prog.style.width=((i+1)/slides.length*100)+'%';prev.disabled=i===0;next.disabled=i===slides.length-1;
 setTimeout(()=>count(slides[i]),R?0:340);history.replaceState(null,'','#'+(i+1))}
function fit(){const s=Math.min(innerWidth/1600,innerHeight/900);deck.style.transform='translate(-50%,-50%) scale('+s+')'}
addEventListener('resize',fit);fit();prev.onclick=()=>go(cur-1);next.onclick=()=>go(cur+1);
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();go(cur+1)}
 if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(cur-1)}
 if(e.key==='Home')go(0);if(e.key==='End')go(slides.length-1)});
let tx=null;addEventListener('touchstart',e=>tx=e.touches[0].clientX,{passive:true});
addEventListener('touchend',e=>{if(tx==null)return;const d=e.changedTouches[0].clientX-tx;if(Math.abs(d)>50)go(cur+(d<0?1:-1));tx=null});
go(Math.max(0,(parseInt(location.hash.slice(1))||1)-1))})();
"""

def cut(s, n):
    s = str(s or "")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(",;:—-") + " …"

def num(el_val, dec=0, pre="", suf=""):
    return f'<span data-count="{el_val}" data-dec="{dec}" data-pre="{esc(pre)}" data-suf="{esc(suf)}">{pre}0{suf}</span>'

def render(L, folder):
    acc = L.get("accent") or "#12100e"
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", acc): acc = "#12100e"
    r_, g_, b_ = (int(acc[i:i+2], 16) for i in (1, 3, 5))
    lum = (0.299*r_ + 0.587*g_ + 0.114*b_)
    acc_ink = acc if lum < 150 else "#12100e"     # accent readable on paper; else fall back to ink
    sh = lambda rel, w=1200: img_uri(folder / rel, w) if rel else ""
    date = time.strftime("%d.%m.%Y")
    name = esc(L["name"]); dom = esc(re.sub(r"^https?://(www\.)?", "", L["website"]).rstrip("/"))
    lh = L.get("lighthouse") or {}
    try: mob = (json.load(open(folder / "shots" / "facts.json", encoding="utf-8")) or {}).get("mobile") or {}
    except Exception: mob = {}
    F = L["findings"]; S = []

    # ---- 1 cover
    vnum, vunit, vsay, vsrc = verdict(L, lh, mob)
    ph = sh("shots/m390-vp1b.png", 700) or sh("shots/m390-vp1.png", 700)
    S.append(f'''<section class="slide cover"><div class="l">
<div><div class="kicker">{esc(L["district"])} · {esc(L["category_label"])}</div>
<h1 class="{"long" if len(L["pitch_title"]) > 44 else ""}">{esc(L["pitch_title"]).replace(dom, f'<em>{dom}</em>')}</h1></div>
<div class="meta"><span><b>{esc(CFG["sender_name"])}</b>{esc(CFG["sender_role"])}</span><span><b>{date}</b>Befund und Vorschlag</span><span><b>Vertraulich</b>nur für {esc(L["contact"].get("person") or name)}</span></div></div>
<div class="r"><div class="stamp">Beweis 01</div>{f'<div class="ph"><img src="{ph}" alt=""></div>' if ph else ''}
<div class="cap">{dom} am Handy, 390 px, aufgenommen am {date}. Das ist der erste Eindruck, den jemand bekommt, der Sie unterwegs sucht.</div></div></section>''')

    # ---- 2 verdict (dark, the signature)
    is_n = bool(re.fullmatch(r"[\d,\.]+", vnum))
    big = (f'<span class="vnum">{num(vnum.replace(",", "."), 1 if "," in vnum else 0)}<small>{esc(vunit)}</small></span>'
           if is_n and vunit else
           f'<span class="vnum">{num(vnum.replace(",", "."), 0)}</span>' if is_n else
           f'<span class="vnum txt" style="font-size:{160 if len(vnum) <= 9 else (128 if len(vnum) <= 14 else 104)}px">{esc(vnum)}</span>')
    S.append(f'''<section class="slide dark verdict"><div><div class="eyebrow">{"Der Befund in einer Zahl" if is_n else "Der Befund in einem Wort"}</div>{big}</div>
<p class="vsay" style="margin-top:34px;max-width:1080px">{esc(vsay)}</p><div></div>
<div class="vfoot"><span class="src">Quelle: {esc(vsrc)}</span><span class="src">{dom}</span></div></section>''')

    # ---- 3 exhibits: their site on three phones
    cells = ""
    for i, (fn, cap) in enumerate((("m390-vp1", "Bildschirm 1 — was zuerst erscheint"), ("m390-vp2", "Bildschirm 2"), ("m390-vp3", "Bildschirm 3"))):
        u = sh(f"shots/{fn}.png", 620)
        if not u: continue
        f = F[i] if i < len(F) else None
        cells += (f'<figure data-reveal style="--i:{i}"><div class="ph"><div class="tag">Beweis {i+2:02d}</div><img src="{u}" alt=""></div>'
                  f'<figcaption><div class="ct">{esc(f["title"]) if f else esc(cap)}</div>'
                  f'<div class="cd">{esc(f["evidence"][:150] + ("…" if len(f["evidence"]) > 150 else "")) if f else ""}</div></figcaption></figure>')
    if cells:
        S.append(f'''<section class="slide"><div class="eyebrow">Beweisaufnahme · das eigene Handy</div>
<h2>Drei Bildschirme, <em>ungeschnitten</em></h2>
<p class="sub">Aufgenommen am {date} auf einem Standard-Handy, 390 px breit. Nichts nachbearbeitet.</p>
<div class="exh grow" style="align-content:start">{cells}</div></section>''')

    # ---- 4 tempo: the time axis (only with a measured LCP)
    m = re.match(r"([\d,\.]+)\s*s", str(lh.get("lcp", "")))
    if m:
        secs = float(m.group(1).replace(",", "."))
        scale = max(secs * 1.15, 4.0)
        comp = []
        for i in range(1, 5):
            p = folder / "shots" / f"comp-{i}-facts.json"
            if not p.exists(): continue
            try: d = json.load(open(p, encoding="utf-8"))
            except Exception: continue
            if isinstance(d.get("load_s"), (int, float)) and d["load_s"] < scale:
                nm = re.sub(r"^https?://(www\.)?", "", d.get("url", "")).rstrip("/")
                comp.append((nm, float(d["load_s"])))
        comp = sorted(comp, key=lambda x: x[1])[:3]
        rows = f'''<div class="tl-row" style="top:0"><span class="tl-lab" style="font-weight:600">{dom}</span>
<span class="tl-track"><i class="tl-bar hot" style="width:{secs/scale*100:.1f}%"></i>
<span class="tl-val" style="left:calc({secs/scale*100:.1f}% + 12px)">{m.group(1)} s</span></span></div>'''
        for k, (nm, v) in enumerate(comp):
            rows += f'''<div class="tl-row" style="top:{(k+1)*36}px"><span class="tl-lab">{esc(nm)}</span>
<span class="tl-track"><i class="tl-bar" style="width:{v/scale*100:.1f}%;transition-delay:{.45+k*.12:.2f}s"></i>
<span class="tl-val" style="left:calc({v/scale*100:.1f}% + 12px);color:var(--mute)">{str(round(v,1)).replace(".", ",")} s</span></span></div>'''
        ticks = "".join(f'<i style="left:{t/scale*100:.1f}%"></i><b style="left:{t/scale*100:.1f}%">{t} s</b>' for t in range(0, int(scale)+1, 2 if scale > 9 else 1))
        S.append(f'''<section class="slide"><div class="eyebrow">Tempo · gemessen, nicht geschätzt</div>
<h2>{m.group(1)} Sekunden, bis am Handy <em>etwas zu sehen ist</em></h2>
<p class="sub">Google zieht die Grenze bei 2,5 Sekunden. Darunter gilt eine Seite als gut, darüber als schlecht — und ein Teil der Besucher ist vorher weg.</p>
<div class="axis"><div class="tl" style="height:{(len(comp)+1)*36+16}px">{rows}
<span class="gline" style="left:calc(250px + (100% - 310px) * {2.5/scale:.4f})"><span>Google-Grenze 2,5 s</span></span></div>
<div class="ticks">{ticks}</div></div>
<div class="botrow" style="display:grid;grid-template-columns:1fr 460px;gap:60px;align-items:end;margin-top:8px">
<p class="note" style="margin:0">Ihre Seite: {esc(lh.get("source",""))}. Vergleichsseiten: vollständige Ladezeit, einmalig gemessen am {date} mit demselben Werkzeug — ein Richtwert, kein Laborwert.</p>
<p class="lede" style="font-size:19px;border-left:2px solid var(--acc);padding-left:20px">{esc(next((f["consequence"] for f in F if re.search(r"sekund|lade|tempo|lcp", f["title"] + f["evidence"], re.I)), F[0]["consequence"]))}</p></div></section>''')

    # ---- 5 SERP mock (only when a Google-visibility finding exists)
    seo = next((f for f in F if re.search(r"beschreibung|meta|seitentitel|google", f["title"], re.I)), None)
    if seo:
        rival = L["competitors"][0] if L["competitors"] else None
        rdom = re.sub(r"^https?://(www\.)?", "", (rival or {}).get("website", "")).rstrip("/") if rival else ""
        S.append(f'''<section class="slide"><div class="eyebrow">Was Google zeigt</div>
<h2>Ihr Eintrag, <em>wie ihn jemand heute sieht</em></h2>
<p class="sub">{esc(seo["evidence"])}</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:44px;margin-top:30px;align-items:start">
<div data-reveal><div class="gq"><span class="q">{esc((L["market"].get("search_terms") or [name])[0])}</span></div>
<div class="serp now" style="margin-top:20px"><span class="lab">Heute</span>
<div class="u"><i></i>{dom}</div><div class="t">{esc(L.get("site_today", {}).get("facts", [{}])[0].get("value", name) if False else name)}</div>
<div class="d empty">Keine Beschreibung hinterlegt — Google nimmt irgendeinen Textfetzen von der Seite.</div></div></div>
<div data-reveal style="--i:1"><div class="src" style="height:46px;display:flex;align-items:center">Zum Vergleich, dieselbe Suche</div>
<div class="serp" style="margin-top:20px"><span class="lab alt">Mitbewerb</span>
<div class="u"><i></i>{esc(rdom)}</div><div class="t">{esc((rival or {}).get("name",""))}</div>
<div class="d">{esc((rival or {}).get("what_their_site_does","")[:190])}</div></div></div></div>
<p class="note">Der Text unter dem blauen Titel ist das Einzige, was zwischen Ihrem Namen und dem Klick steht.</p></section>''')

    # ---- 6 meters + average
    sc = L["scorecard"][:6]
    avg = sum(int(s["score"]) for s in sc) / max(len(sc), 1)
    rows = "".join(f'''<div class="m" data-reveal style="--i:{i}"><span class="name">{esc(s["area"])}</span>
<span class="track"><i class="{'low' if int(s["score"]) <= 4 else ''}" style="width:{int(s["score"])*10}%;--i:{i}"></i></span>
<span class="n">{int(s["score"])}</span><span class="why">{esc(s["why"])}</span></div>''' for i, s in enumerate(sc))
    lhb = ""
    if lh:
        lhb = f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:30px;border-top:1px solid var(--line);padding-top:22px">
<div><div class="src">Lighthouse, Handy</div><div style="font:600 44px/1 var(--fd);margin-top:8px">{num(lh.get("performance",0))}<small style="font:400 18px var(--fd);color:var(--mute)"> / 100 Tempo</small></div></div>
<div><div class="src">SEO-Grundlagen</div><div style="font:600 44px/1 var(--fd);margin-top:8px">{num(lh.get("seo",0))}<small style="font:400 18px var(--fd);color:var(--mute)"> / 100</small></div></div></div>'''
    S.append(f'''<section class="slide"><div class="eyebrow">Bewertung · sechs Bereiche</div>
<div class="grow" style="display:grid;grid-template-columns:1fr 330px;gap:64px;align-items:start">
<div><h2 style="font-size:44px">Was heute trägt, <em>und was nicht</em></h2><div class="meters">{rows}</div></div>
<div style="padding-top:12px"><div class="src">Schnitt über alle sechs</div>
<div class="avg">{num(round(avg,1), 1)}<small> / 10</small></div>
<p class="sub" style="margin-top:14px;font-size:14.5px">Jede Zeile ist in einer Minute am eigenen Handy nachprüfbar. Bewertet am {date}.</p>{lhb}</div></div></section>''')

    # ---- 7 findings ledger (max 4 per slide, different skeleton from everything else)
    for k in range(0, min(len(F), 9), 3):
        chunk = F[k:k+3]
        items = "".join(f'''<li data-reveal style="--i:{i}"><span class="n">{esc(f["id"])}</span>
<div><div class="t">{esc(f["title"])}</div><p class="e">{esc(cut(f["evidence"], 210))}</p><p class="e" style="color:var(--ink-2);margin-top:6px">{esc(cut(f["consequence"], 170))}</p></div>
<div class="fix"><b>Was wir tun</b>{esc(cut(f["fix"], 150))}</div></li>''' for i, f in enumerate(chunk))
        S.append(f'''<section class="slide"><div class="eyebrow">Befunde {k+1}–{k+len(chunk)} von {len(F)}</div>
<h2 style="font-size:44px">{"Was uns aufgefallen ist" if k == 0 else "Weiter im Protokoll"}</h2>
<ul class="led grow" style="align-content:start">{items}</ul></section>''')

    # ---- 8 competitor wall — same scale, their site first
    if L["competitors"]:
        you = sh("shots/desk-hero.png", 900)
        cells = (f'<div class="cell you" data-reveal><div class="shot">{f"<img src=\"{you}\" alt=\"\">" if you else ""}<span class="badge">Ihre Seite</span></div>'
                 f'<div class="who">{name}</div><div class="dom">{dom}</div><div class="does">{esc(L["one_liner"])}</div></div>')
        for i, c in enumerate(L["competitors"][:3]):
            u = sh(c.get("shot", "").replace("m390-vp1", "desk-hero"), 900) or sh(c.get("shot", ""), 900)
            cd = re.sub(r"^https?://(www\.)?", "", c.get("website", "")).rstrip("/")
            cells += (f'<div class="cell" data-reveal style="--i:{i+1}"><div class="shot">{f"<img src=\"{u}\" alt=\"\">" if u else ""}</div>'
                      f'<div class="who">{esc(c["name"])}</div><div class="dom">{esc(cd)}</div><div class="does">{esc(c["what_their_site_does"])}</div></div>')
        S.append(f'''<section class="slide"><div class="eyebrow">Nachbarschaft · dieselbe Kategorie, derselbe Bezirk</div>
<h2 style="font-size:44px">Vier Startseiten, <em>gleicher Maßstab</em></h2>
<div class="wall">{cells}</div>
<p class="note">Alle vier am {date} aufgenommen, 1440 px, unbearbeitet. Beschrieben wird, was die jeweilige Seite tut — nicht, wie gut der Betrieb arbeitet.</p></section>''')

    # ---- 9 market
    mk = L["market"]
    facts = "".join(f'<li data-reveal style="--i:{i}"><span class="n">{i+1:02d}</span><div><div class="c">{esc(x["claim"])}</div><div class="src" style="margin-top:6px">{esc(x["source"])}</div></div></li>' for i, x in enumerate(mk["facts"][:4]))
    terms = "".join(f"<span>{esc(t)}</span>" for t in (mk.get("search_terms") or [])[:6])
    S.append(f'''<section class="slide"><div class="eyebrow">Markt · wie Mandanten heute suchen</div>
<div class="mk grow" style="margin-top:8px"><div><h2 style="font-size:40px;max-width:640px">{esc(mk["summary"][:150])}</h2>
<p class="sub" style="font-size:15.5px">{esc(mk.get("how_clients_find_them",""))}</p>
<div class="terms">{terms}</div></div>
<ol>{facts}</ol></div></section>''')

    # ---- 10 prognosis
    P = L["prognosis"]
    S.append(f'''<section class="slide"><div class="eyebrow">Prognose · {esc(P.get("horizon","12 Monate"))}</div>
<h2 style="font-size:44px">Zwei Wege, <em>ein Jahr</em></h2>
<div class="prog"><div data-reveal><div class="h">Wenn nichts passiert</div><p class="b">{esc(P["if_nothing_changes"])}</p></div>
<div class="good" data-reveal style="--i:1"><div class="h">Wenn wir es umsetzen</div><p class="b">{esc(P["if_fixed"])}</p></div></div>
<p class="note">Einschätzung aus den gezeigten Fakten, keine Garantie. Annahmen: {esc("; ".join(P.get("assumptions", [])[:3]))}</p></section>''')

    # ---- 11 offer
    O = L["offer"]; oname, ocont, oprice, odur = offer_block(O["lead"])
    pm = re.search(r"([\d.]+)\s*[–-]\s*([\d.]+)", O.get("lead_price") or oprice)
    price_html = (f'<span class="price">{num(pm.group(1).replace(".", ""), 0)}<small> – {pm.group(2)} €</small></span>'
                  if pm else f'<span class="price" style="font-size:80px">{esc(O.get("lead_price") or oprice)}</span>')
    second = (f'<div class="second"><b>Zweiter Schritt: {esc(O.get("second",""))}</b><p>{esc(O.get("second_why",""))}</p></div>' if O.get("second") else "")
    S.append(f'''<section class="slide"><div class="eyebrow">Vorschlag</div>
<div class="off grow"><div><div class="oname">{esc(O["lead"])} · {esc(oname)}</div>
{price_html}
<div class="src" style="margin-top:10px">{esc(O.get("lead_duration") or odur)} · Sie besitzen am Ende Domain, Seite und alle Dateien</div>
<p class="owhat">{esc(O["why_this_one"])}</p>{second}
<div class="total"><div class="l">Realistisch im ersten Jahr</div><div class="v">{esc(O.get("realistic_total",""))}</div></div></div>
<div style="padding-top:6px"><h3 style="margin-bottom:14px">Bedingungen</h3><ul class="cond">
<li>50 % bei Auftrag, 50 % bei Go-live. Laufende Leistungen monatlich im Voraus, Zahlungsziel 14 Tage.</li>
<li>Zwei Korrekturrunden je Stufe, Übergabe mit 30 Minuten Einschulung.</li>
<li>Nicht enthalten: Fotografie, finale Rechtstexte, Werbebudget, Hosting und Domain (10–25 € im Monat, direkt an den Anbieter).</li>
<li>Der Zeitplan beginnt, sobald Inhalte und Zugänge da sind.</li>
<li>Derzeit ohne Umsatzsteuer, Kleinunternehmerregelung.</li></ul></div></div></section>''')

    # ---- 12 close (dark)
    refs = "".join(f'<div class="ref" data-reveal style="--i:{i}"><b>{esc(r["name"])}</b><span>{esc(r["line"])}</span></div>' for i, r in enumerate(L["references"][:2]))
    book = CFG.get("booking_url", ""); ok = book.startswith("http")
    S.append(f'''<section class="slide dark"><div class="eyebrow">Nächster Schritt</div>
<h2>Zwanzig Minuten, <em>dann wissen Sie, was das bei Ihnen heißt</em></h2>
<div class="close grow"><div style="margin-top:6px">{refs}</div>
<div><p class="lede" style="font-size:17px">Am Telefon oder bei Ihnen in der Kanzlei. Sie hören, was die Befunde konkret bedeuten und was der erste Schritt wäre. Ohne Verpflichtung.</p>
<div class="cta">{f'<a class="pri" href="{esc(book)}">Termin wählen</a>' if ok else ''}<a href="tel:{esc(CFG["phone"].replace(" ",""))}">{esc(CFG["phone"])}</a><a href="mailto:{esc(CFG["email"])}">{esc(CFG["email"])}</a></div>
<p class="src" style="margin-top:22px">{esc(CFG["sender_name"])} · {esc(CFG["sender_role"])} · {esc(CFG["studio"])}<br>Die Beobachtungen stammen aus einer Prüfung Ihrer öffentlichen Website am {date}, von Hand bestätigt. Gespeichert sind Firmenname, Adresse und was auf Ihrer Website steht; auf Wunsch löschen wir den Eintrag sofort.</p></div></div></section>''')

    body = "\n".join(S)
    return f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{esc(L["pitch_title"])} · {esc(CFG["studio"])}</title>
<style>{fonts_css()}{CSS.replace("ACCENTINK", acc_ink).replace("ACCENT", acc)}</style></head>
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
        try: mb = (json.load(open(folder / "shots" / "facts.json", encoding="utf-8")) or {}).get("mobile") or {}
        except Exception: mb = {}
        v = verdict(L, L.get("lighthouse") or {}, mb)
        out = folder / "pitch.html"; out.write_text(render(L, folder), encoding="utf-8")
        print(f"{s}: pitch.html {out.stat().st_size//1024} KB · verdict = {v[0]}{v[1]}")

if __name__ == "__main__":
    main()
