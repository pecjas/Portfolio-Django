"""Derives the served portrait variants from the full-resolution original.

The photo is only ever painted at ~250-300 CSS px wide, so the 3094x4000
original carried roughly 100x more pixels than any display needs. This emits a
small WebP ladder plus a JPEG of the ladder's middle rung as the fallback.

Deterministic: re-running overwrites with identical output.
"""
import os

from PIL import Image, ImageOps

from _common import IMG_DIR, SOURCE_DIR, report

SRC = os.path.join(SOURCE_DIR, "jasonpeck-original.jpg")
OUT = IMG_DIR
STEM = "jasonpeck"

# Rendered 247px wide on mobile and 297px on desktop, so 300w covers 1x,
# 600w covers 2x, and 900w covers the 3x phones.
WIDTHS = (300, 600, 900)
FALLBACK_WIDTH = 600          # what a browser without WebP downloads


def variants():
    original = ImageOps.exif_transpose(Image.open(SRC)).convert("RGB")
    print(f"  source {original.width}x{original.height}")

    ratio = original.height / original.width

    for width in WIDTHS:
        height = round(width * ratio)
        # LANCZOS over this big a reduction keeps the edges of the glasses and
        # the lapel from going mushy.
        resized = original.resize((width, height), Image.LANCZOS)

        name = f"{STEM}.webp" if width == max(WIDTHS) else f"{STEM}-{width}w.webp"
        resized.save(os.path.join(OUT, name), "WEBP", quality=82, method=6)
        report(os.path.join(OUT, name))

        if width == FALLBACK_WIDTH:
            resized.save(os.path.join(OUT, f"{STEM}.jpg"), "JPEG", quality=82,
                         optimize=True, progressive=True)
            report(os.path.join(OUT, f"{STEM}.jpg"))

    return original.width, ratio


w, ratio = variants()
print(f"\n  width/height attributes: {FALLBACK_WIDTH} x {round(FALLBACK_WIDTH * ratio)}")
