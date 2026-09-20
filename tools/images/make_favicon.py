"""Generates the favicon set: the initials JP in the site palette.

One master tile is drawn large and downsampled to each target, because Pillow
does not antialias shapes and a 16px tile drawn directly is unreadable.

The tile is the site's own header in miniature -- the purple wash it uses
behind light text -- with the pink accent as a base edge. Contrast of the
lettering against the ground is 14.7:1 at the dark end of the wash and 9.4:1
at the light end, so the letters hold at 16px where a favicon actually lives.

Two of the outputs are deliberately different:

  apple-touch-icon  square with opaque corners. iOS applies its own rounding
                    and composites transparency against black, so rounded
                    corners here would arrive as black triangles.
  mstile            square as well, because Windows draws it over the tile
                    colour declared in browserconfig.xml.

Run: python tools/images/make_favicon.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont

from _common import ACCENT, IMG_DIR, PURPLE_DEEP, PURPLE_MID, lerp, report

LIGHT = (0xF7, 0xF5, 0xFA)
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"

OUT_DIR = os.path.join(IMG_DIR, "favicon")

MASTER = 1024       # drawn at this size, then downsampled
INITIALS = "JP"

# Fractions of the tile. The letters are set large because two glyphs at 16px
# have about six pixels each to make themselves understood.
FILL = 0.68         # longest side of the letters' ink box
RADIUS = 0.26       # corner radius
EDGE = 0.05         # accent strip along the base
LIFT = 0.025        # letters sit above centre, to balance against the strip


def wash(size):
    """The diagonal purple the site uses behind light text."""
    grad = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(grad)

    # One line per anti-diagonal, so the gradient runs corner to corner.
    for i in range(size * 2):
        draw.line([(i, 0), (0, i)],
                  fill=lerp(PURPLE_MID, PURPLE_DEEP, i / (size * 2 - 1)))

    return grad


def rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * radius), fill=255)
    return mask


def fitted_font(text, size, fill_ratio):
    """The largest size whose ink box fits `fill_ratio` of the tile.

    Measured from the rendered ink rather than the nominal point size, which
    includes ascent and descent the initials do not use.
    """
    target = size * fill_ratio
    low, high = 10, size * 2
    best = ImageFont.truetype(FONT_BOLD, 10)

    while low <= high:
        middle = (low + high) // 2
        font = ImageFont.truetype(FONT_BOLD, middle)
        left, top, right, bottom = font.getbbox(text)

        if max(right - left, bottom - top) <= target:
            best, low = font, middle + 1
        else:
            high = middle - 1

    return best


def tile(size, *, radius=RADIUS, edge=EDGE):
    """The icon at `size`, with transparent corners unless radius is 0."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = rounded_mask(size, radius) if radius else None
    img.paste(wash(size), (0, 0), mask)

    if edge:
        height = max(1, round(size * edge))
        strip = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(strip).rectangle(
            [0, size - height, size, size], fill=ACCENT + (255,))

        if mask is not None:
            strip.putalpha(Image.composite(
                strip.split()[3], Image.new("L", (size, size), 0), mask))

        img.alpha_composite(strip)

    font = fitted_font(INITIALS, size, FILL)
    left, top, right, bottom = font.getbbox(INITIALS)
    draw = ImageDraw.Draw(img)
    draw.text(((size - (right - left)) / 2 - left,
               (size - (bottom - top)) / 2 - top - size * LIFT),
              INITIALS, font=font, fill=LIGHT)

    return img


def scaled(master, size):
    return master.resize((size, size), Image.LANCZOS)


# Safari renders this as a silhouette, so it is one colour and no gradient.
# Hand-drawn rather than traced from the font: at pinned-tab size a geometric
# J and P read more cleanly than a downsampled outline, and tracing would mean
# adding fontTools for one file.
PINNED_TAB = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <title>JP</title>
  <g fill="none" stroke="#000000" stroke-width="2.2"
     stroke-linecap="round" stroke-linejoin="round">
    <path d="M 5.7 3.2 L 5.7 11.2 A 1.85 1.85 0 0 1 2.0 11.2"/>
    <path d="M 9.9 13.05 L 9.9 3.2 L 11.6 3.2 A 2.6 2.6 0 0 1 11.6 8.4 L 9.9 8.4"/>
  </g>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    master = tile(MASTER)
    square = tile(MASTER, radius=0)

    for name, source, size in (
            ("favicon-16x16.png", master, 16),
            ("favicon-32x32.png", master, 32),
            ("android-chrome-192x192.png", master, 192),
            ("android-chrome-512x512.png", master, 512),
            ("apple-touch-icon.png", square, 180),
            ("mstile-150x150.png", square, 150)):
        path = os.path.join(OUT_DIR, name)
        image = scaled(source, size)

        # iOS and Windows composite these themselves; transparency would
        # arrive as black.
        if source is square:
            image = image.convert("RGB")

        image.save(path, optimize=True)
        report(path)

    ico = os.path.join(OUT_DIR, "favicon.ico")
    scaled(master, 256).save(ico, format="ICO",
                             sizes=[(16, 16), (32, 32), (48, 48)])
    report(ico)

    svg = os.path.join(OUT_DIR, "safari-pinned-tab.svg")
    with open(svg, "w", encoding="utf-8") as handle:
        handle.write(PINNED_TAB)
    report(svg)


if __name__ == "__main__":
    main()
