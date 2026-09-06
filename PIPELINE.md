> 🇬🇧 English · 🇩🇪 [Deutsch](PIPELINE.de.md) · twin file — both languages are always changed together

# Pipeline — how the prospect list is built, audited and scored

## 0. Run it
```bash
cd C:/Users/User/Downloads/clauderoom/akquise
python tools/harvest_osm.py            # → data/prospects.csv        (all 7 segments, ~10 min)
python tools/audit_site.py             # → data/audits.jsonl         (resumable; ~1,000 sites / 10 min at 24 workers)
python tools/score.py --top 40         # → data/prospects_scored.csv, data/SHORTLIST.md, data/STATS.md
```
Options: `harvest_osm.py S1 S4` (segment prefixes) · `audit_site.py --segment S1 --limit 200 --workers 16`.
Needs: Python 3.13, `requests`, `beautifulsoup4`, `lxml` (installed). Playwright is installed for T2-6 screenshots.

## 1. Sources
| Source | Status | Notes |
|---|---|---|
| **OpenStreetMap / Overpass** | ✅ in use | Free, ODbL, no key. Vienna coverage is good for restaurants/cafés/doctors, thinner for offices. Has website/phone/email/address for ~30–65 % depending on category. Query filtered to `area["name"="Wien"]["admin_level"="4"]` |
| **WKO Firmen A-Z** (firmen.wko.at) | ⏳ T2-5 | Official directory of 626k companies, searchable by Branche × Bezirk; lists website/phone. Check terms before automated access; a per-branch manual export may be enough for the priority segments |
| **Herold.at** | ⏳ | Commercial directory; good for professionals; scraping restricted by terms — use manually for name enrichment |
| **Google Maps / Places API** | ⏳ T2-8 | Needs an API key (paid after free tier). Gives profile completeness, reviews, photos — strong Befund material ("Ihr Google-Profil hat 2 Fotos und keine Öffnungszeiten") |
| **LinkedIn** | manual | Decision-maker names for S1/S4 |
| **Existing clients' networks** | manual | Ask Loutati, WOW, Ani Poel, Englibee for names |

## 2. Data schema
`data/prospects.csv` (harvest): `pid, segment, category, name, website, email, phone, street, postcode, district, instagram, facebook, lat, lon, osm, source`

`data/audits.jsonl` (one JSON per site): status, final_url, response_ms, html_bytes, https, title, meta_desc_len, viewport, lang, hreflangs, has_en, generator, builders[], jquery, bootstrap, copyright_year, newest_date_year, h1_count, img_count, img_no_alt, word_count, contact_form, booking, tracking, cookie_banner, mailto[], tel[], socials[], blog, mixed_content, favicon, google_fonts, under_construction, placeholder_text, og_image, schema_org, tables, impressum_url, impressum_snippet, names[], roles[], impressum_emails[]

`data/prospects_scored.csv` (CRM): harvest columns + `score, offer, offer_label, tags, befund, builder, latest_year, names, roles, emails_found, impressum_url, final_url` + **helper-owned** `status, kanal, kontaktiert_am, antwort, notiz`.

`score.py` re-scores everything but **keeps the five helper columns** from the previous `prospects_scored.csv` by `pid` — the helper can edit the file directly. `tools/shots.py` takes the phone screenshots (`data/shots/<pid>.png`) for the shortlist.

## 3. Scoring (see `tools/score.py`)
| Tag | Points | Befund line (DE) |
|---|---|---|
| NO_SITE | 7 | listed without website |
| SITE_DOWN | 8 | site unreachable |
| UNFINISHED | 5 | under construction / lorem ipsum |
| NOT_MOBILE | 4 | no viewport meta |
| NO_HTTPS | 3 | |
| STALE | 2–3 | newest visible date ≤ 2023 |
| BUILDER | 2 | Wix/Jimdo/IONOS/… |
| SEO_BASICS | 2 | empty title (strong line) or missing description (softer line) |
| SLOW | 2 | > 3.5 s first response or > 2.5 MB HTML |
| OLD_TECH | 2 | jQuery 1.x, Bootstrap 3, frames, table layout |
| NO_BOOKING | 2 | S2/S3/S6 without booking |
| NO_CONTACT | 2 | no form and no mailto |
| NO_ANALYTICS · NO_EN · NO_CONTENT · NO_ALT · THIN · NO_H1 · NO_FORM · MIXED | 1 | NO_ANALYTICS, NO_CONTACT and THIN are **tag-only** (no printed line): too weak or too often wrong on JS-rendered sites |
| BLOCKED | 0 | HTTP 401/403/429/503/530 or timeouts = bot protection / slow host, not a finding — human check |

Offer mapping is in [OFFERS.md](OFFERS.md) §"Mapping". Score ≥ 3 with a clear structural finding → letter. Score < 3 → skip (we don't write to people who don't need us).

## 4. Known limits of the automatic audit (why the human check exists)
- No JavaScript rendering: a React/Wix site can look "thin" or "no form" when it isn't. Wix/Webflow/Framer detections are reliable, content checks less so.
- `newest_date_year` reads any date on the page (opening hours don't count, but "© 2019" and news dates do). A stale copyright on a maintained site is still a valid observation, but say it as such.
- `has_en` is heuristic. Check the language switch by hand.
- `names` from the Impressum catch academic-title names (Mag., Dr., DI); plain names are missed — read the `impressum_snippet`.
- Booking detection is keyword-based; a phone-only practice that writes "Termin nach Vereinbarung" is correctly NO_BOOKING.
- Response time is measured from Vienna over a home line; treat SLOW as an indicator, verify with PageSpeed before printing a number.

## 5. Manual qualification checklist (helper, per prospect, ~3 minutes)
1. Open the site on a phone. Do the Befund lines hold? Edit `befund` if not.
2. Is the business alive (Google: open, recent reviews)? If closed → `status = nicht-kontaktieren`.
3. Decision-maker: Impressum → LinkedIn → WKO. Put "Name, Funktion" into `names`.
4. Postal address confirmed (Impressum beats OSM).
5. Anything unusual (chain, franchise, part of a bigger group, already a client of a known agency) → `notiz`.
6. `status = geprüft`.

## 6. Next pipeline steps
- T2-5 second source merge · T2-6 phone screenshots · T4-1 Befund pages · merge-safe CRM (§2 warning).
