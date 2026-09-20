"""Artwork for the professional case-study projects that have no screenshot.

These are integration and delivery projects — there is nothing to screenshot,
and a stock photo would say less than nothing. Each picture instead draws the
one thing that made the project distinctive: the shape of the integration, the
before/after, the constraint.

Built from the same primitives as make_project_art, so the grid reads as one
set. Filenames match the project slug.

Deterministic (fixed seed) so re-running produces identical files.
"""
import math
import os
import random

from PIL import Image, ImageDraw

from _common import ACCENT, LETTERING, PURPLE_MID, SEED, SOURCE_DIR, SUNKEN, load_font
from _draw import (MUTED, SS, H, W, arrow, canvas, centred, dot, field_rows,
                   finish, node, panel, stroke, text_lines)

OUT = os.path.join(SOURCE_DIR, "project-art")

LABEL = 30
SMALL = 26


def sheet():
    img = canvas()
    return img, ImageDraw.Draw(img)


def label(draw, x, y, text, size=LABEL, colour=MUTED, alpha=255):
    centred(draw, x * SS, y * SS, text, load_font(size * SS), colour + (alpha,))


def fit_label(draw, cx, cy, text, max_width, size=SMALL, colour=MUTED,
              alpha=255, minimum=17):
    """Shrinks until the text fits the box it sits in.

    Set by eye, "CUSTOM DOWNSTREAM LOGIC" ran past both edges of its panel.
    """
    while size > minimum:
        font = load_font(size * SS)
        box = draw.textbbox((0, 0), text, font=font)
        if (box[2] - box[0]) <= max_width * SS:
            break
        size -= 1

    centred(draw, cx * SS, cy * SS, text, load_font(size * SS), colour + (alpha,))


def radial_label(draw, x, y, angle, text, size=SMALL, colour=MUTED, alpha=235,
                 gap=26):
    """Sets a label outside a spoke's end, anchored so it reads away from the
    hub. Centring these put long names like ORACLE EBS straight through their
    own node."""
    dx, dy = math.cos(angle), math.sin(angle)

    if dx > 0.35:
        anchor, ox, oy = "lm", gap, 0
    elif dx < -0.35:
        anchor, ox, oy = "rm", -gap, 0
    else:
        anchor = "ms"
        ox, oy = 0, (gap + 10) if dy > 0 else -(gap + 22)

    draw.text(((x + ox) * SS, (y + oy) * SS), text, font=load_font(size * SS),
              fill=colour + (alpha,), anchor=anchor)


# ---------------------------------------------------------------------------

def ai_tooling():
    """Adoption spreading from one tool to a whole team."""
    img, draw = sheet()
    cx, cy = 800, 470

    for radius, alpha in ((150, 70), (250, 44), (350, 24)):
        draw.ellipse([(cx - radius) * SS, (cy - radius) * SS,
                      (cx + radius) * SS, (cy + radius) * SS],
                     outline=ACCENT + (alpha,), width=2 * SS)

    # The team, taking it up.
    seats = 9
    for i in range(seats):
        angle = -math.pi / 2 + i * 2 * math.pi / seats
        x, y = cx + math.cos(angle) * 300, cy + math.sin(angle) * 300
        adopted = i % 3 != 2

        stroke(draw, [(cx, cy), (x, y)], ACCENT if adopted else MUTED,
               70 if adopted else 34, 2)
        node(draw, x, y, 26, hot=adopted)
        dot(draw, x, y, 9, (ACCENT if adopted else MUTED), 210)

    # The tool itself: an editor with an inline suggestion.
    panel(draw, cx - 132, cy - 86, 264, 172, radius=16, outline=ACCENT, width=3)
    text_lines(draw, cx - 100, cy - 46, 150, 3, spacing=26, alpha=150)
    draw.rounded_rectangle([(cx - 100) * SS, (cy + 10) * SS,
                            (cx + 96) * SS, (cy + 46) * SS],
                           radius=8 * SS, fill=ACCENT + (46,),
                           outline=ACCENT + (170,), width=2 * SS)
    text_lines(draw, cx - 86, cy + 28, 120, 1, alpha=210, colour=LETTERING)

    label(draw, cx, 862, "ADOPTION ACROSS THE TEAM")
    finish(img, "ai-tooling", OUT)


