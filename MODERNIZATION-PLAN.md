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

Migrations are now tracked in git (`/main/migrations/` was removed from `.gitignore`). The app had a
recorded migration history whose files no longer existed, so the local database needed repairing:

1. `main/migrations/0001_initial.py` was regenerated from the current models, minus the slug field.
2. The stale `main` rows in `django_migrations` were deleted.
3. `manage.py migrate main --fake-initial` marked 0001 applied without re-creating existing tables.
4. `0002_project_slug.py` added the field, backfilled slugs, then applied the unique constraint.

**The production database on PythonAnywhere needs the same repair before `migrate` will work.** Back
up `db.sqlite3` first, then run steps 2-4 there. Step 2 is:
`DELETE FROM django_migrations WHERE app='main';`

A follow-up fix landed the same day. The new markup depends on CSS classes added to
`materialize.css` at an unchanged URL, so any browser holding a cached copy rendered the new HTML
without the new rules: the screen-reader-only `h1` showed as a duplicate page title and the
collapsible section headers rendered at their default `h2` size. Two changes address it:

- `main/templatetags/versioned_static.py` appends each static file's modification time as `?v=`,
  so the URL changes whenever the file does. `header.html` uses it for the stylesheet and both
  scripts. Without this, every returning visitor would have hit the same broken page after deploy.
- `.collapsible > li.active > .collapsible-body { display: block; }` opens the default section from
  first paint rather than only once Materialize's JS initialises. Materialize's inline styles still
  win once a visitor clicks.

Note: adding a new `templatetags` package requires a server restart. Django's autoreloader does not
pick up a newly created tag library, and templates using it raise `TemplateSyntaxError` until then.

Also outstanding from this phase:

- [ ] Replace the Open Graph image. It currently points at `jasonpeck.png` (300x450 portrait);
      `og:image` wants roughly 1200x630 for LinkedIn and Slack previews to render properly.
- [ ] `manage.py check --deploy` reports pre-existing security warnings unrelated to this phase:
      no `SECURE_HSTS_SECONDS`, no `SECURE_SSL_REDIRECT`, a short `SECRET_KEY`, and neither
      `SESSION_COOKIE_SECURE` nor `CSRF_COOKIE_SECURE` set. Worth folding into Phase 2.
- [ ] The bio card on the home page keeps its horizontal layout at 375px, squeezing the text into a
      narrow column. Pre-existing, but only visible now that the viewport is honest. Phase 3 rebuilds
      the card system and will resolve it.
- [ ] The portfolio filter buttons truncate at 375px (`.filter-container` is `width: 50%`).
      Pre-existing; Phase 4 rebuilds the filter UI.

## Phase 2 — Dependency modernization

- [ ] Django 4.0.6 → 5.2 LTS (review release notes for breaking changes)
- [ ] Replace Universal Analytics with GA4, or switch to Plausible/Fathom
- [ ] Extract custom CSS from `materialize.css:1-105` into its own `custom.css`
- [ ] Convert photos to WebP/AVIF with `srcset` and correct `width`/`height`
- [ ] Delete unreferenced `parallax.png` (4.1 MB) and `profile.jpg`
- [ ] Add `loading="lazy"` to portfolio card images
- [ ] Add `defer` to script tags; scope reCAPTCHA loading to `/contact` only
- [ ] Fix the N+1 in `index()` with `prefetch_related`

## Phase 3 — Visual redesign (Materialize removal)

Decided approach: custom CSS, no framework.

- [ ] Define design tokens as CSS custom properties — keep the existing palette
      (`#2A1B3D` / `#44318D` / `#D83F87` / `#A4B3B6`), fix the sub-4.5:1 pairs
- [ ] Build a modular type scale and spacing rhythm
- [ ] Rebuild components in custom CSS: navbar, card, collapsible, dropdown, toast
- [ ] Rewrite the mobile nav as vanilla JS (`<dialog>` or a CSS-driven drawer)
- [ ] Replace the carousel with a static hero, or drop it
- [ ] Uniform card heights with `object-fit: cover` imagery
- [ ] Real `:focus-visible` states throughout
- [ ] Dark mode via `prefers-color-scheme`
- [ ] Remove jQuery, Materialize CSS and Materialize JS entirely
- [ ] Verify at 375px, 768px, 1440px in both color schemes

## Phase 4 — Portfolio UX rebuild

- [ ] OR semantics within a filter category; AND across categories
- [ ] Active-filter chips with individual remove and a clear-all control
- [ ] Result count ("Showing 5 of 8 projects")
- [ ] Empty state with a clear-filters action
- [ ] Sync filter state to the URL so filtered views are shareable
- [ ] CSS transitions in place of jQuery animations
- [ ] Rewrite `filterCards.js` as a module — no implicit globals, no `console.log`
- [ ] Reposition the legend so it never overlaps content; add a non-color cue (icon or label)

## Phase 5 — Content and IA

- [ ] Home page headline + tagline + primary CTA above the fold
- [ ] Footer with LinkedIn, GitHub, email
- [ ] Resume download
- [ ] Fix the dual "Present" — set Epic Systems' end date
- [ ] Fix "leading me to experimented with" → "experiment with"
- [ ] Restructure project pages as case studies: problem → approach → outcome
- [ ] Decouple Personal/Professional from `githubLink` presence — add an explicit model field
- [ ] Either implement `project_html.html` or remove the `html_project` code path
