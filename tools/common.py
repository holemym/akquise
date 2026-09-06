"""shared bits for befund_pages.py and letters.py — offer texts (DE), slugs, selection, config"""
import csv, json, pathlib, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1251 here; our prints use → and umlauts
except Exception: pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CFG = json.load(open(ROOT / "config.json", encoding="utf-8"))

# id → (name, one-sentence content, price range, duration)  — must match OFFERS.md v1
OFFERS = {
    "A1": ("Website Start", "eine eigene Website mit ein bis fünf Seiten: Konzept, Struktur, Design, mobil, Kontakt/Buchung, Impressum, Google-Unternehmensprofil, auf Ihrer eigenen Domain", "1.490 – 2.900 €", "2–3 Wochen"),
    "A2": ("Relaunch", "die bestehende Website neu gebaut: Struktur, Design, Inhalte übernommen, mobil, schnell, SEO-Basis, Messung", "2.900 – 5.900 €", "3–5 Wochen"),
    "A3": ("Sichtbarkeit", "technischer SEO-Durchgang, lokale Einträge, Schema und drei Kernseiten neu getextet – danach optional monatliche Fachbeiträge", "690 – 1.290 €", "2 Wochen"),
    "A4": ("Anfrage & Buchung", "Online-Terminbuchung bzw. Reservierung, Anfrageformular mit Auto-Antwort, WhatsApp-/Telefon-Tippziele und Messung der Anfragen", "590 – 1.190 €", "1–2 Wochen"),
    "A5": ("Mehrsprachig", "eine englische Version Ihrer Website, sauber verlinkt, mit Sprachumschalter und englischem Google-Profil", "690 – 1.490 €", "1–2 Wochen"),
    "B1": ("Digital-Betrieb", "monatliche Betreuung: Updates, Aktuelles, Newsletter, kleine Designstücke, eine Auswertung, ein Gespräch", "290 – 890 € pro Monat", "laufend, 3 Monate Mindestlaufzeit"),
    "C1": ("Workflow-Workshop", "ein halber Tag bei Ihnen: wer tippt was in welche Tabelle, welche drei Schritte wiederholen sich – und ein schriftlicher Vorschlag, was davon ein Tool übernehmen kann", "490 €", "1 Woche"),
}
UMLAUT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue", "é": "e", "è": "e", "á": "a", "č": "c", "š": "s", "ž": "z"})

def slug(row):
    s = row["name"].translate(UMLAUT).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48]
    return f"{s}-{row['pid'][-4:].lower()}"

def load_scored():
    return list(csv.DictReader(open(DATA / "prospects_scored.csv", encoding="utf-8")))

def select(rows, top=40, segments=(), districts=(), min_score=3, pids=()):
    if pids:
        return [r for r in rows if r["pid"] in set(pids)]
    per, out = {}, []
    for r in rows:
        if r["offer"] == "X0" or int(r["score"]) < min_score: continue
        if r.get("status", "neu") in ("nicht-kontaktieren", "verloren", "gewonnen"): continue
        if segments and not any(r["segment"].upper().startswith(s.upper()) for s in segments): continue
        if districts and (not r["district"] or int(r["district"]) not in districts): continue
        if per.get(r["segment"], 0) >= top: continue
        per[r["segment"]] = per.get(r["segment"], 0) + 1; out.append(r)
    return out

def befunde(row, n=3):
    lines = [l.strip() for l in row["befund"].split(" // ") if l.strip()]
    return lines[:n]

def domain(row):
    u = row.get("final_url") or row["website"]
    return re.sub(r"^https?://(www\.)?", "", u).rstrip("/") if u else ""

def parse_districts(s):
    out = set()
    for part in (s or "").split(","):
        part = part.strip()
        if not part: continue
        if "-" in part:
            a, b = part.split("-"); out.update(range(int(a), int(b) + 1))
        else: out.add(int(part))
    return out
