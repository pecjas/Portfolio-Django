# Portfolio review, from a recruiter's perspective

Reviewed **https://jasonpeck.pythonanywhere.com** (production, real data) on
2026-09-18, against what a technical recruiter or hiring manager looks for when
screening a Solution Architect candidate.

Nothing here is implemented — each item is a proposal to accept or reject.

## What this review deliberately ignores

Everything the pending code migration already fixes: the visual redesign, dark
mode, responsive layout, filter behaviour, slug URLs, SEO and social card, the
styled 404, accessibility, and the home-page intro paragraph (which is template
text and gets replaced by the new tagline, typo and all).

What remains is **database content** — jobs, education, skills, projects — which
carries across unchanged, plus a few template strings the migration leaves
alone. That is where every item below sits.

One precondition, since it is not content: the CV still has to be committed.
`main/static/main/files/jason-peck-resume.pdf` is untracked, so the Download CV
button will not appear in production even after the deploy. A downloadable
resume is the single most-wanted artifact on a portfolio site.

---

## What is already working

Worth stating plainly, because it sets the bar for the rest:

- **Epic's end date is set** (June 2017 – Aug 2020). No overlapping "Present".
- **The Esker progression reads as a progression.** Four roles with genuinely
  different bullets — leading a team, securing one of Esker's largest projects
  globally, establishing documentation practice across the US division.
- **The Epic bullets are excellent.** 40 hours/month saved, 300+ customer
  systems evaluated, patient-safety impact. Concrete, quantified, memorable.
- **Project write-ups are real prose**, not stubs. Mapped Data Cleanup and
  File Transfer Script both explain a genuine problem and a considered solution.
- **Every personal project links to GitHub**; no professional one does, which
  is the correct instinct.

I also checked how the migration will categorise projects: `is_personal` is
seeded from whether a GitHub link exists, and for all nine that produces the
right answer. Nothing to fix there.

---

## High impact

### 1. Your portfolio does not demonstrate what you are selling

This is the biggest gap on the site.

Your tagline positions you as a Solution Architect with "a strong background in
**B2B, ERP, and healthcare integration**." Your last four roles are Esker —
REST-based ERP integrations, four years of them.

The portfolio contains **zero ERP or B2B integration projects.**

What it does contain: healthcare interoperability (Mumps, from Epic), two
internal tools, and five personal Python projects. A recruiter matching the
headline against the evidence finds the healthcare half supported and the B2B
and ERP half unsupported — for the work you have spent the last four years
doing and want to be hired for next.

Even heavily redacted, one Esker-era entry would close this: the integration
pattern, the systems connected, the volume, the constraints. No customer names
needed.

*Effort: an hour of writing, plus a judgement call on what you can disclose.*
*This is the highest-value item on the list.*

### 2. TypeScript is missing from Skills

The list is:

> AI, C#, ChatGPT, Claude, Communication, Critical Thinking, Django, **Java**,
> JavaScript, LLM, M (Mumps), Mathematics, PowerShell, Python, SQL, Teaching

TypeScript appears in **three** of your job entries and in the new tagline. It
is not in Skills. Recruiters and automated screening tools match this list
literally, so this is a keyword you are losing for no reason.

The reverse problem sits next to it: **Java** is listed but appears in no job
bullet and no project on the site. If it is genuine but dated, that is fine —
but right now it is the one entry with no supporting evidence anywhere.

*Effort: two minutes in the admin.*

### 3. Skills has no architecture vocabulary

Every entry is a language, a soft skill, or an AI tool. For a Solution
Architect, the terms a recruiter actually searches on are absent:

> REST APIs · system integration · ERP integration · B2B / EDI · healthcare
> interoperability (HL7, FHIR, LOINC, SNOMED) · ETL · solution design ·
> requirements gathering · Scrum · technical leadership

You have demonstrated nearly all of these on the site — LOINC and SNOMED appear
by name in Mapped Data Cleanup — but they are not where anyone screening will
look for them.

Separately, **AI, ChatGPT, Claude and LLM are four entries for one capability**
and read as padding. One line — "LLM tooling (Claude Code, Copilot, ChatGPT)" —
says more and takes less space.

*Effort: 15 minutes in the admin.*

### 4. The portfolio order works against you

Nine projects, five of them personal, and no ordering control — so what a
recruiter sees first is largely accidental.

Ranked by what they say about a Solution Architect candidate:

| Project | Signal |
|---|---|
| Mapped Data Cleanup | Strongest on the site — patient safety, millions affected, strict timelines |
| Referral ETL Process | Real architecture across three technologies |
| ISO 27001 Change Management | Compliance, risk, process improvement |
| File Transfer Script | Quantified time saved |
| Portfolio Website | Fine, and self-evidently current |
| Fantasy Football Stats | Competent hobby work |
| Python Components | Developer-hygiene project |
| Project Generator | Scaffolding script |
| Side-scroller Game | Reads as a learning exercise |

The bottom four are the kind of thing that helps a junior candidate stand out
and does the opposite for a senior one — a side-scroller and a project
scaffolder are what a recruiter expects from a bootcamp portfolio, not from
someone leading integration architecture.

Two options: add an ordering field so the professional work leads, or retire the
weakest two or three. Either beats the current arbitrary order.

