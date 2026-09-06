#!/usr/bin/env python3
"""
audit_site.py — fetch every prospect website from data/prospects.csv and record
objective, checkable facts (no judgement here; score.py turns facts into findings).
Resumable: already-audited websites are skipped. Writes data/audits.jsonl.

usage:  python tools/audit_site.py [--workers 24] [--limit N] [--segment S1]
"""
import argparse, csv, json, pathlib, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import requests, urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "audits.jsonl"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 dvision-sitecheck/0.1"}

BUILDERS = [  # (label, regex on html)
    ("Wix", r"wix\.com|parastorage\.com|wixstatic"),
    ("Jimdo", r"jimdo"),
    ("Squarespace", r"squarespace"),
    ("Weebly", r"weebly"),
    ("Webflow", r"webflow"),
    ("Framer", r"framer\.com|framerusercontent"),
    ("IONOS/1&1", r"ionos|1and1|mywebsite-editor|websitebuilder\.1und1"),
    ("Strato", r"strato"),
    ("GoDaddy", r"godaddy|secureserver"),
    ("Shopify", r"cdn\.shopify"),
    ("Site123/Zyro/Hostinger", r"site123|zyro|hostinger"),
    ("WordPress", r"wp-content|wp-includes"),
    ("Elementor", r"elementor"),
    ("Divi", r"et-core|divi"),
    ("TYPO3", r"typo3"),
    ("Joomla", r"joomla|/media/jui/"),
    ("Drupal", r"drupal"),
    ("Contao", r"contao"),
    ("Google Sites", r"sites\.google\.com"),
    ("Next.js", r"_next/static"),
    ("Nuxt", r"/_nuxt/"),
    ("Astro", r"astro-island|/_astro/"),
]
BOOKING = r"doctolib|calendly|terminland|termin\.one|resmio|opentable|quandoo|bookatable|thefork|treatwell|shore\.com|timify|eversports|urbanbooking|reservation|reservierung|online-termin|termin buchen|jetzt buchen|book now|acuity|setmore|planity|salonkee"
TRACKING = r"googletagmanager|gtag\(|google-analytics|analytics\.js|fbq\(|plausible\.io|matomo|piwik|hotjar|clarity\.ms|_vercel/insights"
COOKIE = r"cookie|consent|datenschutz-einstellungen|cookiebot|usercentrics|borlabs|complianz|klaro"
DATE_RE = re.compile(r"\b(0?[1-9]|[12]\d|3[01])\.\s?(0?[1-9]|1[0-2])\.\s?(20[12]\d)\b|\b(20[12]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
NAME_RE = re.compile(r"\b((?:Mag\.?|Dr\.?|DI|Dipl\.-Ing\.?|MMag\.?|Ing\.?|Prof\.?|DDr\.?|Univ\.-Prof\.?|MBA|LL\.M\.?|Mag\.a|Dr\.in)\s*(?:\([A-Za-z]+\)\s*)?[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+){1,2})")
ROLE_RE = re.compile(r"(Geschäftsführ\w*|Inhaber\w*|Obmann|Obfrau|Vorstand|Vorsitzende\w*|Eigentümer\w*|Gründer\w*|Partner\w*|Rechtsanwalt|Rechtsanwältin|Steuerberater\w*|Notar\w*|Ärztin|Arzt|Vertretungsbefugt\w*)[^\n]{0,90}", re.I)

def fetch(url, timeout=15):
    t0 = time.time()
    r = requests.get(url, headers=UA, timeout=timeout, allow_redirects=True, verify=False)
    return r, int((time.time() - t0) * 1000)

def audit_one(row):
    url = row["website"]
    a = {"pid": row["pid"], "website": url, "ok": False}
    try:
        r, ms = fetch(url)
    except Exception as e:
        a["error"] = type(e).__name__; return a
    a.update(status=r.status_code, final_url=r.url, response_ms=ms, html_bytes=len(r.content),
             https=r.url.lower().startswith("https://"), server=r.headers.get("Server", "")[:40],
             last_modified=r.headers.get("Last-Modified", ""), content_type=r.headers.get("Content-Type", "")[:40])
    if r.status_code >= 400: return a
    html = r.text[:1_500_000]; low = html.lower()
    a["ok"] = True
    s = BeautifulSoup(html, "lxml")
    text = s.get_text(" ", strip=True)
    a["title"] = (s.title.string.strip() if s.title and s.title.string else "")[:150]
    md = s.find("meta", attrs={"name": re.compile("^description$", re.I)})
    a["meta_desc_len"] = len(md.get("content", "")) if md else 0
    a["viewport"] = bool(s.find("meta", attrs={"name": re.compile("^viewport$", re.I)}))
    a["lang"] = (s.html.get("lang") if s.html else "") or ""
    a["hreflangs"] = sorted({l.get("hreflang", "").lower()[:2] for l in s.find_all("link", hreflang=True)} - {""})
    a["has_en"] = bool(re.search(r'href="[^"]*/en(/|"|\?)|hreflang="en|>\s*english\s*<|>\s*en\s*<', low))
    gen = s.find("meta", attrs={"name": re.compile("^generator$", re.I)})
    a["generator"] = gen.get("content", "")[:60] if gen else ""
    a["builders"] = [lab for lab, rx in BUILDERS if re.search(rx, low)]
    jq = re.search(r"jquery[-.]?(\d+\.\d+(?:\.\d+)?)", low); a["jquery"] = jq.group(1) if jq else ""
    bs = re.search(r"bootstrap[-.]?(\d)\.", low); a["bootstrap"] = bs.group(1) if bs else ""
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d\d)", low)]
    a["copyright_year"] = max(years) if years else 0
    dates = [int(m[2] or m[3]) for m in DATE_RE.findall(text)]
    a["newest_date_year"] = max(dates) if dates else 0
    a["h1_count"] = len(s.find_all("h1"))
    imgs = s.find_all("img"); a["img_count"] = len(imgs); a["img_no_alt"] = sum(1 for i in imgs if not i.get("alt"))
    a["word_count"] = len(text.split())
    forms = s.find_all("form")
    a["contact_form"] = any(f.find("textarea") or f.find("input", attrs={"type": "email"}) for f in forms)
    a["booking"] = bool(re.search(BOOKING, low))
    a["tracking"] = bool(re.search(TRACKING, low))
    a["cookie_banner"] = bool(re.search(COOKIE, low))
    a["mailto"] = sorted({m.lower() for m in re.findall(r"mailto:([^\"'?> ]+)", html)})[:3]
    a["tel"] = sorted({m for m in re.findall(r"tel:([+\d][\d /-]{6,})", html)})[:2]
    a["socials"] = sorted({d for d in ("instagram", "facebook", "linkedin", "youtube", "tiktok", "whatsapp") if d in low})
    a["kontakt_link"] = bool(re.search(r'href="[^"]*(kontakt|contact|impressum)', low))
    a["blog"] = bool(re.search(r'href="[^"]*/(blog|news|aktuelles|neuigkeiten|artikel|beitraege|beiträge|presse|magazin|journal)', low))
    a["mixed_content"] = a["https"] and bool(re.search(r'(src|href)="http://(?!www\.w3\.org)', html))
    a["favicon"] = bool(s.find("link", rel=re.compile("icon", re.I)))
    a["google_fonts"] = "fonts.googleapis.com" in low
    a["under_construction"] = bool(re.search(r"under construction|im aufbau|coming soon|in kürze|demnächst online|website befindet sich", low))
    a["placeholder_text"] = bool(re.search(r"lorem ipsum|beispieltext", low))
    a["og_image"] = bool(s.find("meta", property="og:image"))
    a["schema_org"] = 'application/ld+json' in low
    a["tables"] = len(s.find_all("table"))
    a["flash_or_frames"] = bool(s.find("frameset") or s.find("embed", type=re.compile("flash")))
    # Impressum → decision-maker hints
    imp = None
    for l in s.find_all("a", href=True):
        h = l["href"].lower(); tx = l.get_text(" ", strip=True).lower()
        if "impressum" in h or "impressum" in tx or "imprint" in h or "kontakt" in h and imp is None:
            if "impressum" in h or "impressum" in tx or "imprint" in h:
                imp = urljoin(r.url, l["href"]); break
    a["impressum_url"] = imp or ""
    if imp:
        try:
            ir, _ = fetch(imp, 12)
            it = BeautifulSoup(ir.text[:400_000], "lxml").get_text("\n", strip=True)
            m = re.search(r"impressum", it, re.I); snippet = it[m.start():m.start()+1500] if m else it[:1500]
            a["impressum_snippet"] = re.sub(r"\n{2,}", "\n", snippet)
            a["names"] = sorted(set(NAME_RE.findall(it)))[:6]
            a["roles"] = [x if isinstance(x, str) else x[0] for x in ROLE_RE.findall(it)][:4]
            a["roles"] = [m.group(0)[:110] for m in ROLE_RE.finditer(it)][:4]
            a["impressum_emails"] = sorted({m.lower() for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", it)})[:3]
        except Exception as e:
            a["impressum_error"] = type(e).__name__
    return a

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=24); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--segment", default="")
    args = ap.parse_args()
    rows = list(csv.DictReader(open(DATA / "prospects.csv", encoding="utf-8")))
    rows = [r for r in rows if r["website"] and (not args.segment or r["segment"].upper().startswith(args.segment.upper()))]
    done = set()
    if OUT.exists():
        for line in open(OUT, encoding="utf-8"):
            try: done.add(json.loads(line)["pid"])
            except Exception: pass
    todo = [r for r in rows if r["pid"] not in done]
    if args.limit: todo = todo[:args.limit]
    print(f"{len(rows)} with website, {len(done)} done, {len(todo)} to audit", flush=True)
    t0 = time.time(); n = 0
    with open(OUT, "a", encoding="utf-8") as f, ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(audit_one, r): r for r in todo}
        for fut in as_completed(futs):
            try: a = fut.result()
            except Exception as e: a = {"pid": futs[fut]["pid"], "website": futs[fut]["website"], "ok": False, "error": "crash:" + type(e).__name__}
            f.write(json.dumps(a, ensure_ascii=False) + "\n"); f.flush(); n += 1
            if n % 50 == 0: print(f"  {n}/{len(todo)}  {int(time.time()-t0)}s", flush=True)
    print(f"done {n} in {int(time.time()-t0)}s → {OUT}")

if __name__ == "__main__":
    main()
