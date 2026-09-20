# Portfolio review — 18 projects

Reviewed on 2026-09-19 against the expanded project set. Proposals only;
nothing here is implemented.

The new professional projects are a large improvement. The gap the earlier
[recruiter review](RECRUITER-REVIEW.md) named — a site claiming B2B, ERP and
healthcare integration with nothing in the portfolio showing it — is closed.
Five projects now demonstrate ERP integration directly, and the AI work is
current in a way most portfolios are not.

The problems below are the problems of having enough material, not too little.

---

## Urgent

### 1. Nothing is featured, so "Selected work" never renders

`featured` is `False` on all 18. The Selected Work section built in Phase 3 has
never appeared on the live page — every project still competes as an equal in
one flat grid.

This matters more now than at nine projects, because the ordering actively
buries your best work. Sorting is *featured, then newest start date*, so:

| Project | Starts | Sorts |
|---|---|---|
| Offshore Delivery Hub | Aug 2026 | 1st |
| AI Tooling Adoption | Apr 2026 | 2nd |
| **SaaS Platform Integrations with ERPs** | Aug 2020 | **~9th** |
| **Custom Pricing API Integrations** | Aug 2020 | **~10th** |

Your flagship — six years of ERP integration work across nine named platforms —
sorts below a side project because it *started* in 2020. Featuring three or four
projects fixes this in the admin with no code.

Suggested: ERP Integrations, EDI 850 Framework, AI Tooling Adoption, and either
Mapped Data Cleanup (patient safety, the strongest story) or Malaysia
E-Invoicing (compliance under deadline).

*Effort: four checkboxes.*

### 2. A copy error in the flagship project

`erp-integrations` content opens:

> "Throughout my tenure at Esker, **a had** a core responsibility to
> **seamlessly integration** our SaaS application with various ERP software."

Two errors in the first sentence of the project a recruiter is most likely to
open. Worth a proofread pass across all 18 while you are in there.

*Effort: minutes.*

### 3. "Unspecified" renders as a language

Offshore Delivery Hub has `language = Unspecified`, which prints literally in
the card's tech run beside real languages. It reads as a bug rather than an
absence.

Two fixes, and I would do both: set it to something real if any code was
involved, **and** change the template to skip `Unspecified` so this cannot
happen again.

*Effort: minutes in the admin; ~20 minutes for the template guard and a test.*

---

## Taxonomy — the capability axis is losing its edge

### 4. "Automation & Tooling" is on 11 of 18 projects

| Capability | Projects |
|---|---|
| Automation & Tooling | **11** |
| Web Applications | 8 |
| Data & ETL | 6 |
| Systems Integration | 5 |
| Compliance & Process | 5 |
| Healthcare Interoperability | 2 |

A filter that matches 61% of the catalogue does not narrow anything. It is
currently applied to a PowerShell file-mover, a portfolio website, an LLM
extraction pipeline and an EDI framework — four unrelated kinds of work.

**Proposal: split out an AI capability.** Four projects carry the AI/LLM tags
already (AI Tooling Adoption, LLM Order Extraction, EDI 850, ERP Integrations).
"AI & LLM Solutions" as its own capability would:

- pull Automation & Tooling down to a meaningful ~7
- give the most current, most differentiating work its own filter
- put an AI keyword on the capability axis, where recruiters look first

Then reserve Automation & Tooling for genuine internal tooling and scripting.

### 5. "Web Applications" does not mean what it says

It is on 8 projects including account consolidation, Malaysia e-invoicing, ISO
27001 and pricing integrations. None of those is a web application in the sense
a recruiter reads it — they are customisations and integrations on a SaaS
platform.

**Proposal: rename to "SaaS Platform Development".** More accurate, and it
describes what you actually do all day. Portfolio Website is then the one entry
that genuinely does not belong, and can drop the tag.

A rename is a single admin edit — the slug regenerates, and the filter picks it
up automatically.

### 6. Four AI skills that always appear together

`AI`, `ChatGPT`, `Claude`, `LLM` co-occur on all four AI projects, so the card
renders four pills saying one thing. In the tech run that reads as padding, and
the earlier review flagged the same problem in the Skills list.

**Proposal:** collapse to named tools you actually used — `Claude Code`,
`GitHub Copilot`, `ChatGPT` — and let the new AI capability carry the concept.
Keep `LLM` only if you want the bare acronym for keyword matching.

### 7. Two projects have no capability at all

Side-scroller Game and Python Components are invisible to capability filtering.
Given both are junior-signal personal projects, the question is whether they
should still be on the site at all — see item 11.

### 8. One skill with zero evidence

