# Capability-led portfolio — phased plan

Reorients the portfolio around **what kind of work a project is**, rather than
which programming language it used. Language stops being the organising
principle and becomes a tag; capability takes its place.

Driven by the finding in [RECRUITER-REVIEW.md](RECRUITER-REVIEW.md): the site
claims a background in B2B, ERP and healthcare integration, and then offers a
taxonomy that cannot express any of those things.

## Sequencing

Code lands first, content follows. Every phase must therefore **work correctly
with no capability data entered at all** — an empty taxonomy renders exactly
today's page, never an empty heading or a dead filter. That constraint is
restated in each phase because it is the thing most likely to get broken.

Phase 1 deliberately carries *all* schema and admin changes, including ones not
needed until Phase 3, so that content entry happens in one pass rather than
three.

---

## Phase 1 — Data model and admin

**Status: complete (2026-09-18). 54 tests passing; public site unchanged.**

- [x] Add `TypeScript` to `Project.ProgramLanguage` — was absent, despite being
      the language of the last four years of work
- [x] Add `Skill.category`, so a skill knows what kind of thing it is
- [x] Add `Skill.slug` for stable filter values and URLs
- [x] Add `Skill.sort_order` so display order is deliberate, not alphabetical
- [x] Add `Project.skills` — many-to-many to `Skill`
- [x] Add `Project.featured` for the Selected Work section in Phase 3
- [x] Add `Project.startDate` / `Project.endDate`, both nullable
- [x] Admin: skill picker on `Project`, category grouping and inline editing
      on `Skill`
- [x] Migrations `0004_project_capabilities` and `0005_seed_capabilities`
- [x] Tests covering the new fields, the admin, and the empty-data case

### Notes

**Adding a unique column to populated rows.** `makemigrations` generated the
skill slug as a single `AddField` with `unique=True`, which gives every existing
row the same empty default and fails the constraint. Split into the same three
steps `0002_project_slug` uses: add non-unique, backfill, then alter to unique.

**Slugs spell out symbols.** `slugify` strips them, so "C#" and "C++" both
became `c` — a collision and a meaningless URL. `#`, `++` and `&` are now
expanded first, giving `c-sharp`, `c-plus-plus` and `data-and-etl`.

**The seed is reversible without data loss.** Rolling `0005` back deletes only
seeded capabilities that no project references; anything tagged with content is
left alone. Verified by rolling both migrations back and re-applying.

**Existing skills are categorised by name**, and anything unrecognised stays at
the `language` default rather than being guessed at — a wrong category is then a
visible one-click fix rather than a silent mislabelling.

**`_build_unique_slug` is now a module-level helper** shared by `Project` and
`Skill`, rather than a `Project` method. Migration `0002` keeps its own copy, as
historical migrations should not call current model code.

### Skill categories

| Category | Purpose | Examples |
|---|---|---|
| `capability` | **The new primary axis.** What kind of work it is. | Systems Integration, Healthcare Interoperability, Data & ETL, Automation & Tooling, Compliance & Process, Web Applications |
| `language` | Programming languages, for the home-page list | Python, TypeScript, SQL |
| `platform` | Frameworks, products, systems | Django, Esker, Epic |
| `tooling` | Development tooling, including AI | Claude Code, Copilot |
| `practice` | Ways of working | Scrum, Technical Leadership, Requirements Gathering |

Only `capability` skills drive the portfolio filter. The rest exist so the home
page skills section can be grouped in Phase 4, and so the flat keyword list a
recruiter's screening tool reads stays complete.

`Project.language` stays as it is. Languages are already modelled there and a
second source of truth would be worse than the small overlap.

---

## Phase 2 — Portfolio page, capability first

**Status: complete (2026-09-18). 63 tests passing.**

- [x] Capability is the primary filter group, labelled "Kind of work"
- [x] Personal / Professional stays as the secondary axis
- [x] Language moves to a quiet tertiary group
- [x] Cards show capability labels prominently, languages quietly
- [x] Capability filter group is hidden entirely while no project has one
- [x] Filter state syncs to the URL under `?work=`; chips carry over

### Notes

**Categories are discovered from the DOM, not hardcoded.** `filterCards.js` used
a fixed `CATEGORIES` array; it now collects categories from the rendered menu
buttons in document order. That is what makes hide-when-empty work with no flag
to keep in sync: a group the server declines to render simply does not
participate in filtering, and a stale `?work=` parameter is ignored rather than
applied. Menu order in the template is therefore also filter precedence.

**Only capabilities in use are offered.** Six are seeded, but the menu lists
only those a project actually claims. An empty filter option advertises the gap
it is meant to fill.

**Two tiers of tag.** Capabilities sit above the description as outlined pills;
languages and platforms sit below it as a plain dot-separated run. Both are
still in the markup for keyword matching — the change is which one the card
leads with.

**The query-count test was strengthened, not just updated.** Adding the skills
prefetch and the capability lookup took the portfolio page from 2 queries to 4,
and the existing test simply pinned a number at one project count. It now
asserts the count is *identical* at 8 and 16 projects, with capabilities
attached, so it detects growth rather than change.

