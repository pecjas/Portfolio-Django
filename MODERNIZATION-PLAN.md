# Portfolio Modernization Plan

Audit date: 2026-09-16
Audited against: https://stagingportfolio.pythonanywhere.com/ (live) + local `bugFixes` branch

**Decision on record:** Drop Materialize entirely in Phase 3, replacing it with custom modern CSS
and vanilla JS. jQuery goes with it.

**Status legend:** `[ ]` not started · `[~]` in progress · `[x]` done

---

## How to resume this work

Each phase below is independently shippable. Work top to bottom — Phase 1 is a prerequisite for
everything else, because the redesign cannot be built reliably on a page rendering in quirks mode.
Check items off as they land. Do not start Phase 3 before Phases 1 and 2 are complete.

---

## Findings summary

Everything below was verified either in the live DOM or by reading the source. Items are grouped by
the phase that addresses them.

### Critical: the page renders in quirks mode on every browser

- `document.compatMode === "BackCompat"` — there is no `<!DOCTYPE html>` in `main/templates/main/header.html`.
  Browsers apply the pre-2000 box model sitewide.
- No `<meta name="viewport">`. At a 375x812 phone viewport, `window.innerWidth` reports **981px** —
  phones render the full desktop layout zoomed out. Body text lands at ~40% of intended size.
- No `<html>` wrapper element; `<head>` and `<body>` are siblings.
- No `lang="en"`.
- `<script>M.AutoInit();</script>` sits outside `</body>`.

### Stack currency

| Dependency | Version | Status |
|---|---|---|
| Materialize CSS | 1.0.0 | Last release Dec 2018; unmaintained |
| jQuery | 3.4.1 | 2019; known prototype-pollution CVEs |
| Django | 4.0.6 | EOL since April 2023 |
| Google Analytics | `UA-162877529-2` | Universal Analytics — stopped collecting data July 2023 |

Custom CSS is prepended into the vendor file at `main/static/main/css/materialize.css:1-105`, so the
vendor build cannot be updated without re-applying the patch by hand.

### Accessibility

- All 8 images sitewide have no `alt` attribute.
- No `<h1>` anywhere. Home page headings start at `<h4>`; the portfolio page has zero headings.
- Carousel slides are empty `<a>` elements — keyboard-focusable, no label, no destination.
- The Professional/Personal legend conveys meaning by color alone (WCAG 1.4.1 failure).
- Contrast: white on hot-pink `#D83F87` measures **4.22:1** at font-weight 300 (card titles), below
  the 4.5:1 AA threshold. Nav `#A4B3B6` on `#44318D` measures 4.69:1 — barely passing.
- `main/templates/main/contact.html:8-11` loops `{{ field }}` without `{{ field.errors }}`, so form
  validation failures redisplay the page with no explanation.

### Portfolio filtering (verified by live testing)

- Filters AND within a category instead of OR: Python alone returns 5 projects; adding Mumps drops
  the result to **1**. Selecting more languages should broaden the set, not narrow it.
- No empty state: filtering to C# (zero matches) hides all 8 cards, leaving a blank page.
- No active-filter chips, no clear-all, no result count, no URL state (filtered views are not shareable).
- Transitions use jQuery `.hide(1000)` / `.show(1000)` — one full second per card.
- The legend is `position: fixed` at 150px and overlaps content at narrow widths.
- Cards are ragged-height; images are letterboxed in fixed 280px boxes leaving large flat color bands.
- `main/static/main/js/filterCards.js` leaks four implicit globals (`typeOptions`, `elementID`,
  `filterType`, `filterSelection`) and ships a `console.log`.

### URLs, SEO, sharing

- Project URLs are `/project/?id=Portfolio%20Website` — the title passed as a query parameter.
- `main/views.py:84` uses `Project.objects.get(title=request_id)`; a missing or renamed title raises
  `DoesNotExist` and returns a **500, not a 404**. No custom 404/500 templates exist.
- Every page shares the same `<title>` and meta description.
- No Open Graph or Twitter card tags — shared links render bare on LinkedIn and Slack.
- No `sitemap.xml`, `robots.txt`, or canonical tags.
- Nav links hardcode `/portfolio` while the URLconf declares `portfolio/`, so **every nav click costs
  a 301 redirect**. Templates should use `{% url %}`.