`Django` is claimed but tagged on no project, despite Portfolio Website being
built with it. The home page shows it with a count of zero, which is the one
number on that list you do not want.

*Effort: one click.*

---

## Presentation

### 9. Titles are too long for cards

| Chars | Title |
|---|---|
| 90 | SaaS Platform Integrations with Various ERPs – SAP, Oracle, Microsoft D365, NetSuite, etc. |
| 72 | Malaysia E-Invoicing Compliance Initiative – MyInvois Portal Integration |
| 69 | Customer Account Consolidation & Data Migration – SAP ECC Integration |

At card width a 90-character title wraps to four lines and pushes everything
below it down, so cards in the same row stop aligning.

Every one of these is really *title – subtitle*. **Proposal: add a `subtitle`
field**, render the title large and the subtitle small beneath it, and shorten
the titles to the part before the dash. "SaaS Platform Integrations" is a better
card heading, and "SAP, Oracle, D365, NetSuite and more" is a better subtitle
than a title fragment.

*Effort: a small migration plus template work, maybe two hours. Or zero code if
you just shorten the titles and move the detail into the description.*

### 10. Brief descriptions range from 82 to 431 characters

Portfolio Website has 82; Pricing Integrations and Offshore Delivery Hub have
431. The long ones are full paragraphs and dominate their cards, so the grid
looks unbalanced and the short ones look unfinished.

**Proposal:** treat `briefDescription` as a card summary with a real limit —
roughly 160–200 characters, two lines at card width — and let the full story
live in `content` where there is room. Either edit them down, or clamp the card
to two lines in CSS and keep the full text for the detail page.

### 11. Five personal projects now sit among thirteen professional ones

Side-scroller Game, Python Components and Project Generator are the kind of work
that helps a junior candidate and does the opposite for someone presenting as a
Solution Architect. They were defensible when the portfolio was thin. It is not
thin any more.

**Proposal:** retire those three, or keep them strictly in the archive section
below Selected Work. Portfolio Website and Fantasy Football Stats can stay —
the first is self-evidently current and the second is a real API integration.

### 12. Nine projects still have no image

The generated artwork is in `source-images/project-art/`, named by slug, ready
to upload. Until then those nine share the placeholder, which is fine but says
nothing project-specific.

### 13. Six projects are open-ended

Portfolio Website, AI Tooling, ERP Integrations, Offshore Delivery Hub, Pricing
Integrations and EDI 850 all render "– Present".

Two of those are not really projects: **ERP Integrations** and **Pricing
Integrations** both run Aug 2020 – Present, which is your whole Esker tenure.
They are ongoing *programmes* of work. That is worth saying explicitly —
"ongoing since 2020" reads as sustained ownership, where six simultaneous
"Present" entries read like nothing ever finishes.

---

## Code proposals

Ranked by value for effort.

| # | Proposal | Why | Effort |
|---|---|---|---|
| A | Skip `Unspecified` in the language tech run | Item 3, a visible bug | 20 min |
| B | `outcome` field, rendered above the description | Still the biggest content gap; the 40 hrs/month figure lives in a job bullet, not on the project page | 1 hr |
| C | `subtitle` field | Item 9, fixes card alignment | 2 hrs |
| D | Counts in the filter menu — "Systems Integration (5)" | Tells a visitor what is behind a filter before they click, and would have made item 4 obvious immediately | 1 hr |
| E | `published` flag | Draft projects in the admin without exposing them; still outstanding from the first review | 1 hr |
| F | Clamp card description to two lines | Item 10 without editing 18 descriptions | 20 min |
| G | Admin action to merge two skills | Item 6 by hand means re-tagging every project; a merge action makes taxonomy changes cheap and reversible | 2 hrs |
| H | Warn in the admin when a skill has zero projects | Item 8 caught automatically rather than by review | 45 min |

### On B, the outcome field

Of the 18 projects, the descriptions that land hardest are the ones with a
number in them. Most have none. A single `outcome` line per project, rendered in
the accent above the description, would be the highest-value content change on
the site — and unlike most of this list, it needs your knowledge rather than
mine.

---

## Suggested order

1. **Today, no code:** feature four projects (1), fix the copy error (2), tag
   Django (8), set a real language on Delivery Hub (3).
2. **This week, admin only:** rename Web Applications (5), add the AI capability
   and re-tag (4), collapse the AI skills (6), decide on the personal projects
   (11), upload the nine images (12).
3. **When you next touch code:** A, then B, then D.
4. **Later:** C, E, F, G, H.

Items 1, 2, 5, 6, 8, 11, 12 and 13 are content only. Everything in the code
table needs a migration or template work, and none of it blocks the content
pass.
