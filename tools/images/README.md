# Image generators

Deterministic Pillow scripts that produce every generated image on the site.
They share a fixed seed, so re-running one is a no-op in git unless you have
changed the code — which makes them safe to run at any time to check output.

Run them from anywhere; paths resolve from the repo root.

```bash
.venv/Scripts/python.exe tools/images/make_banner.py
.venv/Scripts/python.exe tools/images/make_portrait.py
.venv/Scripts/python.exe tools/images/make_og.py
.venv/Scripts/python.exe tools/images/make_favicon.py
```

| Script | Produces | Used by |
|---|---|---|
| `make_banner.py` | `banner-name.*`, `banner-role.*` — 2000x215, PNG + 800/1200/2000w WebP | the crossfading hero on the home page |
| `make_portrait.py` | `jasonpeck.jpg` + `jasonpeck-{300,600}w.webp` + `jasonpeck.webp` | the profile card photo |
| `make_og.py` | `og-card.jpg` — 1200x630 | `og:image` / `twitter:image` link previews |
| `make_favicon.py` | the whole `favicon/` directory — PNGs, `favicon.ico`, `safari-pinned-tab.svg` | the browser tab, bookmarks, home-screen icons |

`_common.py` holds the palette, the fonts, the seed and the paths. The colours
are copied from the `:root` block in `main/static/main/css/app.css`; if the site
palette changes, update `_common.py` and re-run all four.

`make_favicon.py` also writes `safari-pinned-tab.svg`, whose letterforms are hand-drawn paths rather than traced from the font: Safari renders it as a one-colour silhouette at about 16px, where a geometric J and P read more cleanly than an outline would. The colours declared alongside the icons -- `theme_color` and `background_color` in `site.webmanifest`, `TileColor` in `browserconfig.xml`, and the `mask-icon` and `msapplication-TileColor` values in `main/templates/main/header.html` -- are not generated, so they need changing by hand if the palette moves.

## Inputs

`make_portrait.py` and `make_og.py` read `source-images/jasonpeck-original.jpg`,
the full-resolution photo. That directory sits outside the static tree so the
original is neither served nor collected by `collectstatic`. To swap the photo,
replace that file and re-run both scripts.

The fonts are Segoe UI Light and Segoe UI, by absolute Windows path. On another
OS they fall back to Pillow's built-in bitmap font, which will look wrong —
point `FONT_LIGHT` / `FONT_SEMI` in `_common.py` at real files instead.

## Requirements

Pillow only, and it is already in `requirements.txt` — Django's `ImageField` on
`ProjectImage` depends on it — so a working project venv can run these as-is.