### Performance

- 172 KB of unminified Materialize CSS, plus jQuery, Materialize JS and reCAPTCHA — all
  render-blocking in `<head>`, none deferred. reCAPTCHA loads on every page though only `/contact`
  needs it.
- Hero images are PNGs: `Developer.png` 500 KB, `Jason.png` 448 KB, `jasonpeck.png` 172 KB. No
  WebP/AVIF, no `srcset`.
- No `loading="lazy"` on portfolio card images.
- `parallax.png` (**4.1 MB**) and `profile.jpg` are committed but referenced nowhere.
- N+1 query in `index()` — one `JobDetail` query per job (`main/views.py:14-16`).

### Content and information architecture

- No LinkedIn link, no GitHub profile link, no resume download, no footer. The email address appears
  only inside an error message string.
- Two jobs both display "Present": Epic Systems (June 2017 – Present) and Esker (April 2025 – Present).
- Typo in the home bio: "leading me to experimented with" → "experiment with".
- Home page opens with an autoplaying name banner; no headline, tagline, or call to action above the fold.
- "Personal vs Professional" is derived from whether `githubLink` is set (`main/views.py:41-44`),
  conflating two independent facts.

### Housekeeping

- `requirements.txt` is **UTF-16 encoded** (from `pip freeze >` in PowerShell); `pip install -r` fails on it.
- `main/templates/main/project_html.html` is an empty stub — projects with `html_project=True` render
  a title and description and nothing else.
- `main/tests.py` is empty. Worth seeding before the Phase 3 refactor.

---

## Phase 1 — Foundation

**Status: complete (2026-09-16).** Verified locally at 375px and 1280px; 12 tests passing.

Small, high-impact, low visual risk. Desktop appearance barely changes; mobile improves dramatically.

- [x] Add `<!DOCTYPE html>`, `<html lang="en">`, proper `<head>`/`<body>` nesting to `header.html`
- [x] Add `<meta name="viewport" content="width=device-width, initial-scale=1">`
- [x] Move `M.AutoInit()` inside `</body>`
- [x] Add `alt` text to all 8 images
- [x] Establish heading hierarchy: one `<h1>` per page, `<h2>`/`<h3>` for sections
- [x] Give carousel slides accessible names, or make them non-focusable if decorative
- [x] Render `{{ field.errors }}` and `{{ form.non_field_errors }}` in `contact.html`
- [x] Replace hardcoded paths with `{% url %}` tags (removes the 301 on every nav click)
- [x] Add `SlugField` to `Project`; migrate to `/projects/<slug>/`; use `get_object_or_404`
- [x] Add custom `404.html` and `500.html`
- [x] Per-page `<title>` and meta description via a template block
- [x] Add Open Graph + Twitter card tags with a share image
- [x] Re-save `requirements.txt` as UTF-8
- [x] Seed `main/tests.py` with smoke tests for all four views

### Deployment notes for Phase 1

Migrations are now tracked in git (`/main/migrations/` was removed from `.gitignore`).

**Correction (2026-09-16):** an earlier version of this section prescribed deleting production's
`django_migrations` rows and running `migrate --fake-initial`. That is *not* required, and the
instruction has been withdrawn. It was tested against a rebuilt copy of production and a plain
`migrate` is sufficient:

```bash
python manage.py migrate
```

Why it works: production already has a migration record named `0001_initial`. The regenerated file
carries that same name, so Django treats it as applied and skips it. The eight other orphaned
records name files that no longer exist; Django builds its graph from the files on disk and ignores
records it cannot match. `0002_project_slug` then applies for real, backfilling a slug for every
existing project from its own title.

Verified by simulation on a production-shaped database (tables without `slug`, the nine orphaned
records, the real project rows): plain `migrate` applied `0002_project_slug` cleanly and backfilled
8 of 8 projects.

