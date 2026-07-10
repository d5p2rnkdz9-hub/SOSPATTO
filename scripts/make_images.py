#!/usr/bin/env python3
"""Genera favicon, apple-touch-icon e og-image di SOS Patto (Pillow).

Stile: salvagente blu su fondo bianco, bordi ink — coerente con il logo nel header.
Rieseguibile: sovrascrive i PNG in IMAGES/.
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "IMAGES"
IMG.mkdir(exist_ok=True)

BLUE = (51, 177, 255)      # #33B1FF
INK = (26, 26, 26)         # #1A1A1A
WHITE = (255, 255, 255)

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]

def font(size):
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()

def buoy(draw, cx, cy, r, stroke):
    """Salvagente: cerchio blu bordato ink, foro bianco, 4 razze bianche."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE, outline=INK, width=stroke)
    hole = r * 0.45
    spoke = max(2, int(r * 0.22))
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        x1, y1 = cx + dx * hole, cy + dy * hole
        x2, y2 = cx + dx * r, cy + dy * r
        draw.line([x1, y1, x2, y2], fill=WHITE, width=spoke)
    draw.ellipse([cx - hole, cy - hole, cx + hole, cy + hole], fill=WHITE, outline=INK, width=stroke)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=stroke)

# ── favicon 16 / 32 ──────────────────────────────────────────────
for size, name in [(16, "favicon-16x16.png"), (32, "favicon-32x32.png")]:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    m = max(1, size // 16)
    buoy(d, size // 2, size // 2, size // 2 - m, max(1, size // 16))
    im.save(IMG / name)
    print("scritto", name)

# ── apple-touch-icon 180 (fondo pieno, come vuole iOS) ───────────
im = Image.new("RGB", (180, 180), WHITE)
d = ImageDraw.Draw(im)
buoy(d, 90, 90, 66, 7)
im.save(IMG / "apple-touch-icon.png")
print("scritto apple-touch-icon.png")

# ── og-image 1200x630 ────────────────────────────────────────────
im = Image.new("RGB", (1200, 630), WHITE)
d = ImageDraw.Draw(im)
# cornice ink + ombra brutalista
d.rounded_rectangle([48, 48, 1168, 598], radius=28, outline=INK, width=6)
d.rounded_rectangle([36, 36, 1156, 586], radius=28, fill=WHITE, outline=INK, width=6)
# salvagente
buoy(d, 170, 200, 84, 8)
# titolo: "S.O.S." in box blu + "Patto"
f_big = font(110)
f_sub = font(40)
f_url = font(30)
# box blu dietro S.O.S.
sos = "S.O.S."
bb = d.textbbox((0, 0), sos, font=f_big)
sw, sh = bb[2] - bb[0], bb[3] - bb[1]
bx, by = 300, 140
pad = 22
d.rounded_rectangle([bx - pad, by - pad, bx + sw + pad, by + sh + pad * 1.6],
                    radius=18, fill=BLUE, outline=INK, width=6)
d.text((bx - bb[0], by - bb[1]), sos, font=f_big, fill=INK)
d.text((bx + sw + pad * 2.2 - bb[0], by - bb[1]), "Patto", font=f_big, fill=INK)
# sottotitolo
d.text((90, 360), "Il Patto europeo su migrazione e asilo. Spiegato.", font=f_sub, fill=INK)
d.text((90, 425), "Testi normativi interattivi · diagrammi · giurisprudenza · circolari",
       font=f_url, fill=(85, 85, 85))
# barra blu in basso con url
d.rounded_rectangle([90, 495, 560, 552], radius=14, fill=BLUE, outline=INK, width=4)
d.text((115, 505), "www.sospatto.it", font=f_url, fill=INK)
im.save(IMG / "og-image.png")
print("scritto og-image.png")
