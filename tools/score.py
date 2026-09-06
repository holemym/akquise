#!/usr/bin/env python3
"""
score.py — turn audit facts into findings (German "Befund" lines), a pain score,
and a recommended offer per prospect. Writes:
  data/prospects_scored.csv   — everything, sorted by score
  data/SHORTLIST.md           — per-segment top lists with Befund lines (for the outreach person)
  data/STATS.md               — pipeline numbers

usage: python tools/score.py [--top 40]
"""
import argparse, csv, json, pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CENTRAL = {1, 2, 3, 4, 5, 6, 7, 8, 9, 18, 19}
BUILDER_WEAK = {"Wix", "Jimdo", "Weebly", "IONOS/1&1", "Strato", "GoDaddy", "Google Sites", "Site123/Zyro/Hostinger"}
# offer keys must match OFFERS.md ids
OFFER_LABEL = {
    "A1": "A1 · Website Start (keine Website)",
    "A2": "A2 · Relaunch (Website erneuern)",
    "A3": "A3 · Sichtbarkeit: SEO-Basis + Fachtexte",
    "A4": "A4 · Anfrage & Buchung (Conversion-Fix)",
    "A5": "A5 · Mehrsprachig DE/EN",
    "B1": "B1 · Digital-Betrieb (laufend)",
    "C1": "C1 · Interne Tools & Automatisierung",
    "X0": "— kein klarer Bedarf sichtbar",
}