**Phase 1 does not need to ship on its own.** The same simulation, run against an untouched
production copy with a second migration stacked on top, applied both in a single `migrate` — Phase 1
and any later phase can deploy together. Migrations are ordered by their dependency chain, not by
when they are deployed, so batching them changes nothing.

One caveat worth knowing: Django decides `0001_initial` is applied from its *name*, and never checks
that production's tables actually match what that file declares. If production's schema has drifted
from the models, that difference would pass unnoticed. `makemigrations --check --dry-run` reports no
changes locally, so models and migrations agree here. After deploying, confirm the same on the
server:

```bash
python manage.py makemigrations --check --dry-run
```

"No changes detected" means the schema, models and migration files are consistent. Back up
`db.sqlite3` before migrating regardless — `0002` rewrites every row in `main_project`.

Note: adding a new `templatetags` package requires a server restart. Django's autoreloader does not
pick up a newly created tag library, and templates using it raise `TemplateSyntaxError` until then.

Also outstanding from this phase:

- [x] Replace the Open Graph image — now a dedicated 1200x630 card, see *Share card* below.
- [~] `manage.py check --deploy` reported no `SECURE_HSTS_SECONDS`, no `SECURE_SSL_REDIRECT`,
      a short `SECRET_KEY`, and neither `SESSION_COOKIE_SECURE` nor `CSRF_COOKIE_SECURE`.
      All but the `SECRET_KEY` are fixed; that one needs a rotated value only Jason can set.
- [x] The bio card on the home page kept its horizontal layout at 375px. Below 600px it now stacks:
      photo centred on top, text full width underneath.
- [x] The portfolio filter buttons truncated at 375px. `.filter-container` now drops its `width: 50%`
      below 600px and uses side margins instead, so both labels fit.
- [x] A tall gap sat between the banner and the first card on phones. Materialize ships
      `.carousel.carousel-slider { min-height: 165px }`, a floor meant for full-screen sliders; the
      banner artwork is only 215px tall, so below roughly 1535px wide the box floored at 165px and
      left empty space. The carousel now derives its height from the artwork's 2000:215 aspect ratio
      with `min-height: 0`, so it is exactly as tall as the image at every width.
- [ ] The bio card is still cramped at tablet widths: `col s12 m7` gives it 7/12 of the container
      from 601px up, so the text column is roughly 200px at 768px. Not addressed here because it
      needs a layout decision rather than a breakpoint. Phase 3.

Note for future custom rules: the custom block sits at the *top* of `materialize.css`, so a custom
rule with the same specificity as a vendor rule loses on source order. Overriding a vendor
declaration currently needs `!important`. Phase 2's extraction into a separate stylesheet loaded
after Materialize removes that constraint.

## Phase 2 — Dependency modernization

**Status: complete except the GA4 swap (2026-09-16).** 16 tests passing; verified at 375px and 1280px.

- [x] Django 4.0.6 → 5.2.17 LTS
- [ ] Replace Universal Analytics with GA4 — **needs a GA4 property from you, see below**
- [x] Extract custom CSS from `materialize.css` into its own `custom.css`
- [x] Convert photos to WebP with `srcset` and correct `width`/`height`
- [x] Delete unreferenced `parallax.png` (4.1 MB) and `profile.jpg`
- [x] Add `loading="lazy"` to portfolio card images
- [x] Add `defer` to script tags; reCAPTCHA now also `async defer` and scoped to `/contact`
- [x] Fix the N+1 in `index()` with `prefetch_related`
- [x] Security settings carried over from Phase 1's leftovers

### Django 5.2 upgrade

Only one incompatibility existed in the code: `USE_L10N`, removed in Django 5.0. Localised
formatting is unconditional now, so the setting was simply deleted.

`MainConfig.default_auto_field` is pinned to `AutoField`, which silences the six `models.W042`
warnings without a schema change. Switching to `BigAutoField` would rebuild every table for no
benefit at this row count; revisit only if a table approaches 2 billion rows.

After upgrading: `check` is clean, `makemigrations --check` reports no changes, all tests pass, and
every page renders including the legacy `/project/?id=` redirect.

### Images

