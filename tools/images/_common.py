"""Shared palette, fonts and paths for the image generators.

The colours are copied from the `:root` block in main/static/main/css/app.css.
If the site palette changes, change it here and re-run the generators.
"""
import os

from PIL import ImageFont

# Repo root, so the scripts work from any working directory.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IMG_DIR = os.path.join(ROOT, "main", "static", "main", "img")
SOURCE_DIR = os.path.join(ROOT, "source-images")

# Straight from app.css
PURPLE_DEEP = (0x2A, 0x1B, 0x3D)
PURPLE_MID = (0x44, 0x31, 0x8D)
ACCENT = (0xD8, 0x3F, 0x87)
SUNKEN = (0x1C, 0x11, 0x29)
LETTERING = (0xD6, 0xDD, 0xDF)

FONT_LIGHT = "C:/Windows/Fonts/segoeuil.ttf"     # Segoe UI Light
FONT_SEMI = "C:/Windows/Fonts/segoeui.ttf"

# The seed every generator uses, so re-running is a no-op in git.
SEED = 20260917


def lerp(a, b, t):
    """Blends two RGB tuples."""
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def load_font(size, *paths):
    """First font that loads, falling back to Pillow's built-in."""
    for path in (paths or (FONT_LIGHT, FONT_SEMI)):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def report(path):
    print(f"  {os.path.basename(path):24} {os.path.getsize(path) / 1024:7.1f} KB")
