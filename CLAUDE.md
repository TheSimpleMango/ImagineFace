# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ImagineFace is a psychological research experiment that combines face visualization tasks with eye tracking. Participants are asked to imagine and draw faces using audio-only instructions while their eye movements are tracked using Tobii eye tracking hardware.

## Core Architecture

The project consists of several key components:

1. **Main Experiment (`imagineFaceNoClick.py`)** - The primary experiment script that:
   - Runs PsychoPy-based visual experiment with audio instructions
   - Integrates Tobii eye tracking via `TobiiStream.exe` 
   - Collects landmark coordinates as participants draw imagined faces
   - Saves experimental data and screenshots

2. **Analysis Pipeline (`Analysis.py`)** - Processes experimental data to:
   - Convert pixel coordinates to physical measurements (cm/degrees)
   - Compute face dimensions and angular sizes
   - Generate trajectory plots and statistical summaries
   - Combine data across participants

3. **Image Composition (`composeImg.py`)** - Creates stimuli by:
   - Placing people images into room backgrounds
   - Scaling based on visual angle requirements
   - Positioning for specific experimental conditions

4. **Eye Tracking Integration (`eye_tracker.py`)** - Standalone utility for eye tracking setup

## Key Dependencies

- **PsychoPy** - Core experiment framework with specific audio library preferences set to PTB → pyo → pygame
- **Tobii Eye Tracking SDK** - Hardware integration via `TobiiStream/` directory
- **PIL/Pillow** - Image processing for stimulus creation
- **pandas/numpy** - Data analysis and processing
- **matplotlib** - Plotting and visualization

## Data Structure

- `data/` - Contains participant data in timestamped folders:
  - `*_coordinates.csv` - Landmark positions and ellipse dimensions
  - `*_events.csv` - Experimental event timestamps
  - `*.png` - Screenshots of drawn faces
  - Analysis output files with full and summary statistics

- `eyetracking/` - Raw eye tracking data files
- `figures/` - Generated analysis plots organized by participant
- `audio/` - MP3 files for experimental instructions and cues

## Running the Experiment

The main experiment (`imagineFaceNoClick.py`) handles:
- Participant dialog and data folder creation
- Audio setup with interrupt controls (space/s to skip, escape to abort)
- Eye tracking process management 
- Sequential face drawing tasks with landmark collection
- Automatic data saving and cleanup

Key experimental flow:
1. Welcome and instruction phase
2. Face visualization tasks (Mark and Helly identities)
3. Landmark drawing with audio cues (nose, eyes, mouth, face outline)
4. Screenshot capture and coordinate logging
5. Analysis and summary generation

## Screen/Monitor Configuration

Critical parameters for visual angle calculations:
- Default: 1920×1080 resolution, 24" diagonal, 0.5m viewing distance
- Alternative: 2880×2800 resolution, 15.4" diagonal (configurable in Analysis.py)
- PsychoPy uses centered pixel coordinates (0,0) at screen center

## Development Notes

- Audio files must exist in root directory with specific naming convention
- Eye tracking requires Windows environment with Tobii hardware/drivers
- All coordinate data is in PsychoPy pixel units (center origin)
- Analysis scripts automatically detect and process all participant data
- Image composition uses visual angle calculations for precise stimulus sizing