| File | Before (PNG) | After (WebP) | Saving |
|---|---|---|---|
| `Jason.png` | 447 KB | 9.6 KB @800w · 15.6 KB @1200w · 27.7 KB @2000w | 94-98% |
| `Developer.png` | 499 KB | 10.9 KB @800w · 18.3 KB @1200w · 32.8 KB @2000w | 94-98% |
| `jasonpeck.png` | 171 KB | 11.7 KB | 93% |

The PNGs are kept as `<picture>` fallbacks and never fetched by a browser that supports WebP.
Measured on the home page at 375px: **21 KB of images, down from roughly 1.1 MB**. Verified that a
cold load on a 375px @2x phone selects the 800w variant.

`width` and `height` are set on every image so the browser reserves space before the file arrives.
Project detail images take theirs from the `ProjectImage.width` / `.height` model fields.

Portfolio cards lazy-load from the fourth card onward — the first row stays eager so the largest
visible image is not delayed.

### Deferred scripts

jQuery, Materialize and both page scripts now carry `defer`, and jQuery was reordered ahead of
Materialize so Materialize's jQuery bridge is built. `defer` preserves execution order but moves it
after parsing, so three inline initialisers that used to run mid-parse were wrapped in
`DOMContentLoaded`: the `M.AutoInit()` call, the toast calls in `messages.html`, and the filter and
legend setup in `portfolio.html`. The carousel's `$(document).ready(...)` became a plain
`DOMContentLoaded` listener, since `$` is no longer defined when that script is parsed.

Verified after the change: carousel and collapsible initialise, filters still narrow 8 projects to
5, the legend still positions, and the console is clean.

### Security settings

`Portfolio/settings.py` now applies production-only hardening under `if not DEBUG:`. Django's
`check --deploy` drops from 6 warnings to 3 in a simulated production run.

`SECURE_PROXY_SSL_HEADER` is set alongside `SECURE_SSL_REDIRECT`. Without it, PythonAnywhere's proxy
terminates TLS and Django sees plain HTTP on every request, producing an infinite redirect loop.

`SECURE_HSTS_SECONDS` is deliberately **3600, not a year**. HSTS is remembered by each visitor's
browser for the full duration and cannot be withdrawn, so a mistake is expensive. Raise it once
HTTPS is confirmed stable in production.

The three remaining warnings are deliberate:

- `W005` HSTS `includeSubDomains` — off; there are no subdomains and enabling it adds risk.
- `W021` HSTS preload — off; preload-list submission is effectively irreversible.
- `W009` `SECRET_KEY` — **needs your action.** The key in `env.py` is under 50 characters. Generate a
  new one and replace it in `env.py` on both machines. This logs out any active admin session, which
  is the only consequence here:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Outstanding: the GA4 swap

No code change is needed. `main/context_processors.py` injects whatever HTML sits in
`env.google_analytics_head_info`, so switching analytics is purely an `env.py` edit.

Your current value holds the Universal Analytics snippet for `UA-162877529-2`, a property that
stopped collecting data in July 2023. To finish this item:

1. Create a GA4 property at analytics.google.com and copy its Measurement ID (`G-XXXXXXXXXX`).
2. Replace the value of `google_analytics_head_info` in `env.py` with the GA4 snippet Google
   provides, substituting your own ID:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

3. Do the same in `env.py` on PythonAnywhere.

Worth doing before the Phase 3 redesign, so there is a baseline to compare against.

## Phase 3 — Visual redesign (Materialize removal)

**Status: complete (2026-09-16).** 18 tests passing; verified at 375px, 768px and 1280px in both
light and dark, with zero contrast failures on every page in both schemes.

- [x] Define design tokens as CSS custom properties, fixing the sub-4.5:1 pairs
- [x] Build a modular type scale and spacing rhythm
- [x] Rebuild components in custom CSS: navbar, card, accordion, menu, toast
- [x] Rewrite the mobile nav as vanilla JS on `<dialog>`
- [x] Replace the carousel with a CSS crossfade hero
- [x] Uniform card heights with `object-fit: cover` imagery
- [x] Real `:focus-visible` states throughout
- [x] Dark mode via `prefers-color-scheme`
- [x] Remove jQuery, Materialize CSS and Materialize JS entirely

