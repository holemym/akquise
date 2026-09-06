#!/usr/bin/env python3
"""
harvest_osm.py — pull Vienna businesses per segment from OpenStreetMap (Overpass API)
into data/prospects.csv. Free, legal (ODbL), no key. Re-run any time; it overwrites.

usage:  python tools/harvest_osm.py            # all segments
        python tools/harvest_osm.py S1 S4      # only these segment prefixes
"""
import csv, json, pathlib, re, sys, time
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
UA = {"User-Agent": "dvision-prospecting/0.1 (mora@d-vision.design)"}
OVERPASS = "https://overpass-api.de/api/interpreter"

# segment -> list of OSM key=value selectors (see STRATEGY.md §3 for why these)
SEGMENTS = {
    "S1-beratung":       ["office=lawyer", "office=tax_advisor", "office=notary", "office=accountant",
                          "office=financial_advisor", "office=architect", "office=consulting"],
    "S2-gesundheit":     ["healthcare=physiotherapist", "healthcare=psychotherapist", "amenity=dentist",
                          "amenity=doctors", "healthcare=alternative", "healthcare=midwife", "amenity=veterinary"],
    "S3-gastro":         ["amenity=restaurant", "amenity=cafe"],
    "S4-immobilien":     ["office=estate_agent", "office=property_management"],
    "S5-vereine":        ["office=association", "office=ngo", "office=charity", "office=foundation", "office=religion"],
    "S6-studios":        ["shop=hairdresser", "shop=beauty", "leisure=fitness_centre", "craft=photographer",
                          "craft=tailor", "craft=carpenter", "craft=joiner", "craft=electrician", "craft=plumber",
                          "craft=painter", "shop=tattoo", "leisure=dance"],
    "S7-bildung-kultur": ["amenity=language_school", "amenity=music_school", "amenity=dancing_school",
                          "tourism=gallery", "office=coworking", "amenity=driving_school"],
}

MIRRORS = [OVERPASS, "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
RAW = DATA / "raw"; RAW.mkdir(exist_ok=True)

def overpass_one(selector):
    """one selector per query (small, fast, mirror-rotated, cached per selector)"""
    cache = RAW / (selector.replace("=", "_").replace(":", "_") + ".json")
    if cache.exists():
        return json.load(open(cache, encoding="utf-8"))
    k, v = selector.split("=")
    # area id = 3600000000 + relation id of Wien (109166); skips the slow name lookup, works on all mirrors
    q = f'''[out:json][timeout:120];
area(3600109166)->.a;
nwr["{k}"="{v}"](area.a);
out tags center 40000;'''
    for attempt in range(6):
        url = MIRRORS[attempt % len(MIRRORS)]
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=150)
            if r.status_code == 200:
                els = r.json().get("elements", [])
                if els:  # mirrors sometimes answer 200 with an empty set under load — never cache that
                    json.dump(els, open(cache, "w", encoding="utf-8"))
                    return els
                print(f"    {selector}: empty 200 from {url.split('/')[2]}, retry in {15*(attempt+1)}s", flush=True)
                time.sleep(15 * (attempt + 1)); continue
            print(f"    {selector}: {r.status_code} from {url.split('/')[2]}, retry in {15*(attempt+1)}s", flush=True)
        except requests.RequestException as e:
            print(f"    {selector}: {type(e).__name__} from {url.split('/')[2]}, retry in {15*(attempt+1)}s", flush=True)
        time.sleep(15 * (attempt + 1))
    print(f"    {selector}: GAVE UP (rerun later; cache will fill)", flush=True)
    return []

def overpass(selectors):
    els = []
    for s in selectors:
        part = overpass_one(s); els.extend(part)
        print(f"    {s}: {len(part)}", flush=True)
        time.sleep(3)
    return els

def norm_url(u):
    if not u: return ""
    u = u.strip().split(";")[0].split(" ")[0]
    if not re.match(r"^https?://", u, re.I): u = "https://" + u
    return u

def tag(t, *keys):
    for k in keys:
        if t.get(k): return t[k].strip()
    return ""

def category_of(t):
    for k in ("office", "healthcare", "amenity", "shop", "leisure", "craft", "tourism"):
        if t.get(k): return f"{k}={t[k]}"
    return ""

def main():
    only = [a.upper() for a in sys.argv[1:]]
    rows, seen = [], set()
    for seg, selectors in SEGMENTS.items():
        if only and not any(seg.upper().startswith(o) for o in only): continue
        print(f"[{seg}] querying {len(selectors)} selectors …", flush=True)
        els = overpass(selectors)
        n = 0
        for e in els:
            t = e.get("tags", {})
            name = tag(t, "name", "brand", "operator")
            if not name: continue
            pc = tag(t, "addr:postcode")
            key = (name.lower(), pc)
            if key in seen: continue
            seen.add(key)
            district = int(pc[1:3]) if re.fullmatch(r"1\d{2}0", pc) else ""
            lat = e.get("lat") or e.get("center", {}).get("lat", "")
            lon = e.get("lon") or e.get("center", {}).get("lon", "")
            rows.append({
                "pid": "", "segment": seg, "category": category_of(t), "name": name,
                "website": norm_url(tag(t, "website", "contact:website", "url")),
                "email": tag(t, "email", "contact:email"),
                "phone": tag(t, "phone", "contact:phone", "contact:mobile"),
                "street": (tag(t, "addr:street") + " " + tag(t, "addr:housenumber")).strip(),
                "postcode": pc, "district": district,
                "instagram": tag(t, "contact:instagram"), "facebook": tag(t, "contact:facebook"),
                "lat": lat, "lon": lon, "osm": f"{e['type']}/{e['id']}", "source": "osm",
            })
            n += 1
        print(f"  {n} named businesses ({sum(1 for r in rows if r['segment']==seg and r['website'])} with website)", flush=True)
        time.sleep(5)
    rows.sort(key=lambda r: (r["segment"], r["district"] or 99, r["name"].lower()))
    # stable ids from the OSM object (survive re-harvests, so audits/CRM columns stay attached)
    for r in rows: r["pid"] = "P" + r["osm"][0] + r["osm"].split("/")[1]
    out = DATA / "prospects.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows → {out}")

if __name__ == "__main__":
    main()
