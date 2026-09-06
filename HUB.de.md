> 🇩🇪 Deutsch · 🇬🇧 [English](HUB.md) · Zwillingsdatei — beide Sprachen werden immer gemeinsam geändert (`python tools/sync_check.py` prüft das)

# AKQUISE — Wien-Outreach-Hub

Operatives Gehirn, um Wiener Betriebe zu finden, die Davids Leistungen brauchen, ihren konkreten digitalen Schmerz zu diagnostizieren und ihnen spezifische Angebote zu schicken. Diesen Ordner als Obsidian-Vault öffnen; diese Notiz ist die Startseite. Claude arbeitet direkt in diesen Dateien (hakt Aufgaben ab, führt das Session-Log). Konventionen wie in [../BOARD.md](../BOARD.md).

**Verantwortlich:** David (Design, Angebote, Umsetzung) · **Outreach:** deutschsprachige Hilfskraft (Name folgt) · **Studio-Identität:** d-vision.design (bestätigen)
**Angelegt:** 2026-09-02 · **Status:** 🟢 Entscheidungen getroffen, Pipeline läuft durchgehend (Ernte → Audit → Score → Screenshots → Befund-Seiten → Briefe); Batch 1 wartet auf `config.json` (Adresse, Buchungslink, Name der Hilfskraft)

## Repo (wie die Outreach-Person an dieses Vault kommt)
Öffentliches GitHub-Repo: **https://github.com/holemym/akquise** (Branch `main`). Klonen oder herunterladen, dann Obsidian → *Ordner als Vault öffnen*. Einrichtung und Zwillingsregel stehen in [README.de.md](README.de.md).

**Die Methode ist öffentlich, die Daten sind es nicht.** Keine Kontaktdaten liegen in git — weder CRM noch Shortlist, Briefe, Screenshots oder Audit-Dump. David schickt die aktuelle Serie direkt an die Outreach-Person; siehe [data/README.md](data/README.md).

- [ ] T5-0 Der Outreach-Person die aktuelle `prospects_scored.csv`, `SHORTLIST.md` und die Briefserie schicken (das Repo selbst ist öffentlich und enthält keine Daten)

## In dieser Reihenfolge lesen
1. [STRATEGY.de.md](STRATEGY.de.md) — These, Segmente, die Befund-Methode, Kanäle + Recht, Funnel, Kennzahlen
2. [OFFERS.de.md](OFFERS.de.md) — Leistungslandkarte mit Paketen, v1-Preisen, Bedingungen
3. [HANDBUCH.md](HANDBUCH.md) — internes Handbuch für die Outreach-Person (die ganze Landkarte, wie wir Angebote mögen, Regeln)
4. [TIERING.de.md](TIERING.de.md) — **welche Leads einen Brief wert sind**: Prüfmethode, was sie gefunden hat, Tiers A–X und das Vorgehen je Tier
5. [PIPELINE.de.md](PIPELINE.de.md) — wie Scraping/Audit/Scoring funktionieren und wie man sie startet
6. `templates/` — Befund-Brief, LinkedIn-Notiz, Telefon-Leitfaden, Angebots-Skelett (DE, mit EN-Zwillingen)
7. `data/` — `prospects.csv` (roh) · `audits.jsonl` (Fakten) · `prospects_scored.csv` (Befunde + Angebot + CRM-Spalten) · `TIERS.md` (die Arbeitsliste, A→X) · `SHORTLIST.md` · `STATS.md`

## Zwillingsregel (EN ↔ DE)
Jedes Dokument existiert zweimal: `X.md` (EN) ↔ `X.de.md` (DE); deutschsprachige Originale (HANDBUCH, Vorlagen) haben `X.en.md`-Zwillinge. Gleiche Überschriften, gleiche Checkboxen, gleiche Zahlen, gleiche Links — nur die Sprache unterscheidet sich. **Wer eine Datei ändert, ändert den Zwilling in derselben Session.** `python tools/sync_check.py` vergleicht Struktur, abgehakte Aufgaben, Geld/Daten und Links und schlägt bei Abweichung fehl; vor dem Schließen einer Session ausführen. `data/` wird nicht dupliziert (Befund-Zeilen sind absichtlich deutsch; STATS/SHORTLIST werden generiert).