### What replaced what

| Removed | Replaced by |
|---|---|
| `materialize.css` + `.map` (267 KB) | `app.css` (~20 KB) |
| `custom.css` | folded into `app.css` |
| Materialize JS + jQuery (CDN) | `app.js` (~4 KB) |
| `portfolioLegend.js` | CSS; the legend is in normal flow |
| Material Icons webfont | inline SVG sprite, 11 symbols |
| Materialize collapsible | native `<details>` / `<summary>` |
| Materialize sidenav | native `<dialog>` |
| Materialize materialbox | native `<dialog>` lightbox |
| Materialize toast | `app.js`, from server-rendered nodes |
| Materialize carousel | two-frame CSS crossfade |
| `col s12 m6 l4` grid | `grid-template-columns: repeat(auto-fill, minmax(...))` |

Total CSS + JS is now **36 KB on disk**, against roughly 270 KB of stylesheet alone before, plus two
CDN requests for jQuery and Materialize that no longer happen.

### Palette

The brand colours are kept. Two were measured failing and were split rather than replaced:

- `#D83F87` stays as the decorative accent (borders, swatches, top rules).
- `--accent-deep` `#C9306F` carries white text (5.08:1, was 4.22:1).
- `--accent-text` `#E86AA5` is the accent as link text on dark (5.32:1, was 3.77:1).

Dark mode swaps the page and surface tokens only; component rules are written against tokens, so
nothing else changed.

### Progressive enhancement

The accordion is a native `<details>`, so the default section is expanded at first paint with no
script. Nav items are plain links. Project cards are static markup. `app.js` adds the drawer, the
filter menus, toasts and the lightbox, and the page is usable without any of them.

### Three bugs found and fixed during the rebuild

1. **Multi-line `{# #}` comments rendered literally.** Django's `{# #}` is single-line only; a
   comment spanning lines is emitted verbatim into the HTML. Three had shipped into the templates.
   Now `{% comment %}` blocks, with a test asserting no `{#` reaches the response.
2. **`svg { display: block }` un-hid the icon sprite.** Author rules beat the user-agent sheet
   regardless of specificity, so the reset overrode `[hidden] { display: none }` and the sprite took
   150 px of layout above the header. Fixed with an explicit `[hidden]` rule.
3. **Ghost buttons were near-invisible on the white filter bar**, having pinned a light text colour
   that only read on dark surfaces. They now inherit colour from context.

### Filtering

Rewritten as a module. The Phase 4 items on OR semantics, chips, count, empty state and URL state
came along with it, since the old file was being deleted anyway — see Phase 4 below.

### Desktop centring pass (follow-up)

Four alignment complaints after the rebuild, all from constrained-width blocks sitting against the
left edge of a much wider container. Measured rather than eyeballed — the container itself was
already centred; a first reading suggested otherwise only because `window.innerWidth` counts the
15px scrollbar and `document.documentElement.clientWidth` does not.

- Profile card (832px in a 1152px container) — `margin-inline: auto`.
- Contact page — heading, lede and form now share one centred `.column`, so they align with each
  other instead of each taking its own width from the left edge.
- Project detail page — same `.column` treatment; screenshots get a wider `.gallery` since they are
  the point of that page.
- Project grid — the last row of a `repeat(auto-fill, ...)` grid hangs left, because the empty
  tracks stay in place. Switched to a wrapping flex row with `justify-content: center`, so a short
  final row centres under the ones above. Card heights stay uniform per row.
- Legend — was a full-width bar holding 174px of content and no explanation of what the swatches
  meant. Now a `fit-content` pill, centred, reading "Card color · Professional · Personal".

### URL sync moved off the interaction path (follow-up)

`Cannot read properties of undefined (reading 'startTime')` in `et.reportAllChanges`, thrown from a
`VM`-numbered script, appeared while toggling filters. It reproduces in Incognito, so it is not an
extension — `reportAllChanges` is the web-vitals API, which Chrome DevTools injects as part of its
live performance metrics.

