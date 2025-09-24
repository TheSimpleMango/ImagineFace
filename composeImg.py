#!/usr/bin/env python3
"""
compose_people_hardcoded.py

Place two transparent-PNG “people” into a room background:
 - Scale the room to full monitor resolution
 - Helly on the left, Mark on the right
 - Equal spacing to the sides and between them
Scale each so that their face-region is
8° tall for Helly and 4° tall for Mark,
then shift both down by a fixed pixel offset,
additionally move Helly further down,
and shift Mark to the left by a fixed pixel offset.
"""

import math
import os
from PIL import Image

# === USER PARAMETERS ===
# Paths
media_dir = os.path.join(os.path.dirname(__file__), 'media', 'images')
BG_PATH       = os.path.join(media_dir, 'room.png')
P1_PATH       = os.path.join(media_dir, 'marki.png')    # Mark → will be on the right initially
P2_PATH       = os.path.join(media_dir, 'hellyi.png')   # Helly → will be on the left
OUTPUT_PATH   = os.path.join(media_dir, 'room_with_people.png')

# Face bounds in source images (Y-pixels)
FACE1_TOP     = 100   # Mark
FACE1_BOTTOM  = 300
FACE2_TOP     = 110   # Helly
FACE2_BOTTOM  = 310

# Desired face-height in degrees
DES_FACE1_DEG = 2.0   # Mark’s face: 4°
DES_FACE2_DEG = 4.0   # Helly’s face: 8°

# Monitor / screen specs (must match your PsychoPy monitor)
MON_WIDTH_CM     = 53.0      # physical width of monitor in cm
MON_DIST_CM      = 100.0     # viewing distance in cm
RES_X, RES_Y     = 1920, 1080  # resolution in pixels

# Vertical shifts (pixels)
VERT_SHIFT_PX        = 100   # applied to both Helly and Mark
HELLY_EXTRA_SHIFT_PX = 400   # additional downward shift for Helly only
# Horizontal shift for Mark (pixels)
MARK_LEFT_SHIFT_PX   = 200   # move Mark to the left
# === END PARAMETERS ===

def deg_to_px(deg, mon_width_cm, mon_dist_cm, res_px):
    """Convert visual angle in degrees to pixels."""
    width_mm   = mon_width_cm * 10
    dist_mm    = mon_dist_cm  * 10
    mm_per_px  = width_mm / res_px
    offset_mm  = dist_mm * math.tan(math.radians(deg))
    return offset_mm / mm_per_px


def main():
    # --- load & scale room background to full monitor resolution ---
    bg = Image.open(BG_PATH).convert('RGBA')
    bg = bg.resize((RES_X, RES_Y), Image.LANCZOS)

    # --- load people images ---
    mark  = Image.open(P1_PATH).convert('RGBA')
    helly = Image.open(P2_PATH).convert('RGBA')

    # --- compute scale factors so face-region matches desired visual angle ---
    face1_px   = FACE1_BOTTOM - FACE1_TOP
    face2_px   = FACE2_BOTTOM - FACE2_TOP
    target1_px = deg_to_px(DES_FACE1_DEG, MON_WIDTH_CM, MON_DIST_CM, RES_X)
    target2_px = deg_to_px(DES_FACE2_DEG, MON_WIDTH_CM, MON_DIST_CM, RES_X)
    scale1     = target1_px / face1_px    # Mark’s scale
    scale2     = target2_px / face2_px    # Helly’s scale

    # --- apply uniform scaling (maintaining aspect ratio) ---
    def scaled(img, scale):
        w, h = img.size
        return img.resize((int(round(w * scale)), int(round(h * scale))), Image.LANCZOS)

    mark  = scaled(mark, scale1)
    helly = scaled(helly, scale2)

    # --- compute equal margins: left/inner/right gaps all the same ---
    total_w = bg.width
    # three gaps: left edge→helly, helly→mark, mark→right edge
    margin = (total_w - helly.width - mark.width) / 3.0
    x_helly = int(round(margin))
    x_mark_initial = int(round(2 * margin + helly.width))
    # apply extra left shift to Mark
    x_mark = x_mark_initial - MARK_LEFT_SHIFT_PX

    # --- compute vertical positions and apply downward shifts ---
    y_center = int(round((bg.height) / 2))
    y_helly  = y_center - helly.height // 2 + VERT_SHIFT_PX + HELLY_EXTRA_SHIFT_PX
    y_mark   = y_center - mark.height  // 2 + VERT_SHIFT_PX

    # --- composite & save ---
    composite = Image.new('RGBA', bg.size)
    composite.paste(bg,    (0,      0))
    composite.paste(helly, (x_helly, y_helly), helly)
    composite.paste(mark,  (x_mark,  y_mark),  mark)
    composite.save(OUTPUT_PATH)

    print(f"Saved composite → {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
