> 🇩🇪 Deutsch · 🇬🇧 [English](README.md) · Zwillingsdatei — beide Sprachen werden immer gemeinsam geändert

# AKQUISE — Wien-Outreach-Vault

Das operative Gehirn, um Wiener Betriebe zu finden, die Davids Designleistungen brauchen, ihre konkreten digitalen Probleme zu diagnostizieren und ihnen spezifische Angebote zu schicken. Es ist ein **Obsidian-Vault**: reines Markdown, keine Plugins nötig.

⚠️ **Die Methode ist öffentlich, die Daten nicht.** Dieses Repository enthält das Vorgehen, das Handbuch und die Werkzeuge. Es enthält bewusst **keine Kontaktdaten**: Adressen und Impressum-Namen echter Betriebe bleiben außerhalb von git und werden direkt an die Outreach-Person weitergegeben. Siehe [data/README.md](data/README.md) und [STRATEGY.de.md](STRATEGY.de.md) §8.

## In Obsidian öffnen
1. Dieses Repository klonen oder herunterladen.
2. Obsidian → **Ordner als Vault öffnen** → diesen Ordner wählen.
3. Bei [HUB.de.md](HUB.de.md) beginnen (Englisch: [HUB.md](HUB.md)). Als Start-Tab anheften.

Gemeinsame Einstellungen liegen in `.obsidian/`, damit alle dasselbe Erscheinungsbild sehen; die eigene Fensteraufteilung bleibt lokal.

## In dieser Reihenfolge lesen
| # | Deutsch | English | Was es ist |
|---|---|---|---|
| 1 | [HUB.de.md](HUB.de.md) | [HUB.md](HUB.md) | Startseite: Status, Entscheidungen, Aufgaben, Session-Log |
| 2 | [STRATEGY.de.md](STRATEGY.de.md) | [STRATEGY.md](STRATEGY.md) | Segmente, die Befund-Methode, Kanäle + österreichisches Recht, Funnel, Kennzahlen |
| 3 | [OFFERS.de.md](OFFERS.de.md) | [OFFERS.md](OFFERS.md) | Leistungslandkarte: Pakete, Preise, Bedingungen |
| 4 | [HANDBUCH.md](HANDBUCH.md) | [HANDBUCH.en.md](HANDBUCH.en.md) | **Handbuch für die Outreach-Person** — hier anfangen, wenn du das bist |
| 5 | [PIPELINE.de.md](PIPELINE.de.md) | [PIPELINE.md](PIPELINE.md) | Wie die Kontaktliste geerntet, geprüft und bewertet wird |
| 6 | [INBOX.de.md](INBOX.de.md) | [INBOX.md](INBOX.md) | Notizblock: alles, was David oder Claude aufgreifen soll |

`templates/` enthält den Brief, die LinkedIn-Notiz, den Telefon-Leitfaden und das Angebots-Skelett. Verschickt wird immer die deutsche Fassung.

## Die Zwillingsregel
Jedes Dokument existiert zweimal: `X.md` (EN) ↔ `X.de.md` (DE). Deutschsprachige Originale (HANDBUCH, Vorlagen) haben `X.en.md`-Zwillinge. Gleiche Überschriften, gleiche Checkboxen, gleiche Zahlen, gleiche Links — nur die Sprache unterscheidet sich. **Wer eine Datei ändert, ändert den Zwilling in derselben Session.**

```bash
python tools/sync_check.py    # schlägt fehl, sobald ein Paar auseinanderläuft
```

## Was in `data/` liegt
Nur zwei Dateien sind eingecheckt:

| Datei | Was |
|---|---|
| `data/STATS.md` | Pipeline-Zahlen je Segment, Angebotsverteilung, Tag-Häufigkeit — nur Summen, keine personenbezogenen Daten |
| `data/README.md` | Was die nicht eingecheckten Dateien sind und wie man sie neu erzeugt |

**Nicht eingecheckt** (siehe `.gitignore`): die Kontaktliste, das CRM, die Shortlist, Screenshots, erzeugte Briefe und Befund-Seiten, der rohe Audit-Dump und der Overpass-Cache. Alles lässt sich mit den Tools neu erzeugen; David gibt die aktuelle Serie direkt an die Outreach-Person weiter.

## Pipeline starten (David)
```bash
python tools/harvest_osm.py                                        # OpenStreetMap → data/prospects.csv
python tools/audit_site.py --workers 24                            # → data/audits.jsonl (fortsetzbar)
python tools/score.py --top 40                                     # → bewertetes CSV, SHORTLIST.md, STATS.md
python tools/shots.py --segments S1,S4 --districts 1-9,18,19       # → data/shots/<pid>.png
python tools/befund_pages.py --segments S1,S4 --districts 1-9,18,19 # → site/b/*.html
python tools/letters.py --segments S1,S4 --districts 1-9,18,19 --pdf # → data/letters/*.pdf + BATCH.md
```
Braucht Python 3.13 mit `requests`, `beautifulsoup4`, `lxml`, `segno`, `playwright`. Absenderdaten, Buchungslink und Referenzen stehen in `config.json`.

## Konventionen
Nur reines Markdown — kein Dataview, keine Plugin-Syntax, weil diese Dateien genauso oft roh gelesen werden wie in Obsidian. Aufgaben sind `- [ ]`-Checkboxen mit IDs (`T2-4`). Jede Session endet damit, Boxen abzuhaken, eine Session-Log-Zeile im Hub zu ergänzen und den Sync-Check laufen zu lassen.