**Cause, confirmed by bisection** (a switch was added to disable the History write; errors with it
on, none with it off): Chrome's soft-navigation heuristics flag a single trusted interaction that
both changes the URL via the History API and mutates the DOM. A filter click did exactly that.
DevTools' instrumentation of that path is what throws.

Two notes on how this was found, because the first two attempts were wrong:

- Synthetic `element.click()` cannot reproduce it. Chrome's heuristics and INP measurement respond
  only to *trusted* input, so every "no errors in a clean browser" result was meaningless. Later
  runs used real input through the browser's own pipeline.
- Debouncing the write did not help. Interaction context propagates through chained timers, so a
  `setTimeout` scheduled from the handler is still attributed to the click.

**Fix.** A click now only raises a flag. A reconciler started at page load — not a descendant of any
interaction — notices the flag and writes the URL. The address bar behaves identically; there is no
interaction for the heuristic to attribute the write to. Verified with real clicks:
`writeHappenedInsideClickTask: false`, URL still tracks filters, shared links still restore, clear-all
still empties the query string.

`SYNC_URL_TO_FILTERS` remains at the top of the file as an escape hatch.

### Card kind colours made prominent (follow-up)

The Professional/Personal distinction was carried by a 4px top border in `#44318D`, which measures
**1.56:1 against the dark card surface** — below the 3:1 WCAG 1.4.11 asks of non-text UI, and in
practice invisible. Each kind now has two colours, because one cannot do both jobs:

| | band / border (`--kind`) | tag fill (`--kind-fill`) |
|---|---|---|
| Personal | `#E84E96` — 5.96:1 on the card | `#C9306F` — 5.08:1 vs white text |
| Professional | `#7C6BE0` — 5.03:1 on the card | `#44318D` — 10.15:1 vs white text |

Applied as an 8px top band, a 2px border, and a 12% tint of the kind colour mixed into the card
surface. The kind tag is filled rather than outlined, so the category is also stated in words — the
two hues are far apart visually but close in luminance, so colour alone would not carry it for
colour-blind readers.

Verified in both schemes: zero contrast failures on the page, body text still 12:1+ on the tinted
surfaces.

### Theme toggle (follow-up)

Dark mode previously followed the OS only. There is now a control in the header cycling
**System → Light → Dark**. Three states rather than two, because with only a light/dark switch there
is no way back to following the OS once a choice has been made.

- The choice is stored in `localStorage` and cleared again when the cycle returns to System.
- A small **inline, synchronous** script in `<head>` re-applies a stored choice before first paint.
  A deferred or end-of-body script would run after the first paint and flash the light palette at
  anyone who chose dark. A test asserts this script stays in `<head>`, ahead of `<body>`, with no
  `defer`, `async` or `src`.
- While in System mode the page tracks OS changes live via `matchMedia`, without a reload.
- `<meta name="theme-color">` is updated to match, so mobile browser chrome follows the page.
- The button is rendered `hidden` and revealed by `app.js`, so it is never a dead control without
  JavaScript. A test covers that too.

The dark palette now appears in two rules — `@media (prefers-color-scheme: dark)` scoped to
`:root:not([data-theme="light"])`, and `:root[data-theme="dark"]`. They must be kept identical; the
comment above them says so. The alternative, `light-dark()`, would remove the duplication but fails
hard on older browsers, taking the whole palette with it.

Two values that had their own `prefers-color-scheme` blocks (form field borders, error text) became
tokens instead, so they follow the override automatically rather than needing their own rules.

Verified: full cycle in both OS settings, an explicit light choice overriding an OS set to dark and
surviving a reload, zero contrast failures under `[data-theme="dark"]` with the OS on light, and
both header buttons at the 44px touch target on a 375px viewport with no overlap.

### Follow-ups

- [ ] The "Portfolio Website" project description still says *"Materialize was used for the base
      CSS, and custom styling was applied as needed"*. No longer true; update the text in the admin.
- [ ] `project_html.html` remains an empty stub, so a project with `html_project=True` renders a
      title and description only. Still outstanding from the original audit.

## Phase 4 — Portfolio UX rebuild

**Status: complete (2026-09-17).** 22 tests passing; verified at 375px and 1300px in both schemes.

