> 🇩🇪 Deutsch · 🇬🇧 [English](PIPELINE.md) · Zwillingsdatei — beide Sprachen werden immer gemeinsam geändert

# Pipeline — wie die Kontaktliste gebaut, geprüft und bewertet wird

## 0. Starten
```bash
cd C:/Users/User/Downloads/clauderoom/akquise
python tools/harvest_osm.py            # → data/prospects.csv        (alle 7 Segmente, ~10 Min.)
python tools/audit_site.py             # → data/audits.jsonl         (fortsetzbar; ~1.000 Seiten / 10 Min. bei 24 Workern)
python tools/score.py --top 40         # → data/prospects_scored.csv, data/SHORTLIST.md, data/STATS.md
```
Optionen: `harvest_osm.py S1 S4` (Segment-Präfixe) · `audit_site.py --segment S1 --limit 200 --workers 16`.
Braucht: Python 3.13, `requests`, `beautifulsoup4`, `lxml` (installiert). Playwright ist für die Screenshots (T2-6) installiert.

## 1. Quellen
| Quelle | Status | Anmerkungen |
|---|---|---|
| **OpenStreetMap / Overpass** | ✅ im Einsatz | Kostenlos, ODbL, kein Key. Wiener Abdeckung gut für Restaurants/Cafés/Ärzte, dünner für Büros. Website/Telefon/E-Mail/Adresse bei ~30–65 % je nach Kategorie. Abfrage auf `area["name"="Wien"]["admin_level"="4"]` eingegrenzt |
| **WKO Firmen A-Z** (firmen.wko.at) | ⏳ T2-5 | Offizielles Verzeichnis von 626k Firmen, durchsuchbar nach Branche × Bezirk; listet Website/Telefon. Nutzungsbedingungen vor automatisiertem Zugriff prüfen; ein manueller Export je Branche reicht für die Prioritätssegmente wahrscheinlich |
| **Herold.at** | ⏳ | Kommerzielles Verzeichnis; gut für Freiberufler; Scraping laut Bedingungen eingeschränkt — manuell zur Namensanreicherung nutzen |
| **Google Maps / Places API** | ⏳ T2-8 | Braucht API-Key (nach Gratiskontingent kostenpflichtig). Liefert Profilvollständigkeit, Bewertungen, Fotos — starkes Befund-Material („Ihr Google-Profil hat 2 Fotos und keine Öffnungszeiten“) |
| **LinkedIn** | manuell | Entscheider-Namen für S1/S4 |
| **Netzwerke bestehender Kunden** | manuell | Loutati, WOW, Ani Poel, Englibee nach Namen fragen |

## 2. Datenschema
`data/prospects.csv` (Ernte): `pid, segment, category, name, website, email, phone, street, postcode, district, instagram, facebook, lat, lon, osm, source`

`data/audits.jsonl` (ein JSON je Seite): status, final_url, response_ms, html_bytes, https, title, meta_desc_len, viewport, lang, hreflangs, has_en, generator, builders[], jquery, bootstrap, copyright_year, newest_date_year, h1_count, img_count, img_no_alt, word_count, contact_form, booking, tracking, cookie_banner, mailto[], tel[], socials[], blog, mixed_content, favicon, google_fonts, under_construction, placeholder_text, og_image, schema_org, tables, impressum_url, impressum_snippet, names[], roles[], impressum_emails[]

`data/prospects_scored.csv` (CRM): Ernte-Spalten + `score, offer, offer_label, tags, befund, builder, latest_year, names, roles, emails_found, impressum_url, final_url` + **von der Hilfskraft gepflegt** `status, kanal, kontaktiert_am, antwort, notiz`.

`score.py` bewertet alles neu, **behält aber die fünf Hilfskraft-Spalten** aus der vorherigen `prospects_scored.csv` per `pid` — die Hilfskraft kann die Datei direkt bearbeiten. `tools/shots.py` macht die Handy-Screenshots (`data/shots/<pid>.png`) für die Shortlist.