def erp_integrations():
    """One platform, many ERPs — the hub and its spokes."""
    img, draw = sheet()
    cx, cy = 800, 450

    targets = [("SAP ECC", -168), ("S/4HANA", -126), ("ORACLE EBS", -84),
               ("JDE", -42), ("D365", 0), ("NETSUITE", 42), ("AS400", 84),
               ("QAD", 126), ("BOOMI", 168)]

    for name, degrees in targets:
        angle = math.radians(degrees - 90)
        x, y = cx + math.cos(angle) * 300, cy + math.sin(angle) * 300
        stroke(draw, [(cx, cy), (x, y)], PURPLE_MID, 150, 2)
        dot(draw, x, y, 11, ACCENT, 210)
        radial_label(draw, x, y, angle, name)

    panel(draw, cx - 118, cy - 62, 236, 124, radius=18, outline=ACCENT, width=4)
    label(draw, cx, cy - 16, "SaaS", LABEL, LETTERING)
    label(draw, cx, cy + 20, "PLATFORM", SMALL, MUTED)

    label(draw, cx, 880, "ONE PLATFORM, MANY ERPs")
    finish(img, "erp-integrations", OUT)


def delivery_hub():
    """Two sites, one workflow, with the handoff drawn as the subject."""
    img, draw = sheet()
    base = 430

    for x, name, place in ((330, "ONSHORE", "US"), (1270, "DELIVERY HUB", "MALAYSIA")):
        panel(draw, x - 150, base - 92, 300, 184, radius=18,
              outline=ACCENT if x > 800 else PURPLE_MID, width=4)
        fit_label(draw, x, base - 26, name, 260, colour=LETTERING)
        label(draw, x, base + 16, place, SMALL, MUTED)

        for i in range(4):
            dot(draw, x - 78 + i * 52, base + 62, 9, MUTED, 170)

    # The handoff: work out, feedback back.
    arrow(draw, 500, base - 34, 1105, base - 34, ACCENT, 230, 4)
    label(draw, 800, base - 74, "TASK HANDOFF & STANDARDS", SMALL)

    arrow(draw, 1105, base + 44, 500, base + 44, MUTED, 190, 3)
    label(draw, 800, base + 84, "FEEDBACK LOOP", SMALL)

    # Concurrent workstreams the model had to carry.
    for i in range(4):
        y = 660 + i * 52
        stroke(draw, [(430, y), (1170, y)], MUTED, 60, 2)
        dot(draw, 430, y, 8, PURPLE_MID, 200)
        dot(draw, 1170, y, 8, ACCENT, 170)

    label(draw, 800, 906, "CONCURRENT CUSTOMER PROJECTS")
    finish(img, "delivery-hub", OUT)


def account_consolidation():
    """Several accounts becoming one, with the history carried across."""
    img, draw = sheet()

    for i, y in enumerate((250, 400, 550)):
        panel(draw, 200, y - 52, 250, 104, radius=14, width=3)
        text_lines(draw, 228, y - 20, 150, 2, spacing=26, alpha=150)
        arrow(draw, 470, y, 690, 400, ACCENT if i == 1 else MUTED,
              220 if i == 1 else 130, 3)

    panel(draw, 710, 300, 330, 200, radius=18, outline=ACCENT, width=4)
    fit_label(draw, 875, 352, "UNIFIED ACCOUNT", 290, colour=LETTERING)
    field_rows(draw, 760, 404, 230, 3, spacing=38)

    # Order history preserved through the migration.
    stroke(draw, [(760, 690), (1400, 690)], MUTED, 150, 3)
    for i in range(7):
        x = 760 + i * 106
        dot(draw, x, 690, 9, ACCENT if i > 3 else MUTED, 220 if i > 3 else 150)
        stroke(draw, [(x, 676), (x, 704)], MUTED, 120, 2)

    arrow(draw, 875, 512, 875, 660, MUTED, 150, 3)
    label(draw, 1080, 748, "COMPLETE ORDER HISTORY PRESERVED", SMALL)
    label(draw, 325, 660, "SAP ECC", SMALL)
    label(draw, 325, 700, "INTEGRATION", SMALL)

    finish(img, "account-consolidation", OUT)


