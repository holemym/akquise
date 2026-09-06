> 🇬🇧 English · 🇩🇪 [Deutsch](README.de.md) · twin file — both languages are always changed together

# AKQUISE — Vienna outreach vault

The operations brain for finding Viennese businesses that need David's design services, diagnosing their concrete digital problems, and sending them specific offers. It is an **Obsidian vault**: plain Markdown, no plugins required.

⚠️ **The method is public, the data is not.** This repository holds the playbook, the handbook and the tooling. It deliberately contains **no prospect data**: contact details and Impressum names of real businesses stay out of git and are shared directly with whoever does the outreach. See [data/README.md](data/README.md) and [STRATEGY.md](STRATEGY.md) §8.

## Open it in Obsidian
1. Clone or download this repository.
2. Obsidian → **Open folder as vault** → pick this folder.
3. Start at [HUB.md](HUB.md) (German: [HUB.de.md](HUB.de.md)). Pin it as your home tab.

Shared settings live in `.obsidian/` so everyone sees the same appearance; your own pane layout stays local.

## Read in this order
| # | English | Deutsch | What it is |
|---|---|---|---|
| 1 | [HUB.md](HUB.md) | [HUB.de.md](HUB.de.md) | Home: status, decisions, tasks, session log |
| 2 | [STRATEGY.md](STRATEGY.md) | [STRATEGY.de.md](STRATEGY.de.md) | Segments, the Befund method, channels + Austrian law, funnel, KPIs |
| 3 | [OFFERS.md](OFFERS.md) | [OFFERS.de.md](OFFERS.de.md) | Service map: packages, prices, conditions |
| 4 | [HANDBUCH.en.md](HANDBUCH.en.md) | [HANDBUCH.md](HANDBUCH.md) | **Handbook for the outreach person** — start here if that is you |
| 5 | [PIPELINE.md](PIPELINE.md) | [PIPELINE.de.md](PIPELINE.de.md) | How the prospect list is harvested, audited and scored |
| 6 | [INBOX.md](INBOX.md) | [INBOX.de.md](INBOX.de.md) | Scratch: anything you want David or Claude to pick up |

`templates/` holds the letter, the LinkedIn note, the phone guide and the proposal skeleton. German is the version that gets sent.

## The twin rule
Every document exists twice: `X.md` (EN) ↔ `X.de.md` (DE). German-native files (HANDBUCH, templates) have `X.en.md` twins. Same headings, same checkboxes, same numbers, same links — only the language differs. **Whoever changes one file changes the twin in the same session.**

```bash
python tools/sync_check.py    # fails if any pair drifts
```

## What is in `data/`
Only two files are committed:

| File | What |
|---|---|
| `data/STATS.md` | Pipeline numbers per segment, offer distribution, tag frequency — aggregates only, no personal data |
| `data/README.md` | What the uncommitted files are and how to rebuild them |

**Not committed** (see `.gitignore`): the prospect list, the CRM, the shortlist, screenshots, generated letters and Befund pages, the raw audit dump and the Overpass cache. Everything is rebuildable with the tools; David shares the current batch with the outreach person directly.

## Running the pipeline (David)
```bash
python tools/harvest_osm.py                                        # OpenStreetMap → data/prospects.csv
python tools/audit_site.py --workers 24                            # → data/audits.jsonl (resumable)
python tools/score.py --top 40                                     # → scored CSV, SHORTLIST.md, STATS.md
python tools/shots.py --segments S1,S4 --districts 1-9,18,19       # → data/shots/<pid>.png
python tools/befund_pages.py --segments S1,S4 --districts 1-9,18,19 # → site/b/*.html
python tools/letters.py --segments S1,S4 --districts 1-9,18,19 --pdf # → data/letters/*.pdf + BATCH.md
```
Needs Python 3.13 with `requests`, `beautifulsoup4`, `lxml`, `segno`, `playwright`. Sender details, booking link and references live in `config.json`.

## Conventions
Plain Markdown only — no Dataview or plugin-only syntax, because these files are read raw as often as they are read in Obsidian. Tasks are `- [ ]` checkboxes with ids (`T2-4`). Every session ends by ticking boxes, adding one session-log line in the hub, and running the sync check.