## 3. Bewertung (siehe `tools/score.py`)
| Tag | Punkte | Befund-Zeile (DE) |
|---|---|---|
| NO_SITE | 7 | ohne Website gelistet |
| SITE_DOWN | 8 | Seite nicht erreichbar |
| UNFINISHED | 5 | im Aufbau / Lorem ipsum |
| NOT_MOBILE | 4 | kein Viewport-Meta |
| NO_HTTPS | 3 | |
| STALE | 2–3 | neuestes sichtbares Datum ≤ 2023 |
| BUILDER | 2 | Wix/Jimdo/IONOS/… |
| SEO_BASICS | 2 | leerer Titel (starke Zeile) oder fehlende Beschreibung (weichere Zeile) |
| SLOW | 2 | > 3,5 s erste Antwort oder > 2,5 MB HTML |
| OLD_TECH | 2 | jQuery 1.x, Bootstrap 3, Frames, Tabellenlayout |
| NO_BOOKING | 2 | S2/S3/S6 ohne Buchung |
| NO_CONTACT | 2 | kein Formular und kein mailto |
| NO_ANALYTICS · NO_EN · NO_CONTENT · NO_ALT · THIN · NO_H1 · NO_FORM · MIXED | 1 | NO_ANALYTICS, NO_CONTACT und THIN sind **nur Tags** (keine gedruckte Zeile): zu schwach oder bei JS-Seiten zu oft falsch |
| BLOCKED | 0 | HTTP 401/403/429/503/530 oder Timeouts = Bot-Schutz / langsamer Host, kein Befund — menschliche Prüfung |

Angebotszuordnung in [OFFERS.de.md](OFFERS.de.md) §„Zuordnung“. Score ≥ 3 mit klarem strukturellem Befund → Brief. Score < 3 → überspringen (wir schreiben niemandem, der uns nicht braucht).

## 4. Bekannte Grenzen des automatischen Audits (warum die menschliche Prüfung existiert)
- Kein JavaScript-Rendering: eine React-/Wix-Seite kann „dünn“ oder „ohne Formular“ wirken, obwohl sie es nicht ist. Wix/Webflow/Framer-Erkennung ist zuverlässig, Inhaltsprüfungen weniger.
- `newest_date_year` liest jedes Datum auf der Seite (Öffnungszeiten zählen nicht, aber „© 2019“ und News-Daten schon). Ein veraltetes Copyright auf einer gepflegten Seite ist trotzdem eine gültige Beobachtung, aber so formulieren.
- `has_en` ist heuristisch. Sprachumschalter von Hand prüfen.
- `names` aus dem Impressum fängt Namen mit akademischem Titel (Mag., Dr., DI); Namen ohne Titel werden übersehen — `impressum_snippet` lesen.
- Buchungserkennung ist schlagwortbasiert; eine Nur-Telefon-Praxis mit „Termin nach Vereinbarung“ ist korrekt NO_BOOKING.
- Antwortzeit ist aus Wien über eine Heimleitung gemessen; SLOW als Indikator behandeln, vor dem Druck einer Zahl mit PageSpeed prüfen.

## 5. Checkliste manuelle Qualifikation (Hilfskraft, je Betrieb, ~3 Minuten)
1. Seite am Handy öffnen. Halten die Befund-Zeilen? Wenn nicht, `befund` anpassen.
2. Lebt der Betrieb (Google: geöffnet, aktuelle Bewertungen)? Wenn geschlossen → `status = nicht-kontaktieren`.
3. Entscheider: Impressum → LinkedIn → WKO. „Name, Funktion“ in `names`.
4. Postadresse bestätigt (Impressum schlägt OSM).
5. Auffälligkeiten (Kette, Franchise, Teil einer größeren Gruppe, bereits Kunde einer bekannten Agentur) → `notiz`.
6. `status = geprüft`.

## 6. Nächste Pipeline-Schritte
- T2-5 zweite Quelle zusammenführen · T2-6 Handy-Screenshots · T4-1 Befund-Seiten · merge-sichere CRM (§2-Hinweis).
