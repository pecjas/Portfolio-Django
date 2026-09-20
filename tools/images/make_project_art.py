"""Generates project card artwork in the site palette.

Replaces three stock/clip-art images with a consistent set: same ground, same
palette, same line weights, so the portfolio grid reads as one thing rather
than a collection of downloads.

Sized 1600x1000 to match the card's 16:10 media box, so nothing is cropped.

Deterministic (fixed seed) so re-running produces identical files.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

from _common import (ACCENT, IMG_DIR, LETTERING, PURPLE_MID, SEED, SOURCE_DIR,
                     SUNKEN, load_font)
from _draw import MUTED, SS, W, H, canvas, centred, circle
from _draw import finish as _finish

OUT = os.path.join(SOURCE_DIR, "project-art")


def finish(img, stem, directory=None):
    _finish(img, stem, directory or OUT)


# ---------------------------------------------------------------------------
# 1. Binary search tree — Python Components
# ---------------------------------------------------------------------------

def binary_tree():
    img = canvas()
    draw = ImageDraw.Draw(img)
    font = load_font(46 * SS)

    nodes = {
        8: (800, 215), 3: (505, 435), 10: (1115, 435),
        1: (350, 655), 6: (680, 655), 14: (1265, 655),
        4: (560, 875), 7: (805, 875), 13: (1140, 875),
    }
    edges = [(8, 3), (8, 10), (3, 1), (3, 6), (10, 14), (6, 4), (6, 7), (14, 13)]

    # The path a lookup for 13 would take, drawn in the accent so the picture
    # says "search" rather than merely "tree".
    path = [(8, 10), (10, 14), (14, 13)]
    r = 54 * SS

    # Centre the drawing rather than trusting the hand-placed coordinates. The
    # tree is asymmetric -- a dense left subtree against a thin right chain --
    # so eyeballing it left the whole thing sitting low in the frame.
    radius = r / SS
    xs = [x for x, _ in nodes.values()]
    ys = [y for _, y in nodes.values()]
    dx = (W - (min(xs) + max(xs))) / 2
    dy = (H - (min(ys) + max(ys))) / 2
    nodes = {v: (x + dx, y + dy) for v, (x, y) in nodes.items()}

    for a, b in edges:
        ax, ay = (v * SS for v in nodes[a])
        bx, by = (v * SS for v in nodes[b])

        # Stop the line at the node edge so it does not run under the circle.
        angle = math.atan2(by - ay, bx - ax)
        ax, ay = ax + math.cos(angle) * r, ay + math.sin(angle) * r
        bx, by = bx - math.cos(angle) * r, by - math.sin(angle) * r

        hot = (a, b) in path
        draw.line([ax, ay, bx, by],
                  fill=(ACCENT if hot else MUTED) + (255,),
                  width=(5 if hot else 3) * SS)

    for value, (x, y) in nodes.items():
        x, y = x * SS, y * SS
        hot = value in (8, 10, 14, 13)
        circle(draw, x, y, r,
               fill=SUNKEN + (255,),
               outline=(ACCENT if hot else PURPLE_MID) + (255,),
               width=(5 if hot else 3) * SS)
        centred(draw, x, y, str(value), font,
                (LETTERING if hot else MUTED) + (255,))

    finish(img, "python-components")


# ---------------------------------------------------------------------------
# 2. Extract / transform / load — Referral ETL Process
# ---------------------------------------------------------------------------

def etl_pipeline():
    img = canvas()
    draw = ImageDraw.Draw(img)
    label_font = load_font(34 * SS)

    mid = 470 * SS

    def rounded(x0, y0, x1, y1, radius, **kw):
        draw.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS],
                               radius=radius * SS, **kw)

    # Extract: loose records, deliberately uneven.
    for i, (dx, dy, w) in enumerate([(0, -110, 150), (30, -40, 190),
                                     (0, 30, 165), (40, 100, 135)]):
        rounded(180 + dx, 430 + dy, 180 + dx + w, 430 + dy + 42, 10,
                fill=SUNKEN + (255,), outline=PURPLE_MID + (255,), width=3 * SS)

    # Transform: a funnel, because that is what the stage does.
    fx = 760
    draw.polygon([(fx - 150) * SS, (mid - 150 * SS), (fx + 150) * SS, (mid - 150 * SS),
                  (fx + 34) * SS, mid + 10 * SS, (fx + 34) * SS, (mid + 140 * SS),
                  (fx - 34) * SS, (mid + 140 * SS), (fx - 34) * SS, mid + 10 * SS],
                 fill=SUNKEN + (255,), outline=ACCENT + (255,), width=4 * SS)

    # Load: an aligned table.
    tx0, ty0 = 1130, 330
    rounded(tx0, ty0, tx0 + 300, ty0 + 290, 14,
            fill=SUNKEN + (255,), outline=PURPLE_MID + (255,), width=4 * SS)
    draw.line([tx0 * SS, (ty0 + 62) * SS, (tx0 + 300) * SS, (ty0 + 62) * SS],
              fill=ACCENT + (255,), width=4 * SS)
    for row in range(1, 5):
        y = (ty0 + 62 + row * 46) * SS
        draw.line([(tx0 + 26) * SS, y, (tx0 + 274) * SS, y],
                  fill=MUTED + (200,), width=3 * SS)
    for col in (1, 2):
        x = (tx0 + col * 100) * SS
        draw.line([x, (ty0 + 62) * SS, x, (ty0 + 290) * SS],
                  fill=MUTED + (120,), width=2 * SS)

    # Flow between the stages.
    for x0, x1 in ((450, 600), (940, 1100)):
        y = mid
        draw.line([x0 * SS, y, (x1 - 26) * SS, y], fill=ACCENT + (255,), width=5 * SS)
        draw.polygon([(x1 - 30) * SS, y - 16 * SS, (x1 - 30) * SS, y + 16 * SS,
                      x1 * SS, y], fill=ACCENT + (255,))

    for x, text in ((295, "EXTRACT"), (760, "TRANSFORM"), (1280, "LOAD")):
        centred(draw, x * SS, 810 * SS, text, label_font, MUTED + (255,))

    finish(img, "referral-etl")


# ---------------------------------------------------------------------------
# 3. Mapped data cleanup — patient safety
# ---------------------------------------------------------------------------

def bezier(p0, p1, p2, steps=64):
    """Quadratic curve, for the shield's shoulders. Pillow has no curve
    primitive, so the outline is a polygon sampled off this."""
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        points.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                       u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return points


def ecg(x0, x1, baseline, amplitude, beats=2):
    """A clinical trace: flat, P bump, QRS spike, T bump, flat. The single
    most legible shorthand for "patient" there is."""
    span = (x1 - x0) / beats
    points = [(x0, baseline)]

    for beat in range(beats):
        bx = x0 + beat * span
        for fx, fy in ((0.10, 0), (0.20, -0.18), (0.28, 0), (0.38, 0.12),
                       (0.44, -1.0), (0.50, 0.42), (0.56, 0), (0.72, -0.34),
                       (0.84, 0), (1.0, 0)):
            points.append((bx + span * fx, baseline + amplitude * fy))

    return points


def data_mapping():
    img = canvas()
    draw = ImageDraw.Draw(img)
    label_font = load_font(30 * SS)

    cx, top, bottom, half = 800, 120, 880, 320

    outline = ([(cx - half, top)]
               + bezier((cx + half, top), (cx + half, top + 450), (cx, bottom))
               + bezier((cx, bottom), (cx - half, top + 450), (cx - half, top)))
    outline.insert(1, (cx + half, top))

    draw.polygon([(x * SS, y * SS) for x, y in outline],
                 fill=SUNKEN + (225,), outline=PURPLE_MID + (255,), width=5 * SS)

    # The heartbeat carries "patient"; the shield carries "safety". Neither
    # reads as clinical on its own, which is what the mapping dots alone got
    # wrong.
    trace = ecg(cx - 232, cx + 232, top + 300, 150, beats=2)
    draw.line([(x * SS, y * SS) for x, y in trace],
              fill=ACCENT + (255,), width=6 * SS, joint="curve")

    # A faint continuation out to the shield edges, so the trace reads as
    # ongoing rather than starting and stopping inside the frame.
    for x_from, x_to in ((cx - half + 46, cx - 232), (cx + 232, cx + half - 46)):
        draw.line([x_from * SS, (top + 300) * SS, x_to * SS, (top + 300) * SS],
                  fill=ACCENT + (110,), width=4 * SS)

    # Beneath it, the cleanup itself: coded values mapped to standards, one
    # pair corrected.
    left_x, right_x = cx - 120, cx + 120
    first_y, spacing = top + 430, 68
    y_of = lambda row: first_y + row * spacing

    pairs = [(0, 1), (1, 0), (2, 2)]
    corrected = {(0, 1), (1, 0)}

    for src, dst in pairs:
        hot = (src, dst) in corrected
        draw.line([left_x * SS, y_of(src) * SS, right_x * SS, y_of(dst) * SS],
                  fill=(LETTERING if hot else MUTED) + (255 if hot else 130,),
                  width=(5 if hot else 3) * SS)

    for row in range(3):
        hot = any(row in pair for pair in corrected)
        for x in (left_x, right_x):
            circle(draw, x * SS, y_of(row) * SS, 14 * SS,
                   fill=(LETTERING if hot else PURPLE_MID) + (255,),
                   outline=SUNKEN + (255,), width=3 * SS)

    centred(draw, cx * SS, (bottom + 60) * SS, "PATIENT SAFETY", label_font,
            MUTED + (255,))

    finish(img, "mapped-data-cleanup")


# ---------------------------------------------------------------------------
# 4. Placeholder — every project without a screenshot
# ---------------------------------------------------------------------------

def placeholder(rng):
    """Deliberately quiet.

    This sits behind a third of the cards, so it has to recede: the title,
    capability tags and description are the content. The motif is a drafting
    sheet -- grid, elevation, extension and dimension lines, a compass arc --
    which reads as architecture in both senses: the buildings kind and the
    systems kind. No text, since it is shared by unrelated projects.
    """
    img = canvas()
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def line(x0, y0, x1, y1, alpha, width=2, colour=LETTERING):
        draw.line([x0 * SS, y0 * SS, x1 * SS, y1 * SS],
                  fill=colour + (alpha,), width=width * SS)

    # Blueprint grid. Every fourth line is a shade stronger, the way a drafting
    # sheet marks its major divisions.
    step = 50
    for i, x in enumerate(range(0, W + 1, step)):
        line(x, 0, x, H, 20 if i % 4 else 32, 1)
    for i, y in enumerate(range(0, H + 1, step)):
        line(0, y, W, y, 20 if i % 4 else 32, 1)

    # Elevation: one silhouette with internal bays, rather than five separate
    # rectangles -- outlining each bay equally read as a bar chart.
    base_y = 770
    bays = [(150, 250), (120, 380), (175, 300), (140, 470), (115, 205)]

    x = 430
    roof_corners = []
    spans = []
    for width, height in bays:
        spans.append((x, x + width, base_y - height))
        roof_corners.append((x, base_y - height))
        x += width

    # Window bands and mullions first, so the silhouette strokes over them.
    for x0, x1, top_y in spans:
        rows = max(2, (base_y - top_y) // 62)
        for r in range(1, rows):
            y = top_y + (base_y - top_y) * r / rows
            line(x0 + 9, y, x1 - 9, y, 34, 1)
        for c in range(1, 3):
            mx = x0 + (x1 - x0) * c / 3
            line(mx, top_y + 12, mx, base_y - 10, 22, 1)

    # Internal party walls, deliberately fainter than the outline.
    for x0, _, top_y in spans[1:]:
        line(x0, top_y, x0, base_y, 34, 1)

    # The silhouette itself, walked as one path.
    outline = [(spans[0][0], base_y)]
    for i, (x0, x1, top_y) in enumerate(spans):
        outline.append((x0, top_y))
        outline.append((x1, top_y))
        if i + 1 < len(spans):
            outline.append((x1, spans[i + 1][2]))
    outline.append((spans[-1][1], base_y))

    draw.line([(px * SS, py * SS) for px, py in outline],
              fill=LETTERING + (96,), width=3 * SS, joint="curve")

    # Construction lines rising off each roof.
    for x0, x1, top_y in spans:
        for edge in (x0, x1):
            line(edge, top_y - 8, edge, top_y - 92, 24, 1)

    right_edge = x
    line(300, base_y, 1320, base_y, 84, 3)

    # Extension and dimension lines below the elevation.
    for edge in (430, right_edge):
        line(edge, base_y + 14, edge, 866, 46, 1)

    line(430, 850, right_edge, 850, 52, 2)
    for edge, direction in ((430, 1), (right_edge, -1)):
        draw.polygon([(edge * SS, 850 * SS),
                      ((edge + direction * 16) * SS, (850 - 7) * SS),
                      ((edge + direction * 16) * SS, (850 + 7) * SS)],
                     fill=LETTERING + (52,))

    # A compass sweep struck from the left-hand base corner. The previous
    # version arced right over the elevation and read as a rainbow.
    pivot = (430, base_y)
    for radius, alpha in ((250, 60), (188, 30)):
        draw.arc([(pivot[0] - radius) * SS, (pivot[1] - radius) * SS,
                  (pivot[0] + radius) * SS, (pivot[1] + radius) * SS],
                 start=272, end=356, fill=ACCENT + (alpha,), width=2 * SS)
    line(pivot[0], pivot[1], pivot[0] + 250, pivot[1], 34, 1, ACCENT)

    # Nodes sit on the roof corners, so the systems reading of "architecture"
    # attaches to the structure rather than floating beside it.
    for i, (cx_, cy_) in enumerate(roof_corners):
        hot = i in (1, 3)
        r = 7 if hot else 5
        draw.ellipse([(cx_ - r) * SS, (cy_ - r) * SS, (cx_ + r) * SS, (cy_ + r) * SS],
                     fill=(ACCENT if hot else LETTERING) + (92 if hot else 62,))

    img.alpha_composite(layer)
    finish(img, "placeholder", IMG_DIR)


rng = random.Random(SEED)
placeholder(rng)
binary_tree()
etl_pipeline()
data_mapping()
print(f"\n  written to {OUT}")