def auto_updates():
    """A versioning path, and the release that proved it."""
    img, draw = sheet()
    base = 700

    versions = [("v1", 120), ("v2", 170), ("v3", 230), ("v4", 300), ("v5", 380)]
    x = 360
    for i, (name, height) in enumerate(versions):
        current = i == 3
        panel(draw, x, base - height, 130, height, radius=10,
              outline=ACCENT if current else PURPLE_MID,
              width=4 if current else 2,
              fill_alpha=235 if current else 170)
        label(draw, x + 65, base - height - 34, name, SMALL,
              LETTERING if current else MUTED)

        if current:
            # Stacked upward from the bar: marker, then the two label lines.
            # Set closer, PRODUCTION sat on top of the marker.
            dot(draw, x + 65, base - height - 76, 9, ACCENT, 240)
            label(draw, x + 65, base - height - 120, "PRODUCTION", SMALL, ACCENT)
            label(draw, x + 65, base - height - 156, "FIRST TO", SMALL, ACCENT)
        x += 168

    stroke(draw, [(300, base), (1300, base)], LETTERING, 90, 3)
    arrow(draw, 1180, base - 40, 1300, base - 40, ACCENT, 200, 4)
    label(draw, 800, 830, "VERSIONING PATH NOW USED BY EVERY NEW PROJECT")

    finish(img, "auto-updates", OUT)


def pricing_rest_integrations():
    """A price checked against the customer's own system, in real time."""
    img, draw = sheet()

    panel(draw, 150, 330, 300, 240, radius=18, width=3)
    label(draw, 300, 382, "ORDER", SMALL, LETTERING)
    field_rows(draw, 190, 440, 220, 3, spacing=40)

    panel(draw, 1150, 330, 300, 240, radius=18, outline=ACCENT, width=4)
    fit_label(draw, 1300, 382, "CUSTOMER PRICING", 260, colour=LETTERING)
    label(draw, 1300, 418, "SYSTEM", SMALL, MUTED)
    field_rows(draw, 1190, 470, 220, 2, spacing=40)

    arrow(draw, 470, 410, 1130, 410, ACCENT, 235, 4)
    label(draw, 800, 370, "REST REQUEST", SMALL)

    arrow(draw, 1130, 500, 470, 500, MUTED, 200, 3)
    label(draw, 800, 540, "AUTHORITATIVE PRICE", SMALL)

    # The four pricing models the same approach had to cover.
    for i, name in enumerate(("STOCK", "CUSTOMER", "CONTRACT", "QUOTE")):
        x = 380 + i * 280
        dot(draw, x, 700, 10, ACCENT, 200)
        stroke(draw, [(x, 660), (x, 686)], MUTED, 110, 2)
        label(draw, x, 744, name, SMALL)

    stroke(draw, [(380, 660), (1220, 660)], MUTED, 90, 2)
    label(draw, 800, 862, "ONE APPROACH, EVERY PRICING MODEL")

    finish(img, "pricing-rest-integrations", OUT)


def llm_order_extraction(rng):
    """Unstructured purchase order in, validated fields out."""
    img, draw = sheet()

    panel(draw, 150, 250, 330, 440, radius=16, width=3)
    fit_label(draw, 315, 300, "PURCHASE ORDER", 290, colour=LETTERING)
    text_lines(draw, 190, 350, 250, 9, spacing=34, alpha=120, ragged=True, rng=rng)

    # The model in the middle.
    panel(draw, 620, 380, 360, 180, radius=22, outline=ACCENT, width=4)
    label(draw, 800, 436, "LLM", LABEL, LETTERING)
    fit_label(draw, 800, 486, "ENGINEERED PROMPTS", 320)

    arrow(draw, 500, 470, 600, 470, ACCENT, 230, 4)
    arrow(draw, 1000, 470, 1100, 470, ACCENT, 230, 4)

    panel(draw, 1120, 250, 330, 440, radius=16, outline=ACCENT, width=4)
    fit_label(draw, 1285, 300, "VALIDATED FIELDS", 290, colour=LETTERING)
    field_rows(draw, 1160, 360, 250, 6, spacing=52)

    label(draw, 800, 620, "VALIDATED AGAINST MASTER DATA", SMALL)
    label(draw, 800, 812, "STRAIGHT-THROUGH ORDER PROCESSING")

    finish(img, "llm-order-extraction", OUT)