**Verified end to end with real clicks**, not `element.click()` — selecting
Systems Integration filtered to one project, wrote `?work=systems-integration`,
rendered the chip, and logged no console errors. Reloading
`?work=web-applications&lang=Python` restored both filters and intersected them
correctly. Contrast measured against the real card surface, which is a
`color-mix()` result: 12.63, 3.88 and 7.40 against minimums of 4.5, 3.0 and 4.5.

**The empty-taxonomy path was checked in the browser as well as in tests** — with
every project untagged the page renders the previous two-filter layout and the
previous lede.

---

## Phase 3 — Selected Work, dates and ordering

**Status: complete (2026-09-18). 78 tests passing.**

- [x] A "Selected work" section for `featured` projects, above the rest
- [x] Remaining projects in a denser "More projects" grid below
- [x] Project dates rendered on cards and detail pages where present
- [x] Ordering: featured first, then newest by `startDate`, then title
- [x] With nothing featured, the page renders one flat grid — the pre-Phase-3
      page exactly

### Notes

**The card markup is now an include.** Two sections rendering the same card from
two copies of the markup would have drifted within a release. `project_card.html`
takes `project`, `projDetails` and `defaultImage`.

**Card headings change level with the layout.** Sections introduce an `h2`, so
cards inside them are `h3`; in the flat layout they stay `h2`. Otherwise the
document skips from `h1` straight to `h3` whenever nothing is featured.

**Undated projects sort last, not first.** `ORDER BY startDate DESC` puts NULLs
first on some backends, which would have let an undated project outrank a dated
one. `F('startDate').desc(nulls_last=True)` pins it, and a test asserts it.

**Lazy loading moved into the view.** It was `forloop.counter > 3`, which breaks
once there are two loops — the fourth card of each section would have loaded
eagerly. The view now sets a `lazy` flag from the overall index.

**Sections hide with their contents.** A filter that empties a section hides the
heading too, or "Selected work" sits above nothing. Verified in the browser:
filtering to Web Applications hides Selected work and shows two cards under More
projects; filtering to Systems Integration does the reverse; a combination
matching nothing hides both and shows the empty state; clearing restores both.
No console errors in any state.

**The filter script still has one root.** Both sections sit inside
`#cardContainer`, so the script did not need to learn about the new shape — only
to hide emptied sections. A test asserts the cards remain inside that root.

---

## Phase 4 — Skills as evidence

**Status: complete (2026-09-18). 89 tests passing.**

- [x] Home page skills render grouped by category
- [x] Skills with projects behind them link into the filtered portfolio
- [x] Each shows the count of projects demonstrating it
- [x] Skills with no projects still render as plain text
- [x] No proficiency ratings

### Notes

**Counts come from whatever the link filters on.** Capabilities are counted
through the `Skill -> Project` relation and link to `?work=`; languages are
counted from `Project.language` and link to `?lang=`, because that is the field
the language filter matches. Counting languages through the relation instead
would have printed a number the link then contradicted — a "Python" skill with
no M2M rows would show 0 while the link returned five projects. A test pins
this by asserting the relation count is 0 and the displayed count is 1.

**Language links use the filter key, not the display name.** `?lang=C_Sharp`,
not `?lang=C#`, or the link returns nothing.

**Groups with no members are omitted** rather than rendered empty — the same
rule the capability filter follows.

**The count is decorative to a screen reader.** The numeral carries
`aria-hidden`, with an `sr-only` "— 3 projects" beside it, so the pill does not
read as "Python 3".

**The home page went from 4 queries to 5**, the extra being a single pass over
`Project.language`. As in Phase 2, the test was strengthened rather than
renumbered: it now asserts the count is identical after adding jobs, projects
and skills.

### Known content mismatch

The production skill **"M (Mumps)"** does not match the `ProgramLanguage` value
**"Mumps"**, so it renders with no count and no link while every other language
links through. Renaming the skill to "Mumps" fixes it. Not worth fuzzy matching
in code — that would be guessing at which near-misses are the same thing.

---

## Availability indicator

The green dot beside "Open to Solution Architect..." now pulses: a ring expands
out of it and fades, on a 2.6s loop.

Animates `transform` and `opacity` only, both of which composite on the GPU.
Animating the `box-shadow` spread would have produced the same picture while
repainting the card on every frame.

The ring's base state is transparent, so the `prefers-reduced-motion` rule that
stops the animation leaves the dot looking exactly as it did before — no
half-finished frame left on screen.

---

## Phase 5 — Content

Not code. Listed so the plan is honest about what the code cannot do.

- [ ] Assign capabilities to all nine existing projects
- [ ] Add the missing ERP / B2B integration project
- [ ] Choose which three or four projects are featured
- [ ] Backfill project dates
- [ ] Add outcome lines to professional projects
- [ ] Retitle the underselling ones
- [ ] Retire or archive the weakest personal projects
- [ ] Add TypeScript, and the architecture vocabulary, to Skills

Phase 2's headings only pay off once Phase 5 fills them. An empty "Systems
Integration" group is worse than no group at all — it points straight at the
gap. Hence the hide-when-empty rule.
