#!/usr/bin/env python3
"""leads_index.py — data/LEADS.md: every link and file for the five leads, from lead.json + folder contents."""
import json, pathlib, time, re
ROOT = pathlib.Path(__file__).resolve().parent.parent; LEADS = ROOT / "data" / "leads"
order = ["lukanec", "kuhn", "roy-real", "novotny", "wiesinger"]
lh = (LEADS / "_lh" / "SUMMARY.md").read_text(encoding="utf-8") if (LEADS / "_lh" / "SUMMARY.md").exists() else ""
out = [f"# Die fünf Leads — alle Links, Belege, Dossiers und Pitches\n\n_Stand {time.strftime('%Y-%m-%d')} · erzeugt von `tools/leads_index.py` · Reihenfolge = Kontaktreihenfolge aus `PITCH-5.md`. Alles hier bleibt außerhalb von git (Daten Dritter)._\n",
       "| # | Betrieb | Website | Dossier | Pitch (HTML) | Angebot | Hauptbefund |\n|---|---|---|---|---|---|---|"]
details = []
for i, s in enumerate(order, 1):
    f = LEADS / s / "lead.json"
    if not f.exists(): out.append(f"| {i} | {s} | — | (läuft) | — | — | — |"); continue
    L = json.load(open(f, encoding="utf-8")); c = L["contact"]
    out.append(f"| {i} | **{L['name']}** · {L['district']} | [{re.sub(r'^https?://(www\.)?','',L['website']).rstrip('/')}]({L['website']}) | [DOSSIER.md](leads/{s}/DOSSIER.md) | [pitch.html](leads/{s}/pitch.html) | {L['offer']['lead']} {L['offer']['lead_price']} → {L['offer'].get('second','')} | {L['findings'][0]['title']} |")
    shots = sorted(p.name for p in (LEADS / s / "shots").glob("*.png"))
    comps = "\n".join(f"  - {x['name']} ({x.get('district','')}) — [{re.sub(r'^https?://(www\.)?','',x.get('website','')).rstrip('/')}]({x.get('website','')}) · `{x.get('shot','')}` — {x['what_their_site_does']}" for x in L["competitors"])
    srcs = (LEADS / s / "sources.md").read_text(encoding="utf-8").count("http")
    pre = "\n".join(f"  {k+1}. {p}" for k, p in enumerate(L["pre_outreach"]))
    oq = "\n".join(f"  - {q}" for q in L["open_questions"])
    details.append(f"""## {i}. {L['name']} — {L['category_label']}, {L['district']}
- **Website:** {L['website']} · Impressum: `leads/{s}/shots/impressum.png`
- **Ansprechperson:** {c.get('person','')} ({c.get('role','')}) · {c.get('address','')} · {c.get('phone','')} · {c.get('email','') or '—'}
- **Aufhänger:** {L['one_liner']}
- **Dateien:** [DOSSIER.md](leads/{s}/DOSSIER.md) · [lead.json](leads/{s}/lead.json) · [sources.md](leads/{s}/sources.md) ({srcs} Links) · [pitch.html](leads/{s}/pitch.html) · Review-Captures `leads/{s}/review/` · Lighthouse `leads/_lh/{s}-mobile.json`
- **Screenshots ({len(shots)}):** {' · '.join(f'`{n}`' for n in shots)}
- **Befunde:** {' · '.join(f"{x['id']} {x['title']} ({x['severity']})" for x in L['findings'])}
- **Wettbewerb (live geprüft):**
{comps}
- **Angebot:** {L['offer']['lead']} {L['offer']['lead_price']}, {L['offer']['lead_duration']} → {L['offer'].get('second','')} · realistisch {L['offer'].get('realistic_total','')}
- **Was David vor dem Kontakt tut:**
{pre}
- **Offen (°):**
{oq}
""")
out.append("\n" + "\n".join(details))
out.append("## Lighthouse (alle fünf)\n\n" + lh.split("\n", 3)[-1] if lh else "")
out.append("\n## Werkzeuge\n`tools/lead_shots.py` (Screenshots + Messwerte) · `tools/pitch.py --lead <slug>` (Deck aus lead.json) · `tools/verify_pitch.py` (Assertions + Captures) · `tools/leads_index.py` (diese Datei). Vertrag für die Dossiers: `leads/CONTRACT.md`.\n")
(ROOT / "data" / "LEADS.md").write_text("\n".join(out), encoding="utf-8"); print("data/LEADS.md written")