Most of this landed during Phase 3, because the file it lived in was being deleted.

- [x] OR semantics within a filter category; AND across categories (Python + Mumps returns 6, was 1)
- [x] Result count ("Showing 5 of 8 projects")
- [x] Empty state with a clear-filters action
- [x] Sync filter state to the URL so filtered views are shareable
- [x] CSS transitions in place of jQuery animations
- [x] Rewrite `filterCards.js` as a module — no implicit globals, no `console.log`
- [x] Reposition the legend so it never overlaps content, and label each swatch in text
- [x] Active-filter chips with individual remove
- [x] Keyboard support inside the filter menus

### Active-filter chips

A row inside the filter panel lists every active filter as a removable pill. The menu buttons
already carried a pressed state, but only while their menu is open — the chips are the only
always-visible account of what is being filtered.

Labels come from the menu buttons themselves, read once at init into a lookup. That keeps display
names in the template rather than duplicating the `ProgramLanguage` enum in JavaScript, so a chip
reads "C#" rather than the `C_Sharp` filter key.

Removing a chip moves focus to whichever chip takes its place, or to Clear filters when the row
empties, rather than dropping focus to `<body>` and losing a keyboard user's position.

Chips are 32px tall, which clears the WCAG 2.5.8 minimum of 24px. Under `(pointer: coarse)` they
grow to 44px, since a small dismiss target is awkward with a finger.

### Filter menu keyboard support

The menus are disclosures containing toggle buttons, not ARIA menus — `aria-pressed` is the right
state for a filter, and `menuitem` does not carry it. So the buttons stay native and the keys are a
convenience layer on top:

| Key | Behaviour |
|---|---|
| ArrowDown / ArrowUp on the trigger | opens the panel, focuses first / last option |
| ArrowDown / ArrowUp in the panel | moves focus, wrapping at both ends |
| Home / End | first / last option |
| A printable character | jumps to the next option starting with it, cycling |
| Escape | closes and returns focus to the trigger |
| Tab | closes the panel rather than leaving it open behind the focus |

Verified with real key events: ArrowDown from the Language trigger opens and lands on "C#";
ArrowUp from the first option wraps to "Unspecified"; "p" then "p" moves PHP → PowerShell; Escape
restores focus to the trigger with `aria-expanded="false"`; Tab closes the panel behind it.

### Remaining

Nothing outstanding for this phase.

## Phase 5 — Content and IA

**Status: code complete (2026-09-17); several items need content or assets only Jason has.**
26 tests passing; verified at 375px and 1300px in both schemes.

- [x] Home page opener: tagline + primary CTAs, merged into the profile card *(copy is a draft)*
- [x] Footer with GitHub, Contact and a direct email link; LinkedIn wired, awaiting a URL
- [~] Resume download — mechanism built, awaiting the PDF
- [ ] Fix the dual "Present" — production data, needs Epic Systems' end date
- [x] Fix "leading me to experimented with" → "experiment with"
- [x] ~~Restructure project pages as case studies~~ — **declined**, no structured fields wanted
- [x] Decouple Personal/Professional from `githubLink` presence
- [x] Remove the `html_project` code path

### Personal vs Professional is now a real field

`Project.is_personal` replaces the old inference from `githubLink`, which conflated two unrelated
facts: a professional project can have public source, and a personal one need not. Migration
`0003_project_is_personal` seeds it from the old heuristic, so nothing changed on the page, then
drops `html_project`.

`html_project` was dead: `False` on every row, and the template it selected — `project_html.html` —
was an empty stub, so any project using it would have rendered a title and description and nothing
else. Removing it is a schema change, reversible by rolling the migration back.

The field is editable straight from the admin list (`list_editable`), with a filter, so
recategorising a few projects does not mean opening each one.

### One opener, not two

The first pass left two competing intros: a centred tagline block and the older profile card
underneath. They have been merged — photo on the left, the current-role tagline, a supporting line
about personal projects, then the calls to action, all in a single card. The older bio paragraph is
gone; its accurate parts live in the tagline and its "visit the portfolio page" link is now the
"View my work" button.

