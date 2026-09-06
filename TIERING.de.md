> 🇩🇪 Deutsch · 🇬🇧 [English](TIERING.md) · Zwillingsdatei — beide Sprachen werden immer gemeinsam geändert

# Prüfung und Einstufung der Leads — wer wirklich einen Brief wert ist

_2026-09-06 · Grundmenge: die 120 Batch-1-Kandidaten (S1 Beratung + S4 Immobilien, Bezirke 1–9/18/19, Score ≥ 3) · Werkzeug: `tools/validate.py` · Arbeitsliste: `data/TIERS.md`_

## Warum es einen zweiten Durchgang gibt
Die Bewertung beantwortet eine Frage: *Hat dieser Auftritt Probleme?* Das ist nicht dieselbe Frage wie: *Sind uns ein Brief, eine Briefmarke und eine Stunde von Davids Zeit wert?* Eine aufgelassene Kanzlei hat schlechtes SEO. Eine Rechtsanwaltskammer auch. McKinsey auch. Alle drei bekommen einen hohen Score, und alle drei sind für uns wertlos.

Deshalb wird jeder Prospect live gegen drei unabhängige Signale neu geprüft:

| Signal | Frage | Grundlage |
|---|---|---|
| **LIVE** | Ist der Betrieb noch tätig? | frischer Abruf, DNS, Erkennung geparkter Domains und Schließungen, jüngstes Datum auf der Seite, Telefon, Adresse, OSM-Öffnungszeiten |
| **FIT** | Würden die je ein Ein-Personen-Studio beauftragen? | Anzahl der Personen im Impressum, Rechtsform, Zahlungskraft der Kategorie, Filter für Institutionen/Konzerne/Franchise |
| **PAIN** | Ist das Problem echt und Geld wert? | nur strukturelle Mängel (keine Website, nicht erreichbar, nicht mobil, unfertig, verlassen, veraltete Technik) — kosmetische Tags zählen nicht |

## Was die Prüfung tatsächlich gefunden hat
Dieser Durchgang war keine Formalität. Er hat die Serie in vier Punkten verändert:

1. **Drei gute Leads wurden fälschlich als „geschlossen“ aussortiert.** Die Schließungserkennung hat auf die Wörter *Insolvenz* und *Liquidation* angeschlagen — die Anwälte und Steuerberater als **Leistungen anbieten**. Sie hat deren Leistungsverzeichnis als Todesanzeige gelesen. Behoben: eine Schließung muss jetzt über den Betrieb selbst ausgesagt sein („unsere Kanzlei wurde geschlossen“, „tritt in den Ruhestand“). Zurückgeholt: `dr-pfister.at`, `ra-novotny.at`, `rakwien.at`.
2. **Drei „Sie haben keine Website“-Briefe wären peinlich geworden.** Die Betriebe haben sehr wohl Websites, OpenStreetMap hat sie nur nie erfasst: **Allmer Macke** → allmermacke.at, **Dr Naske** → naske.at, **RPCK Rastegar Panchal** → rpck.com (eine internationale Kanzlei). Ein Brief mit „niemand findet Sie online“ an eine Kanzlei mit funktionierender Seite beendet das Gespräch und die Empfehlungskette dahinter. Das Werkzeug probiert jetzt die naheliegenden Domains und verlangt den Namen des Betriebs auf der Seite, bevor wir diese Behauptung überhaupt aufstellen.
3. **Neun Organisationen können nie Kunden werden** und sind raus: Rechtsanwaltskammer Wien und Österreichische Notariatskammer (Institutionen), Boston Consulting Group und Taxand (Konzerne), RE/MAX zweimal (Franchise), BUWOG und ICS Immo (Konzern-Immobilien), COOP HIMMELB(L)AU (ein weltbekanntes Architekturbüro, das uns nicht beauftragen wird).
4. **26 gesunde Büros wurden ganz aus der Briefserie genommen.** Sie sind aktiv und gut geführt; ihre einzigen Lücken sind kosmetisch (keine englische Version, kein Blog, kein OG-Bild). Ein „Befund“-Brief würde da wie Nörgeln von einem Fremden klingen. Für sie gibt es später ein anderes Vorgehen.

Dahinter steckten zwei Fehler: `\bkammer\b` hat *Rechtsanwaltskammer* nie erfasst (das Wort existiert nur als Zusammensetzung), und eine fehlende Telefonnummer in OSM wurde als Beleg gewertet, dass ein Betrieb tot ist — sie belegt nur, dass niemand sie eingetragen hat.

## Die Tiers

| Tier | n | Bedeutung | Handlung |
|---|---|---|---|
| **A** | 5 | Tätig, zahlungskräftig, Entscheider bekannt, und der Mangel ist unbestreitbar und mit einem Screenshot beweisbar | Brief diese Woche |
| **B** | 28 | Echter struktureller Mangel, aber weichere Geschichte oder Entscheider fehlt noch | Brief nach A |
| **C** | 52 | Der automatische Befund ist hier **nicht belastbar** | Zuerst menschliche Prüfung, kein Brief |
| **D** | 26 | Gesunder Betrieb, nur kosmetische Lücken | Beobachtungsliste, anderer Pitch |
| **X** | 9 | Institution, Konzern, Franchise, aufgegeben, geparkt | Nie |