def findings(row, a):
    """returns (score, tags, befund_lines(DE), offer)"""
    seg = row["segment"]; sc = 0; tags = []; lines = []
    d = int(row["district"]) if row["district"] else 0
    if not row["website"]:
        tags.append("NO_SITE"); sc += 7
        lines.append("Auf OpenStreetMap/Google ohne eigene Website gelistet – Kund:innen finden nur Adresse und Telefon.")
        offer = "A1"
        if seg == "S4-immobilien": tags.append("OPS_CANDIDATE")
        return sc, tags, lines, offer
    if not a or not a.get("ok"):
        st = (a or {}).get("status"); err = (a or {}).get("error")
        if st in (401, 403, 429, 503, 530) or err in ("ReadTimeout", "ConnectTimeout"):
            tags.append("BLOCKED")  # bot protection or slow host — not a finding, human check
            return 0, tags, lines, "X0"
        tags.append("SITE_DOWN"); sc += 8
        lines.append(f"Die hinterlegte Website war bei unserer Prüfung nicht erreichbar ({err or 'HTTP ' + str(st)}) – wer den Link aus Google anklickt, landet im Leeren.")
        return sc, tags, lines, "A2"
    if a.get("under_construction") or a.get("placeholder_text"):
        tags.append("UNFINISHED"); sc += 5; lines.append("Die Website ist sichtbar unfertig (Baustellen-/Platzhaltertext).")
    if not a.get("https"):
        tags.append("NO_HTTPS"); sc += 3; lines.append("Kein HTTPS – Browser zeigen „Nicht sicher“ neben dem Namen an.")
    if not a.get("viewport"):
        tags.append("NOT_MOBILE"); sc += 4; lines.append("Kein mobiles Layout – am Handy muss gezoomt und geschoben werden (über 60 % der Besuche kommen mobil).")
    weak = [b for b in a.get("builders", []) if b in BUILDER_WEAK]
    if weak:
        tags.append("BUILDER"); sc += 2; lines.append(f"Baukasten-Seite ({weak[0]}) – begrenzt bei Geschwindigkeit, SEO und Gestaltung.")
    cy, ny = a.get("copyright_year", 0), a.get("newest_date_year", 0)
    latest = max(cy, ny)
    if 0 < latest <= 2022:
        tags.append("STALE"); sc += 3; lines.append(f"Letztes sichtbares Datum auf der Seite: {latest} – die Website wirkt verlassen.")
    elif latest == 2023:
        tags.append("STALE"); sc += 2; lines.append("Letztes sichtbares Datum: 2023 – seit über zwei Jahren nichts Neues.")
    if not a.get("title"):
        tags.append("SEO_BASICS"); sc += 2
        lines.append("Der Seitentitel ist leer – in Google-Ergebnissen steht statt Ihres Namens nur die Adresse der Seite.")
    elif a.get("meta_desc_len", 0) == 0:
        tags.append("SEO_BASICS"); sc += 2
        lines.append("Keine Beschreibung für Google hinterlegt – unter Ihrem Namen zeigt die Suche zufälligen Text von der Seite.")
    if a.get("h1_count", 1) == 0:
        tags.append("NO_H1"); sc += 1
    if a.get("response_ms", 0) > 3500 or a.get("html_bytes", 0) > 2_500_000:
        tags.append("SLOW"); sc += 2; lines.append(f"Langsam: die Startseite braucht {a.get('response_ms',0)/1000:.1f} s bis zur ersten Antwort.")
    jq = a.get("jquery", ""); bs = a.get("bootstrap", "")
    if (jq and jq.startswith("1.")) or bs == "3" or a.get("flash_or_frames") or a.get("tables", 0) > 6:
        tags.append("OLD_TECH"); sc += 2; lines.append("Technisch veraltet (alte Bibliotheken/Tabellenlayout) – schwer zu pflegen, unsicher.")
    if a.get("mixed_content"):
        tags.append("MIXED"); sc += 1
    if not a.get("tracking"):
        tags.append("NO_ANALYTICS"); sc += 1  # tag only — too weak to print
    needs_booking = seg in ("S2-gesundheit", "S6-studios", "S3-gastro")
    if needs_booking and not a.get("booking"):
        tags.append("NO_BOOKING"); sc += 2; lines.append("Keine Online-Terminbuchung/Reservierung – Anfragen laufen nur über Telefon.")
    if not a.get("contact_form") and not a.get("mailto"):
        tags.append("NO_CONTACT"); sc += 2  # tag only — contact usually sits on a subpage we don't fetch; human check
    elif not a.get("contact_form"):
        tags.append("NO_FORM"); sc += 1
    needs_en = seg in ("S1-beratung", "S2-gesundheit", "S3-gastro", "S4-immobilien") and d in CENTRAL
    if needs_en and not a.get("has_en") and "en" not in a.get("hreflangs", []):
        tags.append("NO_EN"); sc += 1; lines.append("Nur Deutsch – im Bezirk mit hohem Anteil internationaler Kund:innen fehlt eine englische Version.")
    if seg in ("S1-beratung", "S4-immobilien") and not a.get("blog"):
        tags.append("NO_CONTENT"); sc += 1; lines.append("Keine Fachbeiträge/Aktuelles – nichts, was Google oder Kund:innen einen Grund zum Wiederkommen gibt.")
    if a.get("img_count", 0) >= 5 and a.get("img_no_alt", 0) / max(a.get("img_count", 1), 1) > 0.6:
        tags.append("NO_ALT"); sc += 1
    if a.get("word_count", 0) < 120:
        tags.append("THIN"); sc += 1  # tag only — JS-rendered sites look thin to the fetcher
    if not a.get("og_image"):
        tags.append("NO_OG")
    # offer choice
    t = set(tags)
    if {"NOT_MOBILE", "UNFINISHED", "OLD_TECH"} & t or ({"BUILDER", "STALE"} <= t) or ({"STALE", "NO_HTTPS"} <= t):
        offer = "A2"
    elif "NO_BOOKING" in t and sc >= 4:
        offer = "A4"
    elif {"SEO_BASICS", "NO_CONTENT", "THIN"} & t and sc >= 3:
        offer = "A3"
    elif "NO_EN" in t and sc >= 3:
        offer = "A5"
    elif sc >= 3:
        offer = "B1"
    else:
        offer = "X0"
    if seg == "S4-immobilien": tags.append("OPS_CANDIDATE")
    return sc, tags, lines, offer

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--top", type=int, default=40); args = ap.parse_args()
    rows = list(csv.DictReader(open(DATA / "prospects.csv", encoding="utf-8")))
    audits = {}
    if (DATA / "audits.jsonl").exists():
        for line in open(DATA / "audits.jsonl", encoding="utf-8"):
            try: a = json.loads(line); audits[a["pid"]] = a
            except Exception: pass
    # helper-owned CRM columns survive re-scoring (merge by pid from the previous scored file)
    CRM = ("status", "kanal", "kontaktiert_am", "antwort", "notiz")
    keep = {}
    prev = DATA / "prospects_scored.csv"
    if prev.exists():
        for o in csv.DictReader(open(prev, encoding="utf-8")):
            keep[o["pid"]] = {k: o.get(k, "") for k in CRM}
    out = []
    for r in rows:
        a = audits.get(r["pid"])
        if r["website"] and a is None:
            continue  # not audited yet
        sc, tags, lines, offer = findings(r, a)
        names = "; ".join(dict.fromkeys(n.splitlines()[0].strip(" -–,") for n in (a or {}).get("names", []) if n.strip()))
        roles = " | ".join(x.splitlines()[0] for x in (a or {}).get("roles", [])[:2] if x.strip())
        emails = ", ".join(dict.fromkeys(([r["email"]] if r["email"] else []) + (a or {}).get("mailto", []) + (a or {}).get("impressum_emails", [])))
        out.append({**r, "score": sc, "offer": offer, "offer_label": OFFER_LABEL[offer], "tags": " ".join(tags),
                    "befund": " // ".join(lines), "builder": ",".join((a or {}).get("builders", [])[:2]),
                    "latest_year": max((a or {}).get("copyright_year", 0), (a or {}).get("newest_date_year", 0)) or "",
                    "names": names, "roles": roles, "emails_found": emails,
                    "impressum_url": (a or {}).get("impressum_url", ""), "final_url": (a or {}).get("final_url", ""),
                    **(keep.get(r["pid"]) or {"status": "neu", "kanal": "", "kontaktiert_am": "", "antwort": "", "notiz": ""})})
    out.sort(key=lambda x: (-x["score"], x["segment"], x["name"].lower()))
    with open(DATA / "prospects_scored.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    # stats
    seg_n = Counter(r["segment"] for r in rows); seg_web = Counter(r["segment"] for r in rows if r["website"])
    seg_aud = Counter(o["segment"] for o in out if o["website"]); off = Counter(o["offer"] for o in out)
    tagc = Counter(t for o in out for t in o["tags"].split())
    with open(DATA / "STATS.md", "w", encoding="utf-8") as f:
        f.write("# Pipeline stats\n\n| Segment | harvested | with website | audited | no website |\n|---|---|---|---|---|\n")
        for s in sorted(seg_n): f.write(f"| {s} | {seg_n[s]} | {seg_web[s]} | {seg_aud[s]} | {seg_n[s]-seg_web[s]} |\n")
        f.write("\n## Offer distribution (scored prospects)\n\n| Offer | n |\n|---|---|\n")
        for k, v in off.most_common(): f.write(f"| {OFFER_LABEL[k]} | {v} |\n")
        f.write("\n## Tag frequency\n\n| Tag | n |\n|---|---|\n")
        for k, v in tagc.most_common(): f.write(f"| {k} | {v} |\n")
    # shortlist
    by = defaultdict(list)
    for o in out:
        if o["offer"] != "X0": by[o["segment"]].append(o)
    with open(DATA / "SHORTLIST.md", "w", encoding="utf-8") as f:
        f.write(f"# Shortlist — Top {args.top} je Segment (nach Score)\n\nQuelle: `prospects_scored.csv`. Score = Summe der Befunde. Befund-Zeilen sind bereits auf Deutsch und können in den Brief übernommen werden (bitte vorher am Handy/Browser gegenprüfen — die Prüfung ist automatisch).\n\n")
        for s in sorted(by):
            f.write(f"\n## {s} ({len(by[s])} mit Bedarf)\n\n")
            for o in by[s][:args.top]:
                site = o["website"] or "— keine Website —"
                f.write(f"### {o['name']} · {o['postcode']} Wien · Score {o['score']} · {o['offer_label']}\n")
                f.write(f"- {site}" + (f" · {o['street']}" if o['street'] else "") + (f" · {o['phone']}" if o['phone'] else "") + "\n")
                if o["names"] or o["roles"]: f.write(f"- Ansprechperson (aus Impressum, prüfen): {o['names']} {('· ' + o['roles']) if o['roles'] else ''}\n")
                if o["emails_found"]: f.write(f"- E-Mail (nur mit Einwilligung nutzen!): {o['emails_found']}\n")
                for l in o["befund"].split(" // "):
                    if l: f.write(f"- Befund: {l}\n")
                f.write("\n")
    print(f"scored {len(out)} · shortlist + stats written")

if __name__ == "__main__":
    main()
