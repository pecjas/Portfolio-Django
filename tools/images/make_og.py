"""Builds the 1200x630 Open Graph / Twitter share card.

og:image previously pointed at the portrait, which is 3:4 — LinkedIn and Slack
crop that to a letterbox and lose the face. This is the 1.91:1 they actually
want, in the same space theme as the hero banners so a shared link looks like
the site it points at.

Deterministic (fixed seed) so re-running produces the identical image.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter

from _common import (ACCENT, FONT_LIGHT, FONT_SEMI, IMG_DIR, LETTERING,
                     PURPLE_DEEP, PURPLE_MID, SEED, SOURCE_DIR, SUNKEN, lerp,
                     load_font, report)

W, H = 1200, 630
OUT = IMG_DIR
PORTRAIT = os.path.join(SOURCE_DIR, "jasonpeck-original.jpg")

TEXT_COLUMN = 0.60          # left share of the canvas the words get


def font(path, size):
    return load_font(size, path)


def ground():
    base = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(base)
    for x in range(W):
        t = x / (W - 1)
        weight = max(0.0, min(1.0, 1 - abs(t - 0.30) * 1.5))
        draw.line([(x, 0), (x, H)],
                  fill=lerp(SUNKEN, lerp(PURPLE_DEEP, PURPLE_MID, 0.55), weight))
    return base


def nebula(rng):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for cx, cy, rw, rh, colour, alpha in [
        (200, 280, 380, 300, PURPLE_MID, 150),
        (430, 430, 320, 240, ACCENT, 66),
        (880, 200, 420, 330, PURPLE_MID, 120),
        (1080, 520, 330, 260, ACCENT, 58),
        (60, 560, 260, 220, PURPLE_MID, 95),
    ]:
        draw.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=colour + (alpha,))

    for _ in range(30):
        cx, cy = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(60, 180)
        colour = ACCENT if rng.random() < 0.4 else PURPLE_MID
        draw.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7],
                     fill=colour + (rng.randint(20, 50),))
    return layer.filter(ImageFilter.GaussianBlur(70))


def stars(rng):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for _ in range(520):
        x, y = rng.randint(0, W), rng.randint(0, H)
        size = rng.choice([1, 1, 1, 1, 2, 2, 3])
        draw.ellipse([x, y, x + size, y + size],
                     fill=(255, 252, 245, rng.randint(140, 255)))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for _ in range(18):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(6, 13)
        gdraw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 245, 250, 105))
    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
    return layer


def portrait():
    """The photo on the right, feathered into the nebula rather than cut out."""
    src = Image.open(PORTRAIT).convert("RGB")

    panel_w = round(W * (1 - TEXT_COLUMN)) + 60
    scale = max(panel_w / src.width, H / src.height)
    src = src.resize((round(src.width * scale), round(src.height * scale)),
                     Image.LANCZOS)

    # Crop toward the top so the head stays in frame, not the torso.
    left = (src.width - panel_w) // 2
    top = min(max(0, round(src.height * 0.04)), src.height - H)
    src = src.crop((left, top, left + panel_w, top + H))

    # Horizontal feather: opaque at the right edge, gone by the left of the panel.
    mask = Image.new("L", (panel_w, H), 0)
    mdraw = ImageDraw.Draw(mask)
    for x in range(panel_w):
        t = x / (panel_w - 1)
        mdraw.line([(x, 0), (x, H)], fill=round(255 * min(1.0, max(0.0, (t - 0.18) / 0.42))))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(src, (W - panel_w, 0), mask)
    return layer


def words(canvas):
    limit = round(W * TEXT_COLUMN)
    x = 72

    name_font = font(FONT_LIGHT, 104)
    role_font = font(FONT_SEMI, 40)

    draw = ImageDraw.Draw(canvas)
    name_h = draw.textbbox((0, 0), "Jason Peck", font=name_font)[3]

    # Block is centred vertically as a unit: name, rule, role.
    block_top = (H - (name_h + 34 + 48)) // 2

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.text((x, block_top + 4), "Jason Peck", font=name_font, fill=(10, 6, 18, 200))
    sdraw.text((x, block_top + name_h + 40), "Solution Architect", font=role_font,
               fill=(10, 6, 18, 190))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))

    draw = ImageDraw.Draw(canvas)
    draw.text((x, block_top), "Jason Peck", font=name_font, fill=LETTERING + (255,))
    draw.rounded_rectangle([x, block_top + name_h + 18, x + 96, block_top + name_h + 24],
                           radius=3, fill=ACCENT + (255,))
    draw.text((x, block_top + name_h + 40), "Solution Architect", font=role_font,
              fill=LETTERING + (235,))
    return limit


rng = random.Random(SEED)
canvas = ground().convert("RGBA")
canvas.alpha_composite(nebula(rng))
# Stars go under the photo: composited over it they land on his face as specks.
canvas.alpha_composite(stars(rng))
canvas.alpha_composite(portrait())
words(canvas)

# Only the JPEG ships; a PNG of this is ~380 KB for no visible gain.
flat = canvas.convert("RGB")
flat.save(os.path.join(OUT, "og-card.jpg"), "JPEG", quality=88, optimize=True,
          progressive=True)
report(os.path.join(OUT, "og-card.jpg"))
