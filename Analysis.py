#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis_allParticipants.py

Automatically finds all "*_coordinates.csv" files in the `data/` folder (one per subfolder) and,
for each participant:
  1. Computes ellipse width/height in cm & deg
  2. Converts all landmark coordinates from px to cm
  3. Prints face dimensions (cm) & angular size (deg)
  4. Prints the rest of the computed values (including raw landmark px)
  5. Prints a per‐identity summary
Finally, it combines all participant data into:
  - analysis_combined_full.csv (all trial data with both px and cm units)
  - analysis_combined_cm.csv (all trial data with only cm units, no px redundancy)

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
import json
import numpy as np
import pandas as pd

# 1. SCREEN PARAMETERS
# Hardcoded physical screen size and viewing distance
DIAG_INCH = 24.0        # inches - hardcoded monitor diagonal
VIEW_DIST_M = 0.5       # meters - hardcoded viewing distance

# Default resolution (used if no hardware specs found)
DEFAULT_RES_X, DEFAULT_RES_Y = 1920, 1080    # px

# Conversion constant
INCH_TO_CM = 2.54

def load_hardware_specs(participant_dir, participant_name):
    """Load hardware specs from JSON file if available."""
    json_path = os.path.join(participant_dir, f"{participant_name}_hardware_specs.json")
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return None

def get_screen_params(hardware_specs):
    """Calculate screen parameters using resolution from hardware specs and hardcoded physical dimensions."""
    # Get resolution from hardware specs or use defaults
    if hardware_specs and 'monitor' in hardware_specs:
        monitor = hardware_specs['monitor']
        res_x, res_y = monitor.get('resolution', [DEFAULT_RES_X, DEFAULT_RES_Y])
    else:
        res_x, res_y = DEFAULT_RES_X, DEFAULT_RES_Y

    # Calculate physical dimensions using hardcoded diagonal
    diag_cm = DIAG_INCH * INCH_TO_CM
    diag_px = np.hypot(res_x, res_y)
    width_cm = diag_cm * (res_x / diag_px)
    height_cm = diag_cm * (res_y / diag_px)

    # Use hardcoded viewing distance
    dist_cm = VIEW_DIST_M * 100

    # Calculate pixel to cm conversion factors
    pix2cm_x = width_cm / res_x
    pix2cm_y = height_cm / res_y

    return {
        'res_x': res_x,
        'res_y': res_y,
        'width_cm': width_cm,
        'height_cm': height_cm,
        'pix2cm_x': pix2cm_x,
        'pix2cm_y': pix2cm_y,
        'dist_cm': dist_cm
    }

# 2. FIND ALL COORDINATES FILES (each in its own subfolder)
data_dir    = 'data'
pattern     = os.path.join(data_dir, '*', '*_coordinates.csv')
coord_files = glob.glob(pattern)
if not coord_files:
    raise RuntimeError(f"No files matching {pattern}")

# Containers for all data
all_summaries = []
all_full_data = []
all_cm_data = []

