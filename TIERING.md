> 🇬🇧 English · 🇩🇪 [Deutsch](TIERING.de.md) · twin file — both languages are always changed together

# Lead validation and tiering — who is actually worth a letter

_2026-09-06 · pool: the 120 batch-1 candidates (S1 Beratung + S4 Immobilien, districts 1–9/18/19, score ≥ 3) · tool: `tools/validate.py` · working list: `data/TIERS.md`_

## Why a second pass exists
The scorer answers one question: *does this web presence have problems?* That is not the same question as *should we spend a letter, a stamp and an hour of David's time on them?* A dead practice has terrible SEO. So does a chamber of commerce. So does McKinsey. All three score high and all three are worthless to us.

So every prospect is re-checked live against three independent signals:

| Signal | Question | Evidence used |
|---|---|---|
| **LIVE** | Is this business still trading? | fresh fetch, DNS, parked-domain and closure detection, newest date on the page, phone, address, OSM opening hours |
| **FIT** | Would they ever hire a one-person studio? | number of people in the Impressum, entity type, category buying power, institution/corporate/franchise filters |
| **PAIN** | Is the problem real and worth money? | structural findings only (no website, unreachable, not mobile, unfinished, abandoned, old tech) — cosmetic tags do not count |

## What the validation actually caught
This pass was not a formality. It changed the batch in four ways:

1. **Three good leads were being wrongly discarded as "closed businesses".** The closure detector matched the words *Insolvenz* and *Liquidation* — which lawyers and tax advisors list as **services they sell**. It read their service menu as their obituary. Fixed: closure now has to be stated about the business itself ("unsere Kanzlei wurde geschlossen", "tritt in den Ruhestand"). Recovered: `dr-pfister.at`, `ra-novotny.at`, `rakwien.at`.
2. **Three "no website" letters would have been humiliating.** The businesses do have websites, OpenStreetMap just never tagged them: **Allmer Macke** → allmermacke.at, **Dr Naske** → naske.at, **RPCK Rastegar Panchal** → rpck.com (an international firm). A letter saying "nobody can find you online" to a firm with a working site ends the conversation and the referral chain behind it. The tool now probes the obvious domains and requires the business's own name on the page before we ever make that claim.
3. **Nine organisations can never be customers** and were removed: Rechtsanwaltskammer Wien and the Österreichische Notariatskammer (institutions), Boston Consulting Group and Taxand (corporates), RE/MAX twice (franchise), BUWOG and ICS Immo (corporate property), COOP HIMMELB(L)AU (a world-famous architecture practice that will not hire us).
4. **26 healthy firms were pulled out of the letter batch entirely.** They are alive and well-run; their only gaps are cosmetic (no English version, no blog, no OG image). Writing them a "findings" letter would read as nitpicking from a stranger. They get a different play later.

Two bugs behind these: `\bkammer\b` never matched *Rechtsanwaltskammer* (the word only exists as a compound), and a missing OSM phone number was being treated as evidence a business was dead, when it is only evidence that nobody tagged it.

## The tiers

| Tier | n | Meaning | Action |
|---|---|---|---|
| **A** | 5 | Trading, pays well, decision-maker known, and the defect is undeniable and provable in one screenshot | Letter this week |
| **B** | 28 | Real structural problem, but softer story or the decision-maker is still missing | Letter after A |
| **C** | 52 | The automated finding is **not trustworthy here** | Human check first, no letter |
| **D** | 26 | Healthy business, cosmetic gaps only | Watch list, different pitch |
| **X** | 9 | Institution, corporate, franchise, abandoned, parked | Never |

Full named list with every finding: `data/TIERS.md`.

## Tier A — the five to write first
All five are law, notary or property firms in central districts with a named partner in the Impressum, a working phone, and a defect you can photograph.

| Business | District | The one sentence | Offer |
|---|---|---|---|
| **Kuhn Rechtsanwälte GmbH** | 1010 | No mobile layout, and the newest date on the site is 2013 | A2 Relaunch |
| **Novak Rechtsanwalts GmbH** | 1010 | No mobile layout, though the content is current | A2 Relaunch |
| **Notar Winkler** | 1180 | No mobile layout, German only in a district full of international clients | A2 Relaunch |
| **Notariat Lukanec** | 1020 | Newest date 2020, and Google has no description to show under the name | A3 Visibility |
| **R.O.Y. Real** | 1060 | The site is visibly unfinished — placeholder text is live | A2 Relaunch |

**Verified on the live sites:** the missing mobile layout is confirmed for Kuhn, Winkler and Novak. That finding is the strongest asset we have — objective, instantly checkable, and the phone screenshot proves it without a single adjective. The date-based claims (Kuhn 2013, Lukanec 2020) and R.O.Y.'s "unfinished" need one human glance before printing, because a footer copyright and a placeholder block are easy to misread.

## Strategy per tier

### A — the proof letter, then a walk-in
Highest-effort treatment, because five letters is nothing and each one is worth €3,000–6,000.

