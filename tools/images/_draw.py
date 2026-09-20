"""Shared drawing primitives for the project artwork.

Everything is composed from these so the whole set reads as one hand: same
ground, same line weights, same alphas. Add a new picture by combining panels,
nodes and arrows rather than by inventing new idioms.

All coordinates are in final pixels; SS supersampling is applied internally.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

from _common import ACCENT, LETTERING, PURPLE_DEEP, PURPLE_MID, SUNKEN, lerp, report

W, H = 1600, 1000

# Drawn at 2x then downsampled — Pillow does not antialias lines or ellipse
# outlines, and thin strokes look ragged without it.
SS = 2

MUTED = (0x8B, 0x7F, 0xA8)


def canvas():
    """The shared ground: a vertical wash with a soft glow off-centre."""
    base = Image.new("RGB", (W * SS, H * SS))
    draw = ImageDraw.Draw(base)

    for y in range(H * SS):
        t = y / (H * SS - 1)
        draw.line([(0, y), (W * SS, y)],
                  fill=lerp(lerp(PURPLE_DEEP, PURPLE_MID, 0.35), SUNKEN, t))

    glow = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([int(W * SS * 0.1), int(-H * SS * 0.35),
                   int(W * SS * 0.95), int(H * SS * 0.75)],
                  fill=PURPLE_MID + (70,))
    base = base.convert("RGBA")
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160 * SS // 2)))

    return base


def finish(img, stem, directory):
    flat = img.convert("RGB").resize((W, H), Image.LANCZOS)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{stem}.png")
    flat.save(path, optimize=True)
    report(path)


def circle(draw, x, y, r, fill, outline, width):
    draw.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline,
                 width=width)


def centred(draw, x, y, text, font, fill):
    draw.text((x, y), text, font=font, fill=fill, anchor="mm")


# --- higher level pieces ---------------------------------------------------

def stroke(draw, points, colour, alpha=255, width=2):
    draw.line([(x * SS, y * SS) for x, y in points],
              fill=colour + (alpha,), width=width * SS, joint="curve")


def panel(draw, x, y, w, h, *, radius=14, outline=PURPLE_MID, alpha=255,
          fill=SUNKEN, fill_alpha=235, width=3):
    """A rounded box: a system, a document, a screen."""
    draw.rounded_rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS],
                           radius=radius * SS,
                           fill=fill + (fill_alpha,) if fill else None,
                           outline=outline + (alpha,), width=width * SS)


def node(draw, x, y, r, *, hot=False, fill=None, alpha=255):
    colour = ACCENT if hot else PURPLE_MID
    circle(draw, x * SS, y * SS, r * SS,
           fill=(fill or SUNKEN) + (alpha,), outline=colour + (255,), width=3 * SS)


def dot(draw, x, y, r, colour, alpha=255):
    circle(draw, x * SS, y * SS, r * SS, fill=colour + (alpha,), outline=None, width=0)


def arrow(draw, x0, y0, x1, y1, colour=ACCENT, alpha=255, width=4, head=15):
    """A straight connector with a solid head at the far end."""
    angle = math.atan2(y1 - y0, x1 - x0)
    bx, by = x1 - math.cos(angle) * head, y1 - math.sin(angle) * head

    draw.line([x0 * SS, y0 * SS, bx * SS, by * SS],
              fill=colour + (alpha,), width=width * SS)

    left = (bx + math.cos(angle + math.pi / 2) * head * 0.55,
            by + math.sin(angle + math.pi / 2) * head * 0.55)
    right = (bx + math.cos(angle - math.pi / 2) * head * 0.55,
             by + math.sin(angle - math.pi / 2) * head * 0.55)

    draw.polygon([(left[0] * SS, left[1] * SS), (right[0] * SS, right[1] * SS),
                  (x1 * SS, y1 * SS)], fill=colour + (alpha,))


def text_lines(draw, x, y, w, count, *, spacing=22, alpha=170, ragged=False,
               colour=MUTED, rng=None):
    """Stand-in body text. `ragged` gives the uneven right edge of an
    unstructured document; otherwise the lines align."""
    for i in range(count):
        length = w
        if ragged and rng is not None:
            length = w * rng.uniform(0.55, 1.0)

        draw.line([x * SS, (y + i * spacing) * SS, (x + length) * SS,
                   (y + i * spacing) * SS],
                  fill=colour + (alpha,), width=3 * SS)


def field_rows(draw, x, y, w, rows, *, spacing=44, label_ratio=0.38):
    """Key/value rows: the structured counterpart to text_lines."""
    for i in range(rows):
        ry = y + i * spacing
        draw.line([x * SS, ry * SS, (x + w * label_ratio) * SS, ry * SS],
                  fill=MUTED + (190,), width=4 * SS)
        draw.line([(x + w * label_ratio + 18) * SS, ry * SS, (x + w) * SS, ry * SS],
                  fill=ACCENT + (200,), width=4 * SS)
