#!/usr/bin/env python3
"""
validate.py — second pass over scored prospects: is this business ALIVE, is it a REAL prospect
for a one-person studio, and how likely is it to buy? Produces tiers A/B/C and an exclusion list.

The scorer answers "does their web presence have problems". This answers "should we spend a letter
and an hour on them". Three independent axes:

  LIVE  — is the business still trading?          (fresh fetch, DNS, parked/closed detection, recency)
  FIT   — would they ever hire a solo studio?     (size, entity type, institution/corporate filters)
  PAIN  — is the problem real and worth money?    (structural findings only, not cosmetic tags)

Writes data/validated.csv, data/TIERS.md, and fills the CRM `status`/`notiz` columns for excluded rows.

usage: python tools/validate.py --segments S1,S4 --districts 1-9,18,19 [--workers 16]
"""
import argparse, csv, json, re, socket, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, urllib3
from bs4 import BeautifulSoup
from common import DATA, load_scored, select, parse_districts, domain, befunde

urllib3.disable_warnings()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"}

# --- who is never a prospect for a one-person studio -------------------------------------------
EXCLUDE = [
    # "kammer\b" not "\bkammer\b": the word only ever appears as a compound (Rechtsanwaltskammer, Wirtschaftskammer)
    ("institution", r"kammer\b|verband\b|ministerium|magistrat|bezirksamt|universit|hochschule|akademie|innung\b|behörde|stadt wien|republik"),
    ("konzern", r"mckinsey|boston consulting|bain & |deloitte|\bkpmg\b|\bpwc\b|pricewaterhouse|ernst & young|accenture|capgemini|taxand|grant thornton|\bbdo\b|mazars|freshfields|baker mckenzie|dla piper|cms |dorda|schoenherr|wolf theiss|binder grösswang"),
    ("kette/franchise", r"re/?max|century ?21|engel & völkers|coldwell|keller williams|immobilien ?scout|willhaben"),
    ("konzern-immo", r"buwog|immofinanz|s ?immo|ca immo|wienerberger|strabag|porr |signa|erste |raiffeisen|sparkasse|bank\b|versicherung"),
    ("star-büro", r"coop himmelb|zaha hadid|snøhetta|bjarke ingels|delugan meissl|querkraft|the next enterprise"),
]
# Closure must be stated ABOUT this business, in closure framing. Never match bare topic words:
# lawyers and tax advisors sell "Insolvenzrecht" and "Liquidation" — those are services, not obituaries.
# (Matching them cost us three good leads on the first run: dr-pfister.at, rakwien.at, ra-novotny.at.)
DEAD = (r"(kanzlei|praxis|ordination|büro|betrieb|unternehmen)\s+(wurde|ist|bleibt|hat)\s+(dauerhaft\s+|endgültig\s+)?geschlossen"
        r"|(trete|treten|tritt)\s+in\s+den\s+ruhestand|in\s+den\s+ruhestand\s+(getreten|verabschiedet)"
        r"|(meine|unsere)\s+(tätigkeit|kanzlei|praxis)\s+(wurde\s+)?(ein|be)gestellt"
        r"|(tätigkeit|geschäftsbetrieb)\s+(wurde\s+)?eingestellt"
        r"|geschäftsaufgabe|dauerhaft geschlossen|wir haben (unsere pforten )?geschlossen"
        r"|nicht mehr (als \w+ )?tätig|diese (website|seite) wird nicht mehr (betreut|gepflegt)")
PARKED = r"domain (steht zum verkauf|is for sale|kaufen)|diese domain (ist|steht)|parkingcrew|sedoparking|bodis\.com|afternic|hugedomains|domain parking|website coming soon|default web site page|es tut uns leid.*nicht verfügbar"
# structural = worth a letter; cosmetic = not worth a stamp on its own
STRUCTURAL = {"NO_SITE", "SITE_DOWN", "NOT_MOBILE", "UNFINISHED", "OLD_TECH", "STALE", "NO_HTTPS", "BUILDER", "SLOW"}
ENTITY_SOLO = r"\b(e\.?u\.?|einzelunternehm|freiberuf)\b"
ENTITY_FIRM = r"\b(gmbh|og\b|kg\b|ag\b|partnerschaft|rechtsanwälte|partner)\b"