*Effort: an hour for an ordering field plus migration; minutes if you just
delete.*

### 5. Project pages describe the work but skip the result

Your job bullets are quantified. Your project pages mostly are not, and the
same work appears in both.

The clearest example: your Epic entry says the file management script saved
**over 40 hours a month**. The File Transfer Script project page — the detailed
write-up of that exact script — never mentions it. The page explains the SFTP
problem thoroughly and then stops before the payoff.

Mapped Data Cleanup describes the scale of the problem ("millions of patients")
but not the outcome: how many systems were corrected, how fast, what the
timeline pressure was.

One bolded outcome line at the top of each professional project would fix this:

> **Outcome** — eliminated ~40 hours of manual file handling per month across
> the team.

*Effort: 15 minutes per project.*

---

## Medium impact

### 6. Projects have no dates

`Project` has no date field at all, so nothing indicates when any of this
happened. **This is not fixed by the migration.**

A recruiter cannot tell whether the Mumps work is from 2018 and the current work
is TypeScript, or the reverse. For a candidate whose recent experience is the
selling point, undated projects let the oldest work look as current as the
newest.

Adding nullable `startDate` / `endDate` is a small migration plus a template
line, and it gives you newest-first ordering, which also solves item 4.

*Effort: an hour of code, plus filling in nine dates.*

### 7. Titles undersell the work

"Mapped Data Cleanup" is the title on your most impressive project — one
involving incorrect clinical code mappings with the potential to affect patient
care at scale, under regulatory time pressure. The title makes it sound like
database housekeeping.

Titles are the only part of a project most visitors read. Compare:

- *Mapped Data Cleanup* → **Clinical Data Mapping Remediation at Scale**
- *File Transfer Script* → **Automated Secure File Transfer (40 hrs/month saved)**
- *Referral ETL Process* → **Referral Metrics ETL Pipeline**

*Effort: 10 minutes.*

### 8. The contact page is written for freelance clients

> "Have questions? Want to reach out to discuss a future project? Fill out the
> form below to send me an email."

You are open to work, and this addresses someone hiring a contractor. **The
migration does not change this string** — it is in `contact.html` and carries
over as-is.

Missing, and expected by recruiters:

- Your email **in plain text on the page**, not only in the footer — many people
  want to send from their own client
- A response-time expectation, which also reassures them the form works
- LinkedIn, repeated here
- Location and working preference — "Madison, WI, open to remote" is on the home
  page but not here
- One line on what you want to hear about, which filters bad-fit outreach

*Effort: 20 minutes of copy, one template edit.*

### 9. Education leads with a 2017 GPA

The entry shows "Overall GPA: 3.495/4.000" and "Dean's List (three semesters)"
for a degree awarded in May 2017. Nine years in, academic detail reads as
filler.

The genuinely interesting fact is unframed: **a BBA in Marketing and
Communication Arts, now leading integration architecture.** For a customer-facing
architect — someone who scopes with customers and translates business needs into
systems — that is a differentiator, not an oddity. Right now it looks like an
unrelated degree with a GPA attached.

Note that `GPA` is a required field on the model, so hiding it needs either a
template change or a migration making it nullable.

*Effort: minutes for the template; small migration if you want the field gone.*

### 10. The 2015 marketing role

Popcult Marketing, five months, eleven years ago, three bullets about social
media strategy. It is the weakest block on a page whose other entries are
strong.

Two defensible options: drop it, or keep it and let the marketing degree plus
marketing role support a deliberate "I came to engineering from the business
side" narrative. What does not work is leaving it unexplained at the bottom,
which is the current state.

*Effort: minutes either way, once you decide.*

---

## Lower priority

### 11. Personal projects do not say why they exist

Fantasy Football Stats and Project Generator describe what they do in detail but
never why you built them. At senior level, side projects are read as evidence of
curiosity and self-direction — one sentence of motivation is worth more than a
feature list.

### 12. No proof from anyone but you

Everything is self-reported. Two short pull quotes from LinkedIn
recommendations, linked to the profile, are the cheapest credible
counterweight — close to free if the recommendations already exist.

### 13. Project imagery

Several projects have no image. For integration work, an architecture or
data-flow diagram — even a redacted one — communicates more in three seconds
than three paragraphs. This would help items 1 and 4 at the same time.

### 14. No public technical writing

Not expected at this level, but it differentiates for architect roles. If
anything internal could be adapted — an integration pattern, a migration
post-mortem — two or three short posts would carry weight. Largest effort on
this list by a wide margin.

---

## Suggested order

| Priority | Items | Why |
|---|---|---|
| First | 2, 3 | Twenty minutes total, and you are currently losing keyword matches |
| Then | 1 | The headline claims B2B and ERP; nothing on the site shows it |
| Then | 5, 7 | Your strongest work is underlabelled and under-quantified |
| When convenient | 4, 8, 9, 10 | Real polish, modest effort |
| If you touch the model | 6, and 4 alongside it | One migration covers ordering and dates |
| Someday | 11, 12, 13, 14 | Nice to have |

Items 1, 2, 3, 4, 5, 7, 10, 11 and 12 are **content only** — admin edits, no
deploy needed. Items 6 and 9 need a migration. Item 8 is a template edit.
