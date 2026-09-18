"""Generates the two hero banner frames.

Space-themed, built from the site's own palette so the banner and the page
agree: deep purple ground, indigo and magenta nebula, pale starfield, and the
grey-purple the nav already uses for the lettering.

Deterministic (fixed seed) so re-running produces the identical image.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter

from _common import (ACCENT, FONT_LIGHT, FONT_SEMI, IMG_DIR, LETTERING,
                     PURPLE_DEEP, PURPLE_MID, SEED, SUNKEN, lerp, load_font,
                     report)

W, H = 2000, 215
OUT = IMG_DIR


def ground():
    """Diagonal wash from the sunken purple through the mid purple."""
    base = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(base)

    for x in range(W):
        t = x / (W - 1)
        # Brightest around a third of the way across, so the panel is not flat.
        weight = 1 - abs(t - 0.36) * 1.5
        weight = max(0.0, min(1.0, weight))
        draw.line([(x, 0), (x, H)], fill=lerp(SUNKEN, lerp(PURPLE_DEEP, PURPLE_MID, 0.55), weight))

    return base


def nebula(rng):
    """Soft clouds of indigo and magenta, blurred well past recognition."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    clouds = [
        (330, 95, 460, 150, PURPLE_MID, 150),
        (640, 130, 380, 120, ACCENT, 70),
        (1180, 80, 520, 165, PURPLE_MID, 125),
        (1520, 140, 420, 130, ACCENT, 60),
        (1810, 70, 360, 120, PURPLE_MID, 110),
        (120, 150, 300, 110, ACCENT, 48),
    ]

    for cx, cy, rw, rh, colour, alpha in clouds:
        draw.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=colour + (alpha,))

    # A few smaller knots for texture.
    for _ in range(26):
        cx = rng.randint(0, W)
        cy = rng.randint(0, H)
        r = rng.randint(40, 130)
        colour = ACCENT if rng.random() < 0.4 else PURPLE_MID
        draw.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7],
                     fill=colour + (rng.randint(22, 55),))

    return layer.filter(ImageFilter.GaussianBlur(58))


def stars(rng):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    for _ in range(420):
        x, y = rng.randint(0, W), rng.randint(0, H)
        size = rng.choice([1, 1, 1, 1, 2, 2, 3])
        bright = rng.randint(140, 255)
        draw.ellipse([x, y, x + size, y + size], fill=(255, 252, 245, bright))

    # A handful of brighter ones with a soft halo.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for _ in range(16):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(5, 11)
        gdraw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 245, 250, 105))

    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(7)))
    return layer


def draw_text(canvas, text):
    """Fits the text to the banner, then draws it with a soft drop shadow."""
    size = 150
    font = load_font(size, FONT_LIGHT, FONT_SEMI)

    # Shrink until it clears the edges with room to breathe.
    while size > 40:
        box = ImageDraw.Draw(canvas).textbbox((0, 0), text, font=font)
        if (box[2] - box[0]) <= W * 0.82 and (box[3] - box[1]) <= H * 0.68:
            break
        size -= 4
        font = load_font(size, FONT_LIGHT, FONT_SEMI)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((W // 2, H // 2 + 4), text, font=font,
                                fill=(10, 6, 18, 190), anchor="mm")
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))

    ImageDraw.Draw(canvas).text((W // 2, H // 2), text, font=font,
                                fill=LETTERING + (255,), anchor="mm")
    return size


def build(text, stem):
    rng = random.Random(SEED)

    canvas = ground().convert("RGBA")
    canvas.alpha_composite(nebula(rng))
    canvas.alpha_composite(stars(rng))
    size = draw_text(canvas, text)

    flat = canvas.convert("RGB")
    flat.save(os.path.join(OUT, f"{stem}.png"), optimize=True)

    for width in (800, 1200, 2000):
        height = round(H * width / W)
        variant = flat.resize((width, height), Image.LANCZOS)
        name = f"{stem}.webp" if width == W else f"{stem}-{width}w.webp"
        variant.save(os.path.join(OUT, name), "WEBP", quality=86, method=6)
        report(os.path.join(OUT, name))

    return size


for text, stem in [("Jason Peck", "banner-name"), ("Solution Architect", "banner-role")]:
    used = build(text, stem)
    print(f"  {stem:14} '{text}'  font {used}px")