## Entscheidungen (David hat D1–D7 am 2026-09-02 an Claude delegiert; jede Zeile kann durch Bearbeiten überstimmt werden)
- [x] D1 **Preise als v1 gesperrt** (2026-09-02) — die Zahlen in [OFFERS.de.md](OFFERS.de.md) gelten. Überprüfung nach 10 Angeboten oder 3 Abschlüssen. Im Brief nie unter einer Spanne anbieten; David darf im schriftlichen Angebot darüber gehen.
- [x] D2 **Kanäle = Brief + Vorbeigehen + einzelne LinkedIn-Notizen.** Keine Kalt-E-Mails, keine Kaltanrufe, und **auch keine Kontaktformular-Nachrichten** (das rechtliche Risiko trifft genau das Reputationssegment, das wir am meisten wollen). E-Mail/Telefon erst nach einer Antwort, Einwilligung mit Datum protokolliert.
- [x] D3 **Person zuerst, Studio als Zweites.** Briefe sind mit „David Mora, Product & Digital Designer“ unterschrieben, Studio-Zeile „d-vision“. Absenderadresse = die Impressum-Adresse des Studios (in `config.json` eintragen). ⚠ d-vision.design löst heute nicht auf, daher tragen die Briefe die Befund-Seiten-URL auf Vercel + Davids Telefon, bis die Domain live ist.
- [x] D4 **Batch 1 = S1 Beratung + S4 Immobilien in den Bezirken 1–9, 18, 19.** Batch 2 = S2 Gesundheit, dieselben Bezirke. S3/S6 erst, wenn der Brief eine gemessene Antwortquote hat.
- [x] D5 **Rollenprofil Hilfskraft:** 8 h/Woche, Start sobald das Batch-1-Material existiert; Bezahlung = Stundensatz + 10 % der Erstprojekt-Rechnung bei gewonnenen Aufträgen. Name noch offen → in INBOX und `config.json` eintragen.
- [x] D6 **Dieselbe rechnungslegende Einheit wie bei Loutati** (Veronika Didorenko, Kleinunternehmer, 0 % USt), bis die 12-Monats-Prognose die österreichische Kleinunternehmergrenze überschreitet (55.000 € netto, Regel 2025); dann vor dem nächsten Angebot zur USt registrieren. Das Kennzahlen-Blatt führt die laufende Summe.
- [x] D7 **Befund-Seiten = statisches Vercel-Projekt** `befund` (noindex, `/b/<slug>`), erzeugt von `tools/befund_pages.py`; Alias auf d-vision.design/befund, sobald die Domain registriert und gepointet ist.

## Tracks & Aufgaben

### T1 Strategie & Angebote
- [x] T1-1 Strategiedokument (Segmente, Befund-Methode, Recht, Funnel, Kennzahlen) — 2026-09-02
- [x] T1-2 Leistungskatalog mit Entwurfspreisen + Bedingungen — 2026-09-02
- [x] T1-3 Preise/Bedingungen als v1 gesperrt (D1, delegiert) — OFFERS am 2026-09-02 als GESPERRT markiert
- [ ] T1-4 Einseitiges „Warum wir“-Beweisblatt (Loutati, WOW, JewishServices, interne Tools; Screenshots) zum Beilegen