Moving the buttons inside the card exposed a bug worth noting: `.card a { color: var(--accent-text) }`
applied to them, so the accent button rendered accent-coloured text on an accent background —
**1.70:1**. Both link rules are now `a:not(.btn)`, and the buttons are back to 5.08:1 and 10.15:1.
Caught by the contrast sweep, not by eye.

### Optional assets render only when present

A `static_if_exists` template tag returns a static URL or an empty string, so the CV links on the
home page and in the footer appear only once `main/static/main/files/jason-peck-resume.pdf` exists.
No dead link in the meantime. `LINKEDIN_URL` in settings behaves the same way for the footer link.

### Outstanding, and what each needs

| Item | Needs |
|---|---|
| Tagline copy | Jason's own wording; the draft is marked as such in the template |
| LinkedIn link | the profile URL, into `LINKEDIN_URL` in `Portfolio/settings.py` |
| CV download | drop the PDF at `main/static/main/files/jason-peck-resume.pdf` |
| Dual "Present" | set Epic Systems' end date in the production admin |
| Project copy | the Portfolio Website description still credits Materialize |

All other rows in this table have since been filled: the tagline is Jason's own wording plus an
availability line, `LINKEDIN_URL` is set, and the CV is in place.

## Pre-deployment pass (2026-09-17)

**Status: complete. 33 tests passing.**

### Portrait

A new `jasonpeck.jpg` arrived at 3094x4000 and 469 KB, for a slot that is painted 247px wide on
phones and 297px on desktop. It now ships as a WebP ladder (300w / 600w / 900w) with a 600w JPEG
fallback; desktop pulls 10.8 KB, down from 469 KB.

Two things broke in passing and were fixed:

- `jasonpeck.png` was still the `og:image` and the `<picture>` fallback, so both 404'd once the
  PNG was replaced by a JPG.
- Declaring the fallback's true `600x776` changed the layout. The photo sits in an `auto` grid
  column, so its intrinsic width is a sizing input; the column claimed more, then got squeezed,
  and the photo rendered 99px wide. Declared at `300x388` instead — the old scale, the new ratio.

The full-resolution original is kept at `source-images/jasonpeck-original.jpg`, outside the static
tree so it is neither served nor collected.

### Share card

`og:image` pointed at the 3:4 portrait, which LinkedIn and Slack letterbox into a strip that loses
the face. Replaced with `og-card.jpg`, a 1200x630 card in the same space theme as the hero banners:
the palette gradient and starfield on the left with the name and role, the portrait feathered in on
the right. 75 KB. `og:image:width`/`height`/`alt` are declared so the preview reserves the right box.

`SocialCardTests` now asserts that every share image resolves through the staticfiles finders and
that the declared dimensions match the file and are landscape. Verified by mutation: pointing
`og:image` at a missing file fails the suite.

### Profile card

- The three text segments had **no** gap. `.profile-card__body p { margin: 0 }` is (0,1,1) and the
  spacing rule was a universal child selector at (0,1,0), so it lost outright. Fixed with a
  `p + p` branch at matching specificity, set to `var(--space-5)`.
- The three CTAs wrapped to two rows, short by 8.8px. The card's `max-width` went 52rem to 56rem,
  which gives the button row ~55px of headroom and leaves the text at a 63-character measure.
  Holds down to roughly 920px wide, below which the buttons wrap again.

### Housekeeping

- Deleted the superseded `Jason.*` and `Developer.*` banner files — 8 files, 1.05 MB, unreferenced
  since the hero moved to `banner-name.*` / `banner-role.*`.
- `makemigrations --check` is clean; no model changes are unmigrated.

### Still outstanding at deploy time

| Item | Needs | Blocking? |
|---|---|---|
| `SECRET_KEY` under 50 chars | a rotated value in `env.py`, both local and on PythonAnywhere | no, but do it |
| Dual "Present" | Epic Systems' end date in the production admin | no |
| Portfolio Website copy | drop the Materialize credit, add AI / Claude Code | no |
| GA4 swap | a GA4 property, then an `env.py` edit | no, UA stopped collecting in 2023 |
| `env.py` handling | deferred by Jason | no |
