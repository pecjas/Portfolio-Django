# Image generators

Deterministic Pillow scripts that produce every generated image on the site.
They share a fixed seed, so re-running one is a no-op in git unless you have
changed the code — which makes them safe to run at any time to check output.

Run them from anywhere; paths resolve from the repo root.

```bash
.venv/Scripts/python.exe tools/images/make_banner.py
.venv/Scripts/python.exe tools/images/make_portrait.py
.venv/Scripts/python.exe tools/images/make_og.py
```

| Script | Produces | Used by |
|---|---|---|
| `make_banner.py` | `banner-name.*`, `banner-role.*` — 2000x215, PNG + 800/1200/2000w WebP | the crossfading hero on the home page |
| `make_portrait.py` | `jasonpeck.jpg` + `jasonpeck-{300,600}w.webp` + `jasonpeck.webp` | the profile card photo |
| `make_og.py` | `og-card.jpg` — 1200x630 | `og:image` / `twitter:image` link previews |

`_common.py` holds the palette, the fonts, the seed and the paths. The colours
are copied from the `:root` block in `main/static/main/css/app.css`; if the site
palette changes, update `_common.py` and re-run all three.

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
