# data/ — not in this repository

This folder holds the prospect list, the audit results and the CRM. **None of it is committed**, because this repository is public and the files contain contact details and Impressum names of real Vienna businesses and the people who run them.

| File | What | Where to get it |
|---|---|---|
| `prospects.csv` | Harvested businesses | `python tools/harvest_osm.py` |
| `audits.jsonl` | Raw site-audit facts | `python tools/audit_site.py` |
| `prospects_scored.csv` | The CRM: findings, offer, status columns | `python tools/score.py` |
| `SHORTLIST.md` · `STATS.md` | Working list and pipeline numbers | `python tools/score.py` |
| `shots/` | Phone screenshots | `python tools/shots.py` |
| `letters/` · `befund_urls.csv` | Letters, PDFs, per-prospect page URLs | `python tools/letters.py`, `tools/befund_pages.py` |

**Outreach person:** David sends you the current `prospects_scored.csv`, `SHORTLIST.md` and the letter batch directly. Put them in this folder and Obsidian will pick them up. Do not commit them and do not forward them.

Everything here can be rebuilt from scratch with the tools; see [../PIPELINE.md](../PIPELINE.md).