### T2 Pipeline & Daten
- [x] T2-1 `tools/harvest_osm.py` — OSM-Overpass-Ernte, 7 Segmente, Dubletten, Bezirk — 2026-09-02
- [x] T2-2 `tools/audit_site.py` — objektive Website-Fakten + Entscheider-Hinweise aus dem Impressum — 2026-09-02
- [x] T2-3 `tools/score.py` — Befunde (DE), Score, Angebotszuordnung, SHORTLIST + STATS — 2026-09-02
- [x] T2-4 Pilotlauf über alle Segmente — 2026-09-02: 9.016 geerntet, 4.334 Seiten geprüft (17 Min.), STATS.md geschrieben; 14 Batch-1-Befunde gesichtet → 3 schwache Zeilentypen auf Tag-only zurückgestuft, 403/429 als BLOCKED umklassifiziert, Impressum-Namen bereinigt
- [ ] T2-5 Zweite Quelle für die Prioritätssegmente (WKO Firmen A-Z oder Herold), zusammenführen über Name+PLZ
- [x] T2-6 Handy-Screenshot je Shortlist-Seite (`tools/shots.py`, 390 px) → `data/shots/<pid>.png` — Batch 1 am 2026-09-02 fotografiert
- [x] T2-9 `tools/validate.py` — Live-Prüfung auf Lebenszeichen/Eignung/Schmerz, Tiers A–X, Suche nach übersehenen Websites → `data/validated.csv` + `data/TIERS.md`, ausgewertet in [TIERING.de.md](TIERING.de.md) — 2026-09-06
- [ ] T2-7 Manuelle Qualifikation durch die Hilfskraft — jetzt konkret: **Tier C abarbeiten** (52 Prospects, ~1 Std.; 33 brauchen einen Entscheidernamen, 14 eine Google-Prüfung, 3 haben doch eine Website, 2 brauchen die aktuelle Domain). Erwartung: 20–25 Aufstufungen nach B. Checkliste in PIPELINE §5, Anweisungen je Prospect in `data/TIERS.md`
- [ ] T2-8 Google-Unternehmensprofil prüfen (Profil? Fotos? Bewertungen? Öffnungszeiten?) — ins Audit, sobald ein Places-Key existiert

### T3 Dokumente für den Outreach
- [x] T3-1 HANDBUCH.md (DE) — Leistungslandkarte, Beschreibungen, Bedingungen, wie wir Angebote mögen, Regeln, Ablauf — 2026-09-02
- [x] T3-2 Vorlagen: Befund-Brief, LinkedIn-Notiz, Telefon-Leitfaden, Angebots-Skelett — 2026-09-02
- [x] T3-3 Druckfertiges Befund-Brief-Layout (`tools/letters.py`: A4 HTML/PDF, QR, Screenshot-Feld, BATCH.md-Checkliste — gebaut 2026-09-02; braucht Adresse + Buchungslink in `config.json`)
- [ ] T3-4 Angebotsvorlage als gestaltetes HTML/PDF (Struktur von loutati-redesign/pitch.html wiederverwenden)
- [ ] T3-5 Einwand-Blatt wächst mit echten Antworten (Hilfskraft loggt sie in INBOX)
- [ ] T3-6 Beweis-Sätze je Kategorie (Architekten/Notare in S1 bekommen derzeit die Steuerberater-Referenz) — `config.json`-Referenzen nach OSM-Kategorie erweitern

### T4 Personalisierte Assets (die „einzigartige“ Schicht)
- [x] T4-1 Befund-Seiten-Generator (`tools/befund_pages.py`, gebaut + für Batch 1 am 2026-09-02 ausgeführt, 67 Seiten in `site/b/`): `data/prospects_scored.csv` → eine statische Seite je Shortlist-Betrieb (Befunde + Handy-Screenshot + Angebot + Buchungslink)
- [ ] T4-2 Schnelle Startseiten-Neuskizze je Top-20-Betrieb (Foundry-Kit + deren Inhalte, 20 Min. je Stück) als Vorher/Nachher auf der Seite
- [ ] T4-3 Unter der Studio-Domain veröffentlichen, noindex, kurze QR-URLs