def live_check(row):
    """fresh fetch + DNS; returns liveness facts"""
    out = {"pid": row["pid"], "dns": False, "http": 0, "parked": False, "dead_text": False,
           "final": "", "year": 0, "body_words": 0, "err": "", "found_site": ""}
    url = row["website"]
    if not url:
        out["dns"] = True  # no website is a finding, not death; liveness decided by phone/address
        out["found_site"] = probe_missing_site(row)
        return out
    host = re.sub(r"^https?://", "", url).split("/")[0]
    try:
        socket.getaddrinfo(host, 443)
        out["dns"] = True
    except Exception:
        out["err"] = "DNS"
        return out
    try:
        r = requests.get(url, headers=UA, timeout=18, allow_redirects=True, verify=False)
        out["http"] = r.status_code
        out["final"] = r.url
        if r.status_code < 400:
            low = r.text[:400_000].lower()
            out["parked"] = bool(re.search(PARKED, low))
            out["dead_text"] = bool(re.search(DEAD, low))
            txt = BeautifulSoup(r.text[:400_000], "lxml").get_text(" ", strip=True)
            out["body_words"] = len(txt.split())
            yrs = [int(y) for y in re.findall(r"\b(20[12]\d)\b", txt)]
            out["year"] = max(yrs) if yrs else 0
    except Exception as e:
        out["err"] = type(e).__name__
    return out

MONEY_CATS = ("lawyer", "notary", "tax_advisor", "accountant", "property_management", "estate_agent")

STOP = r"\b(gmbh|og|kg|ag|mag|dr|dipl|ing|ddr|mmag|rechtsanwalts?|rechtsanwälte|rechtsanwältin|notar|notariat|immobilien|immobilienmakler|immobilientreuhand|immobilienverwaltung|sachverständigenbüro|wirtschaftstreuhand|steuerberat\w*|architekt\w*|consulting|partner|und|luxury|real|estate)\b"

def probe_missing_site(row):
    """A prospect tagged 'no website' may simply be untagged in OSM. Before we ever post
    'nobody can find you online', try the obvious domains and require the business's own
    distinctive name tokens to appear on the page. Returns a URL or ""."""
    n = row["name"].lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    n = re.sub(STOP, " ", n)
    toks = [t for t in re.split(r"[^a-z0-9]+", n) if len(t) > 3]
    if not toks: return ""
    cands = []
    if len(toks) >= 2: cands += [toks[0] + toks[1], toks[0] + "-" + toks[1]]
    cands.append(toks[0])
    # distinctive tokens the page must mention for us to believe it is really them
    need = [t for t in toks if len(t) > 4] or toks
    for c in dict.fromkeys(cands):
        for tld in (".at", ".com"):
            d = c + tld
            try:
                socket.getaddrinfo(d, 443)
                r = requests.get("https://" + d, headers=UA, timeout=8, verify=False)
                if r.status_code >= 400: continue
                txt = BeautifulSoup(r.text[:200_000], "lxml").get_text(" ", strip=True).lower()
                txt = txt.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
                if sum(1 for t in need if t in txt) >= min(2, len(need)) and "wien" in txt:
                    return "https://" + d
            except Exception:
                continue
    return ""

