#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis_allParticipants.py

Automatically finds all “*_coordinates.csv” files in the `data/` folder and,
for each participant:
  1. Computes ellipse width/height in cm & deg
  2. Prints face dimensions (cm) & angular size (deg)
  3. Prints the rest of the computed values
  4. Prints a per‐identity summary
  5. Saves both the full trial table and summary to CSVs

Assumptions:
  • screen resolution: 1920×1080 px
  • screen diagonal: 24″
  • viewing distance: 0.5 m
  • PsychoPy “pix” units centered at (0,0)
"""

import os
import glob
import numpy as np
import pandas as pd

# 1. SCREEN PARAMETERS
RES_X, RES_Y    = 1920, 1080           # px
DIAG_INCH       = 24.0                 # inches
VIEW_DIST_M     = 0.5                  # meters

# 2. PIXELS → CM / DISTANCE IN CM
INCH_TO_CM = 2.54
diag_cm     = DIAG_INCH * INCH_TO_CM
diag_px     = np.hypot(RES_X, RES_Y)
width_cm    = diag_cm * (RES_X / diag_px)
height_cm   = diag_cm * (RES_Y / diag_px)
pix2cm_x    = width_cm  / RES_X
pix2cm_y    = height_cm / RES_Y
dist_cm     = VIEW_DIST_M * 100

# 3. FIND ALL COORDINATES FILES
data_dir    = 'data'
pattern     = os.path.join(data_dir, '*_coordinates.csv')
coord_files = glob.glob(pattern)
if not coord_files:
    raise RuntimeError(f"No files matching {pattern}")

# 4. PROCESS EACH PARTICIPANT
for coords_path in coord_files:
    participant = os.path.basename(coords_path).replace('_coordinates.csv', '')
    df = pd.read_csv(coords_path)

    # rename to standard names
    df = df.rename(columns={
        'ellipse_width':  'ellipse_w_px',
        'ellipse_height': 'ellipse_h_px',
        'nose_x':         'nose_x_px',   # still kept if you want raw px later
        'nose_y':         'nose_y_px'
    })

    # px → cm for ellipse
    df['ellipse_w_cm'] = df['ellipse_w_px'] * pix2cm_x
    df['ellipse_h_cm'] = df['ellipse_h_px'] * pix2cm_y

    # compute ellipse angular size (deg)
    df['ellipse_w_deg'] = 2 * np.degrees(
        np.arctan2(df['ellipse_w_cm'] / 2, dist_cm)
    )
    df['ellipse_h_deg'] = 2 * np.degrees(
        np.arctan2(df['ellipse_h_cm'] / 2, dist_cm)
    )

    # console output
    pd.set_option('display.max_rows', None, 'display.max_columns', None)
    print(f"\n\n=== Participant: {participant} ===")

    # face dims (cm) & face angular size (deg)
    face_cols = [
        'identity',
        'ellipse_w_cm','ellipse_h_cm',
        'ellipse_w_deg','ellipse_h_deg'
    ]
    print("\n-- Face dimensions (cm) & angular size (deg) --")
    print(df[face_cols].to_string(index=False))

    # rest of computed columns
    other_cols = [c for c in df.columns if c not in face_cols]
    print("\n-- Other computed values --")
    print(df[other_cols].to_string(index=False))

    # per-identity summary
    summary = df[[
        'identity',
        'ellipse_w_cm','ellipse_h_cm',
        'ellipse_w_deg','ellipse_h_deg'
    ]].groupby('identity').mean().round(2)

    print("\n-- Mean values by identity --")
    print(summary)

    # save outputs
    full_csv    = os.path.join(data_dir, f"analysis_{participant}_full.csv")
    summary_csv = os.path.join(data_dir, f"analysis_{participant}_summary.csv")

    df.to_csv(full_csv, index=False)
    summary.to_csv(summary_csv)
    print(f"\nSaved full table   → {full_csv}")
    print(f"Saved summary table→ {summary_csv}")

print("\nAll participants processed.\n")