### T5 Outreach-Betrieb
- [x] T5-1 CRM = Spalten `status/kanal/kontaktiert_am/antwort/notiz` in `prospects_scored.csv` (Hilfskraft pflegt; Claude bewertet neu, ohne sie zu überschreiben) — merge-sicher seit 2026-09-02
- [ ] T5-2 Batch 1: 50 Briefe, S1+S4 innere Bezirke — nach D1–D4
- [ ] T5-3 Wöchentliches Review-Ritual: Antworten → Angebote innerhalb 48 h → ins Session-Log
- [ ] T5-4 Kennzahlen-Blatt (gesendet / geantwortet / Gespräche / Angebote / gewonnen) je Batch und Segment

## Session-Log
- 2026-09-06 — **Lead-Prüfung ([TIERING.de.md](TIERING.de.md)).** Alle 120 Batch-1-Kandidaten live nachgeprüft → A 5 · B 28 · C 52 · D 26 · X 9. Gefunden: 3 Leads fälschlich aussortiert, weil die Schließungserkennung *Insolvenz*/*Liquidation* (Leistungen von Anwälten) als Todesanzeige las; 3 „keine Website“-Briefe, die falsch gewesen wären (allmermacke.at, naske.at, rpck.com); 9 Institutionen/Konzerne/Franchises; 26 gesunde Büros aus der Serie genommen. Die ehrlich druckbare Serie ist jetzt **22 Briefe**, nicht 67. Tier As „kein mobiles Layout“ auf den echten Seiten bestätigt.
- 2026-09-03 — Repo **als `holemym/akquise`** öffentlich gemacht, ohne Daten: die 5 Dateien mit Kontaktdaten wurden aus der Versionierung genommen und die Historie auf einen Commit zurückgesetzt. Das alte `akquise-vault` ließ sich nicht sicher umstellen (seine Commits vor dem Rewrite blieben trotz Force-Push per SHA abrufbar), daher wurde es wieder auf privat gesetzt und ein sauberes Repo angelegt. ⚠ David: `akquise-vault` in den GitHub-Einstellungen löschen (das API-Token hat keine Delete-Berechtigung).
- 2026-09-02 (nachts) — Vault als privates GitHub-Repo `holemym/akquise-vault` veröffentlicht (45 Dateien, EN/DE-Zwillinge + Tools + Shortlist/CRM). README-Zwillinge mit der Obsidian-Einrichtung ergänzt. Erzeugte Artefakte über `.gitignore` ausgeschlossen. Offen: Outreach-Person als Mitarbeiter einladen.
- 2026-09-02 (abends) — Entscheidungen D1–D7 getroffen (delegiert). Pipeline komplett durchgelaufen; Qualitätsdurchgang der Befunde; Batch-1-Material erzeugt: `data/SHORTLIST.md`, `site/b/*.html` (Befund-Seiten), `data/letters/*.pdf` + `BATCH.md`. Offen vor dem Druck: ⚠-Felder in `config.json`, Handprüfung durch die Hilfskraft, Vercel-Deploy von `site/`.
- 2026-09-02 (später) — Vault zweisprachig gemacht: jedes Dokument hat einen EN/DE-Zwilling, `tools/sync_check.py` besteht 10/10. Ernte mit der Area-ID-Abfrage neu gestartet (Overpass-Spiegel liefen bei der Namenssuche in Timeouts); der abgekoppelte Runner `tools/run_all.py` prüft + bewertet, sobald das CSV da ist.
- 2026-09-02 — Projekt angelegt: Strategie, Angebote (Entwurf), Handbuch (DE), Pipeline-Tools, Vorlagen. OSM-Ernte + Audit für alle 7 Segmente gestartet. Rechtsprüfung: § 174 TKG 2021 verbietet unerbetene B2B-E-Mails/Anrufe in Österreich → Brief-zuerst-Strategie.