# 3. PROCESS EACH PARTICIPANT
for coords_path in coord_files:
    participant = os.path.basename(coords_path).replace('_coordinates.csv', '')
    participant_dir = os.path.dirname(coords_path)
    df = pd.read_csv(coords_path)

    # Load participant-specific hardware specs
    hardware_specs = load_hardware_specs(participant_dir, participant)
    screen_params = get_screen_params(hardware_specs)

    # Extract parameters for this participant
    pix2cm_x = screen_params['pix2cm_x']
    pix2cm_y = screen_params['pix2cm_y']
    dist_cm = screen_params['dist_cm']
    res_x = screen_params['res_x']
    res_y = screen_params['res_y']

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

    # px → cm for all landmarks
    df['nose_x_cm'] = df['nose_x_px'] * pix2cm_x
    df['nose_y_cm'] = df['nose_y_px'] * pix2cm_y
    df['lefteye_x_cm'] = df['lefteye_x_px'] * pix2cm_x
    df['lefteye_y_cm'] = df['lefteye_y_px'] * pix2cm_y
    df['righteye_x_cm'] = df['righteye_x_px'] * pix2cm_x
    df['righteye_y_cm'] = df['righteye_y_px'] * pix2cm_y
    df['mouth_x_cm'] = df['mouth_x_px'] * pix2cm_x
    df['mouth_y_cm'] = df['mouth_y_px'] * pix2cm_y

    # compute ellipse angular size (deg)
    df['ellipse_w_deg'] = 2 * np.degrees(
        np.arctan2(df['ellipse_w_cm'] / 2, dist_cm)
    )
    df['ellipse_h_deg'] = 2 * np.degrees(
        np.arctan2(df['ellipse_h_cm'] / 2, dist_cm)
    )

    # Add hardware info to dataframe
    df['resolution_x'] = res_x
    df['resolution_y'] = res_y
    df['viewing_dist_cm'] = dist_cm
    df['screen_width_cm'] = screen_params['width_cm']
    df['screen_height_cm'] = screen_params['height_cm']

    # console output
    pd.set_option('display.max_rows', None, 'display.max_columns', None)
    print(f"\n\n=== Participant: {participant} ===")
    print(f"    Resolution: {res_x}x{res_y} px")
    print(f"    Screen size: {screen_params['width_cm']:.1f}x{screen_params['height_cm']:.1f} cm")
    print(f"    Viewing distance: {dist_cm:.1f} cm")
    if hardware_specs:
        print(f"    (Using hardware specs from JSON)")
    else:
        print(f"    (Using default hardware parameters)")

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

    # Create dataframe with only cm/deg columns (no px) for summary
    cm_cols = ['identity',
               'ellipse_w_cm', 'ellipse_h_cm',
               'ellipse_w_deg', 'ellipse_h_deg',
               'nose_x_cm', 'nose_y_cm',
               'lefteye_x_cm', 'lefteye_y_cm',
               'righteye_x_cm', 'righteye_y_cm',
               'mouth_x_cm', 'mouth_y_cm']

    df_cm = df[cm_cols + ['resolution_x', 'resolution_y', 'viewing_dist_cm',
                          'screen_width_cm', 'screen_height_cm']].copy()
    df_cm.insert(0, 'participant', participant)

    # per-identity summary
    summary = (
        df[cm_cols]
        .groupby('identity')
        .mean()
        .round(2)
        .reset_index()
    )
    # tag with participant and hardware info
    summary.insert(0, 'participant', participant)
    summary['resolution'] = f"{res_x}x{res_y}"
    summary['viewing_dist_cm'] = dist_cm
    summary['screen_size_cm'] = f"{screen_params['width_cm']:.1f}x{screen_params['height_cm']:.1f}"

    print("\n-- Mean values by identity --")
    print(summary.to_string(index=False))

    # Add participant column to full data
    df.insert(0, 'participant', participant)

    # collect for combined tables
    all_summaries.append(summary)
    all_full_data.append(df)
    all_cm_data.append(df_cm)

# 5. COMBINE AND SAVE ALL DATA
# Combine full data (with px and cm)
combined_full = pd.concat(all_full_data, ignore_index=True)
combined_full_csv = os.path.join(data_dir, 'analysis_combined_full.csv')
combined_full.to_csv(combined_full_csv, index=False)

# Combine cm data (without px columns)
combined_cm = pd.concat(all_cm_data, ignore_index=True)
combined_cm_csv = os.path.join(data_dir, 'analysis_combined_cm.csv')
combined_cm.to_csv(combined_cm_csv, index=False)

print("\n=== Combined Data Across All Participants ===")
print(f"Total records in full data: {len(combined_full)}")
print(f"Total records in cm data: {len(combined_cm)}")
print(f"\nSaved combined full data (px + cm) -> {combined_full_csv}")
print(f"Saved combined cm data (no px)     -> {combined_cm_csv}\n")