def classify(row, lv):
    """Tier by OPPORTUNITY TYPE, not by summed scores.

    A  undeniable need + money + reachable decider  → letter now
    B  real structural problem, softer story        → letter after A
    C  finding not yet trustworthy (JS site/blocked/no name) → human check first
    D  alive and good fit, but only cosmetic gaps   → no Befund letter; growth pitch later
    X  never: institution, corporate, franchise, dead, parked
    """
    name = row["name"].lower(); why = []
    tags = set(row["tags"].split())
    cat = row["category"].split("=")[-1]
    has_site = bool(row["website"])

    # --- hard exclusions -----------------------------------------------------------------------
    for label, rx in EXCLUDE:
        if re.search(rx, name):
            return "X", 0, 0, 0, [f"kein Prospect: {label}"]
    if lv["parked"]:
        return "X", 0, 0, 0, ["Domain geparkt/zum Verkauf — Betrieb vermutlich weg"]
    if lv["dead_text"]:
        return "X", 0, 0, 0, ["Website meldet Schließung/Ruhestand"]
    if has_site and not lv["dns"]:
        # the OSM url is stale — that says nothing about the business, only about the tag
        return "C", 1, 0, 0, ["OSM-Adresse löst nicht auf — aktuelle Domain von Hand suchen (der Betrieb kann sehr wohl aktiv sein)"]

    # --- LIVE: is it trading? ------------------------------------------------------------------
    live = 0
    if lv["http"] and lv["http"] < 400: live += 2; why.append("Website erreichbar")
    if lv["year"] >= 2025: live += 2; why.append(f"aktueller Inhalt ({lv['year']})")
    elif lv["year"] == 2024: live += 1
    elif 0 < lv["year"] <= 2021: live -= 1; why.append(f"jüngstes Datum {lv['year']}")
    if row["phone"]: live += 2; why.append("Telefon gelistet")
    if row["street"]: live += 1
    if row["emails_found"]: live += 1
    if row.get("opening_hours"): live += 2; why.append("Öffnungszeiten gepflegt")

    # --- FIT: would they hire a one-person studio? ---------------------------------------------
    fit = 0
    n_names = len([x for x in row["names"].split(";") if x.strip()])
    if 0 < n_names <= 3: fit += 2; why.append("überschaubares Büro, Entscheider im Impressum")
    elif 4 <= n_names <= 6: fit += 1
    elif n_names > 6: fit -= 1; why.append("größere Sozietät — längerer Entscheidungsweg")
    if re.search(ENTITY_SOLO, name): fit += 1
    if cat in MONEY_CATS: fit += 2; why.append("zahlungskräftige Kategorie")
    elif cat in ("architect", "financial_advisor"): fit += 1
    if lv["body_words"] and lv["body_words"] < 250: fit += 1  # nobody is maintaining this

    # --- PAIN: which opportunity is this? -------------------------------------------------------
    structural = tags & STRUCTURAL
    pain = len(structural) * 2 + (1 if "SEO_BASICS" in tags else 0) + (1 if "NO_EN" in tags else 0)
    if structural: why.append("struktureller Mangel: " + ", ".join(sorted(structural)))

    # undeniable = a problem the owner cannot argue with, provable in one screenshot
    undeniable = bool({"NO_SITE", "SITE_DOWN", "NOT_MOBILE", "UNFINISHED"} & tags) or "STALE" in tags and lv["year"] and lv["year"] <= 2022
    softer = bool({"BUILDER", "OLD_TECH", "SLOW", "STALE", "NO_HTTPS"} & tags)
    needs_eyes = "BLOCKED" in tags or (has_site and lv["http"] == 200 and lv["body_words"] == 0) or (has_site and not row["names"])
    if "BLOCKED" in tags: why.append("⚠ Audit blockiert (Bot-Schutz) — Befund von Hand prüfen")
    if has_site and lv["http"] == 200 and lv["body_words"] == 0:
        why.append("⚠ Seite rendert nur mit JavaScript — automatischer Befund unzuverlässig")
    if has_site and not row["names"]:
        why.append("⚠ kein Entscheidername gefunden — Impressum/LinkedIn/WKO nachschlagen")

    # no-website prospects are the cleanest sale — but only if they really have none.
    if not has_site:
        if lv.get("found_site"):
            return "C", live, fit, 0, why + [
                f"❌ A1-Brief VERBOTEN: es gibt sehr wohl eine Website ({lv['found_site']}) — OSM war nur nicht getaggt. Seite prüfen und neu bewerten"]
        why.append("⚠ VOR dem Brief googeln: existiert doch eine Website, ist der Brief falsch")

    # --- tier ----------------------------------------------------------------------------------
    # A missing OSM phone is a gap in OpenStreetMap, not proof the business is gone — so a
    # prospect without a website is never killed on liveness, it goes to the human-check pile.
    if live < 3:
        if not has_site:
            return "C", live, fit, pain, why + ["keine Website und kein Telefon in OSM — Existenz und Kontakt von Hand prüfen (Google, WKO Firmen A-Z)"]
        return "X", live, fit, pain, why + ["kaum Lebenszeichen (kein Telefon/Adresse/aktueller Inhalt)"]
    if needs_eyes and undeniable is False:
        tier = "C"
    elif undeniable and fit >= 3 and live >= 4:
        tier = "A"
    elif undeniable or (softer and fit >= 3):
        tier = "B"
    elif needs_eyes:
        tier = "C"
    else:
        tier = "D"; why.append("nur kosmetische Lücken — kein Befund-Brief, später Wachstums-Pitch (A3)")
    return tier, live, fit, pain, why

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", default=""); ap.add_argument("--districts", default="")
    ap.add_argument("--top", type=int, default=999); ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--min-score", type=int, default=3)
    a = ap.parse_args()
    rows = select(load_scored(), top=a.top, segments=[s for s in a.segments.split(",") if s],
                  districts=parse_districts(a.districts), min_score=a.min_score)
    # enrich from the Overpass cache: opening_hours is a strong "this business is real and tended" signal
    hours = {}
    for f in (DATA / "raw").glob("*.json"):
        try:
            for e in json.load(open(f, encoding="utf-8")):
                t = e.get("tags", {})
                if t.get("opening_hours"):
                    hours[f"{e['type']}/{e['id']}"] = t["opening_hours"]
        except Exception:
            pass
    for r in rows:
        r["opening_hours"] = hours.get(r.get("osm", ""), "")
    print(f"validating {len(rows)} prospects… ({sum(1 for r in rows if r['opening_hours'])} with opening hours)", flush=True)
    lv = {}
    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(live_check, r): r for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            try: o = f.result()
            except Exception as e: o = {"pid": futs[f]["pid"], "dns": False, "http": 0, "parked": False, "dead_text": False, "final": "", "year": 0, "body_words": 0, "err": "crash"}
            lv[o["pid"]] = o
            if i % 25 == 0: print(f"  {i}/{len(rows)} {int(time.time()-t0)}s", flush=True)

    out = []
    for r in rows:
        v = lv.get(r["pid"], {"dns": True, "http": 0, "parked": False, "dead_text": False, "year": 0, "body_words": 0, "err": ""})
        tier, live, fit, pain, why = classify(r, v)
        out.append({**r, "tier": tier, "live": live, "fit": fit, "pain": pain,
                    "recheck_http": v["http"], "recheck_year": v["year"], "recheck_words": v["body_words"],
                    "recheck_err": v["err"], "gefundene_website": v.get("found_site",""), "why": " · ".join(why)})
    order = {"A": 0, "B": 1, "C": 2, "D": 3, "X": 4}
    out.sort(key=lambda x: (order[x["tier"]], -(x["live"] + x["fit"] + x["pain"]), x["name"].lower()))
    with open(DATA / "validated.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    from collections import Counter
    cnt = Counter(o["tier"] for o in out)

    TITLES = {
        "A": ("Tier A — zuerst anschreiben", "Lebt, zahlungskräftig, Entscheider bekannt, und der Mangel ist unbestreitbar und mit einem Screenshot beweisbar."),
        "B": ("Tier B — danach anschreiben", "Echter struktureller Mangel, aber die Geschichte ist weicher oder der Entscheider fehlt noch."),
        "C": ("Tier C — erst prüfen, dann entscheiden", "Der automatische Befund ist hier NICHT belastbar. Kein Brief, bevor ein Mensch nachgesehen hat."),
        "D": ("Tier D — Beobachtungsliste", "Betrieb ist gesund, nur kosmetische Lücken. Kein Befund-Brief — das wäre Nörgeln. Später Wachstums-Pitch (A3) oder Vorbeigehen."),
        "X": ("Tier X — nie anschreiben", "Institution, Konzern, Franchise, aufgegeben oder geparkt."),
    }
    with open(DATA / "TIERS.md", "w", encoding="utf-8") as f:
        f.write(f"# Tiers — {time.strftime('%Y-%m-%d')} · {len(out)} geprüfte Prospects\n\n")
        f.write("Erzeugt von `tools/validate.py`. Reihenfolge der Arbeit: **A → B → C prüfen → D beobachten**. "
                "Spalten `status/kanal/kontaktiert_am/antwort/notiz` werden in `prospects_scored.csv` gepflegt.\n\n")
        f.write("| Tier | Anzahl | Bedeutung |\n|---|---|---|\n")
        for t in "ABCDX":
            f.write(f"| {t} | {cnt.get(t,0)} | {TITLES[t][1]} |\n")
        for t in "ABCDX":
            rows_t = [o for o in out if o["tier"] == t]
            if not rows_t: continue
            f.write(f"\n\n## {TITLES[t][0]} ({len(rows_t)})\n\n{TITLES[t][1]}\n\n")
            for o in rows_t:
                site = o["website"] or "**keine Website in OSM**"
                f.write(f"### {o['name']} · {o['postcode']} Wien · {o['category'].split('=')[-1]} · {o['offer_label']}\n")
                f.write(f"- {site}" + (f" · {o['phone']}" if o["phone"] else "") + (f" · {o['street']}" if o["street"] else "") + "\n")
                if o["names"]: f.write(f"- Ansprechperson (Impressum, prüfen): {o['names']}\n")
                if o.get("gefundene_website"): f.write(f"- ❌ **Website existiert doch:** {o['gefundene_website']}\n")
                for l in [x for x in o["befund"].split(" // ") if x]:
                    f.write(f"- Befund: {l}\n")
                f.write(f"- Bewertung: LIVE {o['live']} · FIT {o['fit']} · PAIN {o['pain']} — {o['why']}\n\n")
    print("tiers:", cnt.most_common())
    print(f"→ data/validated.csv + data/TIERS.md ({len(out)} rows, {int(time.time()-t0)}s)")

if __name__ == "__main__":
    main()
