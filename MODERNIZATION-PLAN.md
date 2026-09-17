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

- [ ] Replace the Open Graph image. It currently points at `jasonpeck.png` (300x450 portrait);
      `og:image` wants roughly 1200x630 for LinkedIn and Slack previews to render properly.
- [ ] `manage.py check --deploy` reports pre-existing security warnings unrelated to this phase:
      no `SECURE_HSTS_SECONDS`, no `SECURE_SSL_REDIRECT`, a short `SECRET_KEY`, and neither
      `SESSION_COOKIE_SECURE` nor `CSRF_COOKIE_SECURE` set. Worth folding into Phase 2.
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