Vollständige Liste mit allen Befunden: `data/TIERS.md`.

## Tier A — die fünf, die zuerst geschrieben werden
Alle fünf sind Anwalts-, Notariats- oder Immobilienbüros in zentralen Bezirken, mit namentlich genanntem Partner im Impressum, funktionierendem Telefon und einem Mangel, den man fotografieren kann.

| Betrieb | Bezirk | Der eine Satz | Angebot |
|---|---|---|---|
| **Kuhn Rechtsanwälte GmbH** | 1010 | Kein mobiles Layout, und das jüngste Datum auf der Seite ist 2013 | A2 Relaunch |
| **Novak Rechtsanwalts GmbH** | 1010 | Kein mobiles Layout, obwohl die Inhalte aktuell sind | A2 Relaunch |
| **Notar Winkler** | 1180 | Kein mobiles Layout, nur Deutsch in einem Bezirk voller internationaler Klientel | A2 Relaunch |
| **Notariat Lukanec** | 1020 | Jüngstes Datum 2020, und Google hat keine Beschreibung, die es unter dem Namen zeigen kann | A3 Sichtbarkeit |
| **R.O.Y. Real** | 1060 | Die Seite ist sichtbar unfertig — Platzhaltertext ist live | A2 Relaunch |

**Auf den echten Seiten überprüft:** das fehlende mobile Layout ist bei Kuhn, Winkler und Novak bestätigt. Dieser Befund ist unser stärkstes Werkzeug — objektiv, sofort nachprüfbar, und der Handy-Screenshot beweist ihn ohne ein einziges Adjektiv. Die datumsbasierten Behauptungen (Kuhn 2013, Lukanec 2020) und R.O.Y.s „unfertig“ brauchen vor dem Druck einen menschlichen Blick, weil ein Copyright im Fußbereich und ein Platzhalterblock leicht falsch gelesen werden.

## Vorgehen je Tier

### A — der Beweis-Brief, dann persönlich vorbei
Höchster Aufwand, denn fünf Briefe sind nichts und jeder ist 3.000–6.000 € wert.

- **Ablauf:** Montag Brief → Tag 4 oder 5 vorbeigehen (alle fünf sind zentral; ein Notariat hat einen Empfang) → Tag 10 LinkedIn-Notiz, falls still. Nie alles drei gleichzeitig.
- **Der Brief:** genau die drei Befunde, der Handy-Screenshot in voller Größe, ein Angebot mit Spanne, ein Beweis, ein nächster Schritt. Der Screenshot überzeugt — der Text bleibt nüchtern.
- **Die Neuskizze machen (T4-2).** Für genau diese fünf lohnen sich die 20 Minuten, ihre Startseite mit ihren eigenen Inhalten im Foundry-Kit neu zu bauen und als Vorher/Nachher auf die Befund-Seite zu legen. Fünf Neuskizzen sind ein Nachmittag und verwandeln den Reflex „schon wieder ein Agenturbrief“ in „die haben schon angefangen“.
- **Welcher Beweis:** loutati.at für die Anwalts- und Notariatsbüros — gleicher Berufsstand, gleiche Stadt, und es ist ein Relaunch, aus dem ein laufender Retainer wurde, also genau die Form von Zusammenarbeit, die wir wollen.
- **Was es zerstört:** ein Datum behaupten, das man nicht selbst gesehen hat. Kuhns 2013 und Lukanecs 2020 vorher im Browser prüfen.

### B — die Mengenserie, in zwei verschiedene Spiele geteilt
28 Prospects, aber keine einheitliche Gruppe. Sie teilen sich in zwei:

**B1 · „Sie haben gar keine Website“ (11 Betriebe)** — Makler, Buchhalter und Anwälte, die mit Adresse und Telefon gelistet sind und sonst nichts. Das ist der sauberste Verkauf im ganzen Bestand: keine bestehende Agentur, kein „wir haben schon jemanden“, und das Angebot ist A1 zu 1.490–2.900 €.
- **Harte Sperre:** Namen zuerst googeln. Bei drei dieser Betriebe stellte sich heraus, dass es doch eine Seite gibt. Die Eingangsbehauptung des Briefs ist in zehn Sekunden widerlegbar, also muss sie in zehn Sekunden geprüft werden.
- **Der Brief:** die Variante ohne Website — ein Screenshot des nackten Google-Ergebnisses statt einer Website. „Wer Sie googelt, findet nur eine Adresse.“
- **Bester Kanal:** hier schlägt Vorbeigehen die Post. In einem Maklerbüro im 1. Bezirk sitzt jemand am Empfang, und „Sie haben keine Website“ ist ein Gespräch, das persönlich besser funktioniert als im Kuvert.