def edi_850():
    """Many trading partners in, one standard shape, configurable out."""
    img, draw = sheet()

    for i in range(5):
        y = 250 + i * 120
        panel(draw, 120, y - 42, 210, 84, radius=12, width=2, fill_alpha=180)
        fit_label(draw, 225, y, f"PARTNER {i + 1}", 180)
        arrow(draw, 350, y, 560, 440, MUTED, 150, 3)

    panel(draw, 580, 350, 300, 180, radius=20, outline=ACCENT, width=4)
    label(draw, 730, 404, "EDI 850", LABEL, LETTERING)
    fit_label(draw, 730, 456, "STANDARD MAPPING", 260)

    for i in range(3):
        y = 320 + i * 120
        arrow(draw, 900, 440, 1090, y, ACCENT, 200, 3)
        panel(draw, 1110, y - 42, 340, 84, radius=12, outline=PURPLE_MID, width=3)
        fit_label(draw, 1280, y, "CUSTOM DOWNSTREAM LOGIC", 300)

    label(draw, 800, 750, "CONFIGURABLE BY AN ADMINISTRATOR, NO CODE REQUIRED")
    label(draw, 800, 812, "SELF-SERVICE PARTNER ONBOARDING", SMALL)

    finish(img, "configurable-edi-850-integration-framework", OUT)


def malaysia_einvoicing():
    """A government deadline, and a lot of customers to move before it."""
    img, draw = sheet()

    panel(draw, 150, 330, 280, 300, radius=16, width=3)
    label(draw, 290, 384, "INVOICES", SMALL, LETTERING)
    text_lines(draw, 190, 440, 200, 5, spacing=34, alpha=130)

    arrow(draw, 450, 470, 640, 470, ACCENT, 230, 4)

    # The portal, drawn as an institution rather than a box.
    cx = 800
    stroke(draw, [(cx - 140, 400), (cx, 330), (cx + 140, 400)], LETTERING, 150, 3)
    panel(draw, cx - 130, 400, 260, 190, radius=6, outline=PURPLE_MID, width=3)
    for i in range(4):
        x = cx - 96 + i * 64
        stroke(draw, [(x, 424), (x, 566)], MUTED, 130, 3)
    stroke(draw, [(cx - 150, 590), (cx + 150, 590)], LETTERING, 150, 4)
    label(draw, cx, 640, "MyInvois PORTAL", SMALL, LETTERING)

    arrow(draw, 960, 470, 1150, 470, ACCENT, 230, 4)

    # The deadline.
    ring = (1290, 470)
    draw.ellipse([(ring[0] - 108) * SS, (ring[1] - 108) * SS,
                  (ring[0] + 108) * SS, (ring[1] + 108) * SS],
                 outline=ACCENT + (210,), width=5 * SS)
    draw.arc([(ring[0] - 108) * SS, (ring[1] - 108) * SS,
              (ring[0] + 108) * SS, (ring[1] + 108) * SS],
             start=-90, end=34, fill=ACCENT + (255,), width=12 * SS)
    stroke(draw, [(ring[0], ring[1]), (ring[0], ring[1] - 64)], LETTERING, 220, 4)
    stroke(draw, [(ring[0], ring[1]), (ring[0] + 48, ring[1])], LETTERING, 220, 4)
    label(draw, ring[0], 626, "MANDATE DATE", SMALL)

    label(draw, 800, 800, "CROSS-BORDER RESPONSE UNDER A COMPLIANCE DEADLINE")
    label(draw, 800, 862, "HIGH VOLUME OF CUSTOMERS ONBOARDED", SMALL)

    finish(img, "malaysia-e-invoicing", OUT)


if __name__ == "__main__":
    rng = random.Random(SEED)

    ai_tooling()
    erp_integrations()
    delivery_hub()
    account_consolidation()
    auto_updates()
    pricing_rest_integrations()
    llm_order_extraction(rng)
    edi_850()
    malaysia_einvoicing()

    print(f"\n  written to {OUT}")
