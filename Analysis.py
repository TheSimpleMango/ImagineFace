#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis_allParticipants.py

Automatically finds all “*_coordinates.csv” files in the `data/` folder (one per subfolder) and,
for each participant:
  1. Computes ellipse width/height in cm & deg
  2. Prints face dimensions (cm) & angular size (deg)
  3. Prints the rest of the computed values (including raw landmark px)
  4. Prints a per‐identity summary
  5. Saves both the full trial table and summary to CSVs
Finally, it combines all participant summaries into a single CSV.

Assumptions:
  • screen resolution: 1920×1080 px
  • screen diagonal: 24″
  • viewing distance: 0.5 m
  • PsychoPy “pix” units centered at (0,0)
"""
# TODO x and y of nose location in eccentricity also images if possible
# TODO instructions on installing psychopy and tobii software

import os
import glob
import numpy as np
import pandas as pd

# 1. SCREEN PARAMETERS
# RES_X, RES_Y    = 1920, 1080           # px
# DIAG_INCH       = 24.0                 # inches
# VIEW_DIST_M     = 0.5                  # meters
RES_X, RES_Y    = 2880, 2800           # px
DIAG_INCH       = 15.4                 # inches
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

# 3. FIND ALL COORDINATES FILES (each in its own subfolder)
data_dir    = 'data'
pattern     = os.path.join(data_dir, '*', '*_coordinates.csv')
coord_files = glob.glob(pattern)
if not coord_files:
    raise RuntimeError(f"No files matching {pattern}")

# Container for all summaries
all_summaries = []

# 4. PROCESS EACH PARTICIPANT
for coords_path in coord_files:
    participant = os.path.basename(coords_path).replace('_coordinates.csv', '')
    df = pd.read_csv(coords_path)

    # --- Rename to standard px columns ---
    df = df.rename(columns={
        'ellipse_w':    'ellipse_w_px',
        'ellipse_h':    'ellipse_h_px',
        'nose_x':       'nose_x_px',
        'nose_y':       'nose_y_px',
        'lefteye_x':    'lefteye_x_px',
        'lefteye_y':    'lefteye_y_px',
        'righteye_x':   'righteye_x_px',
        'righteye_y':   'righteye_y_px',
        'mouth_x':      'mouth_x_px',
        'mouth_y':      'mouth_y_px',
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
        'ellipse_w_cm', 'ellipse_h_cm',
        'ellipse_w_deg', 'ellipse_h_deg'
    ]
    print("\n-- Face dimensions (cm) & angular size (deg) --")
    print(df[face_cols].to_string(index=False))

    # rest of computed columns (including raw px landmarks)
    other_cols = [c for c in df.columns if c not in face_cols]
    print("\n-- Other computed & raw values --")
    print(df[other_cols].to_string(index=False))

    # per-identity summary
    summary = (
        df[face_cols]
        .groupby('identity')
        .mean()
        .round(2)
        .reset_index()
    )
    # tag with participant
    summary.insert(0, 'participant', participant)

    print("\n-- Mean values by identity --")
    print(summary.to_string(index=False))

    # save individual CSVs
    full_csv    = os.path.join(data_dir, f"analysis_{participant}_full.csv")
    summary_csv = os.path.join(data_dir, f"analysis_{participant}_summary.csv")
    df.to_csv(full_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    print(f"\nSaved full table   → {full_csv}")
    print(f"Saved summary table→ {summary_csv}")

    # collect for combined table
    all_summaries.append(summary)

# 5. COMBINE ALL SUMMARIES
combined = pd.concat(all_summaries, ignore_index=True)
combined_csv = os.path.join(data_dir, 'analysis_allParticipants_summary_combined.csv')
combined.to_csv(combined_csv, index=False)

print("\n=== Combined Summary Across All Participants ===")
print(combined.to_string(index=False))
print(f"\nSaved combined summary → {combined_csv}\n")