**B2 · „Ihre Website hat ein echtes strukturelles Problem“ (17 Betriebe)** — veraltete Technik, Baukastenseiten, verlassene Inhalte, kein HTTPS. Angebote A2 (8), A3 (7), A5, B1.
- **Ablauf:** Brief, dann nach 10 Tagen eine LinkedIn-Notiz. Kein Vorbeigehen — mit funktionierender Website wirkt das aufdringlich.
- **Der Brief:** dieselbe Drei-Befund-Struktur wie bei A, ohne Neuskizze. Hier zählt Menge mehr als Tiefe.
- **Auf den Ton achten:** diese Inhaber sind oft stolz darauf, überhaupt *eine* Website zu haben. Nie „veraltet“ schreiben. Schreiben, was kaputt ist: „am Handy muss man zoomen“, „letztes Datum 2019“.

### C — der Qualifizierungsstapel, nicht der Absagestapel (52)
Das ist das größte Tier, und genau hier gehören die Stunden der Outreach-Person hin. Es gliedert sich danach, was unklar ist:

| Problem | n | Was die Hilfskraft tut (~3 Min. je Fall) |
|---|---|---|
| Kein Entscheidername gefunden | 33 | Impressum → LinkedIn → WKO Firmen A-Z. Gefunden → Aufstufung nach B |
| Ohne Website gelistet, ungeprüft | 14 | Namen googeln. Keine Seite → Aufstufung nach B1. Seite vorhanden → Audit darauf neu laufen lassen |
| Es wurde doch eine Website gefunden | 3 | Öffnen, beurteilen, neu bewerten. Der A1-Brief ist hier **verboten** |
| OSM-Adresse löst nicht mehr auf | 2 | Aktuelle Domain suchen; das Büro lebt vermutlich unter neuer Adresse |

Rund die Hälfte von Tier C wird zu Tier B, sobald ein Mensch eine Stunde investiert hat. Das ist die wertvollste Stunde der ganzen Pipeline — billiger als jede neue Ernte.

### D — die Beobachtungsliste, und ein völlig anderer Pitch (26)
Zwölf Anwälte, fünf Beratungen, vier Architekturbüros und ein paar weitere. Gesunde Seiten, nur kosmetische Lücken.

Ein Befund-Brief wäre hier der klassische Agenturfehler: einem gut geführten Betrieb erklären, seine völlig brauchbare Website sei falsch. Stattdessen:
- **Jetzt nicht schreiben.** In drei Monaten wieder ansehen — eine Seite, die heute in Ordnung ist, ist in achtzehn Monaten verlassen, und dann wird sie zu Tier A oder B.
- **Wenn wir schreiben, den Rahmen umdrehen.** Nicht „das ist kaputt“, sondern „das machen Sie noch nicht“: A3 Sichtbarkeit, das Loutati-Modell mit monatlichen Fachbeiträgen. Das ist ein Wachstumsgespräch mit einem gesunden Büro, kein Reparaturgespräch.
- **Das sind die besten Empfehlungsgeber.** Eine gut geführte Kanzlei im 1. Bezirk, die uns mag, aber nicht braucht, kennt trotzdem fünf Kanzleien, die uns brauchen.

### X — nie (9)
Aus der Arbeitsliste löschen, im CRM als `nicht-kontaktieren` behalten, damit keine spätere Serie sie wieder ausgräbt.

## Drei harte Sperren, bevor irgendetwas gedruckt wird
1. **Nie „keine Website“ behaupten, ohne den Namen zu googeln.** Nachweislich nötig — drei Fälle bei 29.
2. **Nie ein Datum drucken, das man nicht im Browser gesehen hat.** Copyright-Fußzeilen und News-Daten speisen beide den „verlassen“-Befund.
3. **Nie an Tier D schreiben.** An einem gesunden Betrieb herumzukritteln kostet die Empfehlung, und Empfehlung ist unser bester Kanal.

## Was das für den Serienplan bedeutet
Die ursprüngliche Serie umfasste 67 Briefe. Nach der Prüfung ist die ehrliche Zahl **33 Briefe** (A + B) — und 11 davon warten auf eine Google-Prüfung, die sofort druckbare Serie ist also **22**, davon 5 mit Neuskizze.

Das ist eine bessere Woche als 67 Briefe, denn die 34 entfernten waren Institutionen, Konzerne, gesunde Büros und nicht überprüfbare Behauptungen. Jeder dieser Briefe hätte Glaubwürdigkeit in einem Segment gekostet, das miteinander redet: die Wiener Anwalts- und Notariatswelt ist klein, und eine falsche Behauptung reist weiter als eine richtige.

**Als Nächstes:** die Outreach-Person arbeitet Tier C ab (etwa eine Stunde für 52 Prospects im Checklisten-Takt), was 20–25 nach B hochstuft und eine zweite volle Serie ohne jede neue Ernte ergibt. Danach Serie 2 = S2 Gesundheit, dieselben Bezirke, derselbe Prüfdurchgang.