- **Sequence:** letter Monday → walk in on day 4 or 5 (all five are central; a notary's office has a front desk) → LinkedIn note on day 10 if silent. Never all three at once.
- **The letter:** exactly the three findings, the phone screenshot at full size, one offer with a range, one proof, one next step. The screenshot does the persuading — keep the prose flat.
- **Do the re-mock (T4-2).** For these five specifically, spend the 20 minutes to rebuild their homepage in the Foundry kit with their own content and put it on the Befund page as before/after. Five re-mocks is one afternoon and it converts the "another agency letter" reflex into "they already started".
- **The proof to name:** loutati.at for the law and notary firms — same profession, same city, and it is a relaunch that turned into an ongoing retainer, which is exactly the shape of the relationship we want.
- **What kills it:** claiming a date you have not seen yourself. Check Kuhn's 2013 and Lukanec's 2020 in the browser first.

### B — the volume batch, split into two different plays
28 prospects, but they are not one group. They split into two:

**B1 · "You have no website at all" (11 businesses)** — estate agents, accountants and lawyers listed with an address and a phone and nothing else. This is the cleanest sale in the whole set: no incumbent agency, no "we already have someone", and the offer is A1 at €1,490–2,900.
- **Hard gate:** Google the name first. Three of these already turned out to have a site. The letter's opening claim is falsifiable in ten seconds, so it must be verified in ten seconds.
- **The letter:** the no-website variant — a screenshot of the bare Google result rather than of a website. "Wer Sie googelt, findet nur eine Adresse."
- **Best channel:** walk-in beats post here. An estate agent's office in the 1st district has someone at a desk, and "you have no website" is a conversation that works better face to face than in an envelope.

**B2 · "Your website has a real structural problem" (17 businesses)** — old tech, builder sites, abandoned content, no HTTPS. Offers A2 (8), A3 (7), A5, B1.
- **Sequence:** letter, then one LinkedIn note after 10 days. No walk-in — with a working website the walk-in reads as pushy.
- **The letter:** same three-finding structure as A, without the re-mock. Volume matters more than depth here.
- **Watch the tone:** these owners are often proud of having *a* website. Never write "outdated". Write what breaks: "am Handy muss man zoomen", "letztes Datum 2019".

### C — the qualification pile, not the reject pile (52)
This is the biggest tier and it is where the outreach person's hours actually belong. It splits by what is uncertain:

| Problem | n | What the helper does (~3 min each) |
|---|---|---|
| No decision-maker name found | 33 | Impressum → LinkedIn → WKO Firmen A-Z. Found → promote to B |
| Listed without a website, unverified | 14 | Google the name. No site → promote to B1. Site exists → re-run the audit on it |
| A website was found after all | 3 | Open it, judge it, re-score. The A1 letter is **forbidden** for these |
| OSM's URL no longer resolves | 2 | Find the current domain; the firm is probably alive under a new address |

Expect roughly half of tier C to become tier B once a human has spent an hour on it. That is the single highest-value hour in this whole pipeline — it is cheaper than any new scraping.

### D — the watch list, and a completely different pitch (26)
Twelve lawyers, five consultancies, four architects and a few others. Healthy sites, cosmetic gaps only.

Sending these a findings letter would be the classic agency mistake: telling a competent business their perfectly good website is wrong. Instead:
- **Do not write now.** Revisit in three months — a site that is fine today is abandoned in eighteen months, and then it becomes tier A or B.
- **When we do write, invert the frame.** Not "here is what is broken" but "here is what you are not doing yet": A3 Visibility, the Loutati model of monthly expert articles. That is a growth conversation with a healthy firm, not a repair conversation.
- **These are the best referral targets.** A well-run 1010 law firm that likes us but does not need us still knows five firms that do.

### X — never (9)
Delete from the working list, keep in the CRM as `nicht-kontaktieren` so no future batch resurrects them.

## Three hard gates before anything is printed
1. **Never claim "no website" without googling the name.** Proven necessary — three cases in a pool of 29.
2. **Never print a date you have not seen in the browser.** Copyright footers and news dates both feed the "abandoned" finding.
3. **Never write to tier D.** Nitpicking a healthy business costs the referral, and referral is the best channel we have.

## What this changes about the batch plan
The original batch was 67 letters. After validation the honest number is **33 letters** (A + B) — and 11 of those wait on a Google check, so the immediate, printable batch is **22**, with 5 of them getting the re-mock treatment.

That is a better week than 67 letters, because the 34 removed were institutions, corporates, healthy firms and unverifiable claims. Each of those letters would have cost credibility in a segment that talks to itself: Vienna's law and notary community is small, and a wrong claim travels further than a right one.

**Next:** the outreach person works tier C (roughly one hour for 52 prospects at the checklist rate), which should promote 20–25 into B and give a second full batch without any new scraping. Then batch 2 = S2 Gesundheit, same districts, same validation pass.
