# Copy proposals

Every project reviewed on 2026-09-19. Proposals only — none of this is applied,
because it is your voice and your facts.

Cards now clamp the summary to three lines, so an over-long description no
longer breaks the grid. It is still truncated rather than edited, and the first
three lines are what a visitor actually reads.

---

## Errors to fix

| Project | Field | Now | Should be |
|---|---|---|---|
| SaaS Platform Integrations | content | "**a had** a core responsibility to **seamlessly integration** our SaaS application" | "**I had** a core responsibility to **seamlessly integrate** our SaaS application" |
| Project Generator | brief | "Python's **build in** unittest library" | "Python's **built-in** unittest library" |
| Side-scroller Game | brief | "a **python** module" | "a **Python** module" |
| ISO 27001 | brief | "improvements to **company's** current tool" — and no full stop | "improvements to **the company's** tool for auditing production changes, in accordance with ISO 27001." |

The first is the most costly: it is the opening sentence of the project a
recruiter is most likely to open.

---

## Titles

Five run long enough to wrap to three or four lines on a card, which stops
cards in a row aligning. Each is really *title — subtitle*; the right-hand side
belongs in the description, or in a `subtitle` field if you want one later.

| Now | Chars | Proposed |
|---|---|---|
| SaaS Platform Integrations with Various ERPs – SAP, Oracle, Microsoft D365, NetSuite, etc. | 90 | **ERP Integration Programme** |
| Malaysia E-Invoicing Compliance Initiative – MyInvois Portal Integration | 72 | **Malaysia E-Invoicing Compliance** |
| Customer Account Consolidation & Data Migration – SAP ECC Integration | 69 | **Customer Account Consolidation** |
| AI Tooling Adoption Initiative – Microsoft Copilot in VS Code | 61 | **AI Tooling Adoption** |
| Order Management – Next-Generation Versioning Deployment | 56 | **Next-Generation Versioning Rollout** |

Two others are accurate but undersell the work:

- **Mapped Data Cleanup** → *Clinical Data Mapping Remediation*. The current
  title makes a patient-safety project under regulatory time pressure sound
  like database housekeeping.
- **File Transfer Script** → *Automated Secure File Transfer*. "Script" reads
  smaller than a thing that saved 40 hours a month.

---

## Summaries that are too long

Ten summaries run past 250 characters. Two lines at card width is roughly
150–180. Suggested rewrites, with the detail moving into `content` where there
is room for it:

**Custom Pricing API Integrations** — 431 → 148

> Real-time REST integrations validating order pricing against customers'
> own systems, across stock, contract, customer-specific and quote pricing.

**Offshore Delivery Hub** — 431 → 165

> Designed the operating model for a new Malaysia delivery hub: task handoff,
> communication cadences and quality standards across concurrent customer
> projects.

**Next-Generation Versioning** — 420 → 155

> Solution architect on the first production deployment of Esker's new
> versioning infrastructure, now the standard path for every Order Management
> project.

**ERP Integration Programme** — 354 → 171

> Six years integrating Esker's SaaS platform with SAP, Oracle, D365, NetSuite,
> AS400, QAD and middleware — from hands-on delivery to leading the team that
> builds them.

**Malaysia E-Invoicing** — 348 → 158

> Flew to Malaysia at short notice to automate customer submissions to the
> government's MyInvois portal, onboarding a high volume ahead of the
> compliance mandate.

**AI Tooling Adoption** — 309 → 152

> Project-managed the rollout of an internal Copilot-based development tool
> across the professional services team, from stakeholder engagement to
> adoption.

**Customer Account Consolidation** — 305 → 161

> Consolidated a customer's multiple accounts into one heavily customised SAP
> ECC ordering portal, preserving complete order history through the migration.

**EDI 850 Framework** — 302 → 169

> A no-code EDI 850 framework letting customers standardise inbound
> trading-partner orders and onboard new partners themselves, without
> developer involvement.

**AI-Powered Order Data Extraction** — 300 → 147

> ChatGPT with engineered prompts extracting shipping and carrier data from
> unstructured purchase orders, validated against master data before
> auto-processing.

**Project Generator** — 293 → 132

> Generates a standard Python package skeleton — source layout, tests,
> licence, run scripts — so a new project starts consistent.

---

## Summaries that are too thin

These read as unfinished beside the others. A sentence of substance each:

| Project | Now | Suggested direction |
|---|---|---|
| Portfolio Website | 82 ch, "Created with Django" | Say it is database-driven and that later versions were built with AI assistance — both are already in the content |
| Referral ETL Process | 83 ch, "collecting sales figures" | The content describes Mumps extraction into SQL with Python reporting; the summary should carry that |
| Side-scroller Game | 92 ch | Say what it taught you, not what PyGame is |
| Fantasy Football Stats | 102 ch | It aggregates across seasons that ESPN only shows one at a time — that is the point, and it is missing |
| Mapped Data Cleanup | 130 ch, "bad mapping values" | The content says millions of patients and strict timelines. None of that is in the summary. |

---

## Outcome lines

The `outcome` field now renders above the description on the card and in a
callout on the detail page, and stays invisible until filled in. Starting
points where the number already exists in your own text:

| Project | Outcome available from |
|---|---|
| File Transfer Script | "saving colleagues over 40 hours/month" — currently only in the Epic job bullet |
| Mapped Data Cleanup | 300+ systems evaluated; patient-safety impact |
| EDI 850 Framework | onboarding time and support overhead reduced — quantify if you can |
| Malaysia E-Invoicing | number of customers onboarded, and the days before the mandate |
| ERP Integration Programme | count of ERP platforms, size of team trained |
| Next-Generation Versioning | now the deployment path for every new Order Management project |

The projects that land hardest are the ones with a number in them. Most of
yours have none, and this is the field that fixes it.
