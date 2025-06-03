#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import core, visual, event, data, gui, logging, monitors
import os
import random
import time
import subprocess
import threading
import csv

import math

monitor_name = 'default'

# Physical display parameters
screen_width_cm = 53.0
screen_height_cm = 30.0
screen_distance_cm = 100.0  # viewing distance from participant in cm
screen_resolution = [1920, 1080]  # width x height in pixels

# Derived pixel size (cm/px)
px_per_cm_vert = screen_resolution[1] / screen_height_cm  # px/cm
cm_per_px_vert = screen_height_cm / screen_resolution[1]  # cm/px

# Image & face 1 pixel range (editable)
image_height_px = 1024
face1_top_px = 106
face1_bottom_px = 650
face2_top_px = 246
face2_bottom_px = 428

# Desired visual angle for face 1
target_angle_deg = 8.0


# === 1. EXPERIMENT SETUP ===
exp_info = {'participant': ''}
dlg = gui.DlgFromDict(exp_info, title='Face-Landmark Experiment')
if not dlg.OK:
    core.quit()

_thisDir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(_thisDir, 'data')
os.makedirs(data_dir, exist_ok=True)
file_base = f"{exp_info['participant']}_faceLandmarks"
exp = data.ExperimentHandler(
    name='FaceSize',
    version='1.0',
    extraInfo=exp_info,
    originPath=__file__,
    savePickle=True,
    saveWideText=True,
    dataFileName=os.path.join(data_dir, file_base)
)

# === EVENT LOGGING SETUP ===
event_log_path = os.path.join(data_dir, f"{exp_info['participant']}_event_log.csv")
event_log_file = open(event_log_path, 'w', newline='')
event_log_writer = csv.writer(event_log_file)
event_log_writer.writerow(['event', 'label', 'unix_time'])
event_log_file.flush()

def log_event(event_name, label=''):
    t = time.time()
    event_log_writer.writerow([event_name, label, t])
    event_log_file.flush()


mon = monitors.Monitor(monitor_name)
mon.setWidth(screen_width_cm)
mon.setDistance(screen_distance_cm)
mon.setSizePix(screen_resolution)
mon.saveMon()

# === VISUAL WINDOW ===
win = visual.Window(
    size=screen_resolution,
    fullscr=True,
    monitor=monitor_name,
    units='pix',
    color=(0, 0, 0),
    allowGUI=False,
    checkTiming=False
)
event.globalKeys.add(key='escape', func=core.quit, name='shutdown')

blank = visual.Rect(
    win,
    width=win.size[0],
    height=win.size[1],
    fillColor='black',
    lineColor='black'
)


# === FACE LANDMARK REGIONS (EDITABLE) ===
# Source image resolution
image_native_res = (1536, 1024)  # width x height

# Face 1 pixel bounds (top to bottom)
face1_top_px = 106
face1_bottom_px = 650

# Face 2 pixel bounds (top to bottom)
face2_top_px = 246
face2_bottom_px = 428

# Target angle in degrees for face 1
target_angle_deg = 8.0

# === CALCULATIONS ===
# Face 1 actual height in px and cm
face1_height_px = abs(face1_bottom_px - face1_top_px)
face1_height_cm = face1_height_px * cm_per_px_vert

# Convert height in cm to actual visual angle
face1_angle_rad = 2 * math.atan2(face1_height_cm / 2, screen_distance_cm)
face1_angle_deg = math.degrees(face1_angle_rad)

# Compute scaling factor to reach target angle
scaling_factor = target_angle_deg / face1_angle_deg

# Apply same scaling to face 2 and get its resulting visual angle
face2_height_px = abs(face2_bottom_px - face2_top_px)
face2_scaled_px = face2_height_px * scaling_factor
face2_scaled_cm = face2_scaled_px * cm_per_px_vert

face2_angle_rad = 2 * math.atan2(face2_scaled_cm / 2, screen_distance_cm)
face2_angle_deg = math.degrees(face2_angle_rad)

# === PRINT RESULTS (Optional) ===
print(f"[INFO] Face 1: {face1_height_px}px → {face1_angle_deg:.2f}°")
print(f"[INFO] Scaling factor to match {target_angle_deg}°: {scaling_factor:.3f}")
print(f"[INFO] Face 2: {face2_height_px}px → {face2_angle_deg:.2f}° (after scaling)")

# === 2. EYE TRACKING SETUP ===
def tobii_reader(proc, logfile_path, stop_flag):
    with open(logfile_path, 'a') as logfile:
        while not stop_flag['stop']:
            line = proc.stdout.readline()
            if not line:
                break
            logfile.write(f"{time.time()}\t{line.strip()}\n")
            logfile.flush()

eyetrack_proc = None
eyetrack_thread = None
eyetrack_stop_flag = {'stop': False}
eyetrack_file_path = None

def start_eyetracking(participant_name):
    global eyetrack_proc, eyetrack_thread, eyetrack_stop_flag, eyetrack_file_path
    date = time.strftime("%m_%d")
    log_dir = os.path.join(os.getcwd(), 'Data')
    os.makedirs(log_dir, exist_ok=True)
    file_name = f"{participant_name}_{date}_FaceLandmark_Eye_Tracking.txt"
    eyetrack_file_path = os.path.join(log_dir, file_name)

    with open(eyetrack_file_path, 'a') as logfile:
        logfile.write(f"{time.time()}\tEXPERIMENT_MARKER: Eye tracking started\n")

    eyetrack_proc = subprocess.Popen(
        ['TobiiStream\\TobiiStream.exe'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    eyetrack_stop_flag = {'stop': False}
    eyetrack_thread = threading.Thread(
        target=tobii_reader,
        args=(eyetrack_proc, eyetrack_file_path, eyetrack_stop_flag),
        daemon=True
    )
    eyetrack_thread.start()

def stop_eyetracking():
    global eyetrack_proc, eyetrack_thread, eyetrack_stop_flag
    if eyetrack_proc is not None:
        with open(eyetrack_file_path, 'a') as logfile:
            logfile.write(f"{time.time()}\tEXPERIMENT_MARKER: Eye tracking stopped\n")
        eyetrack_stop_flag['stop'] = True
        try:
            eyetrack_proc.terminate()
        except Exception:
            pass
        if eyetrack_thread:
            eyetrack_thread.join(timeout=2)

# === 3. HELPER FUNCTIONS ===
def show_text(message, label=None):
    if label:
        log_event(f"{label}_start")
    stim = visual.TextStim(win, text=message, wrapWidth=800, height=24, color='white')
    stim.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    if label:
        log_event(f"{label}_end")

def show_image_with_caption(fname, caption, label=None):
    if label:
        log_event(f"{label}_start")
    path = os.path.join(_thisDir, fname)
    if not os.path.isfile(path):
        raise IOError(f"Image not found: {path}")
    # When showing the image, apply scaling only on the height
    img = visual.ImageStim(
        win,
        image=os.path.join(_thisDir, 'face.png'),
        pos=(0, 150),
        size=(image_native_res[0], image_native_res[1] * scaling_factor)
    )

    cap = visual.TextStim(win, text=caption, pos=(0,-400), height=24, wrapWidth=800, color='white')
    img.draw()
    cap.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    if label:
        log_event(f"{label}_end")

def ask_landmarks(names, identity):
    rt_clock = core.Clock()
    rt_clock.reset()
    win.flip()
    for land in names:
        blank.draw()
        win.flip()
        instr = visual.TextStim(
            win,
            text=f"Please look at where you imagine their {land} to be and press [space] when you're looking at it.",
            pos=(0,300), height=24, wrapWidth=800, color='white'
        )
        # === LOG SCREEN START ===
        log_event('landmark_start', land)
        instr.draw()
        win.flip()
        event.waitKeys(keyList=['space'])
        # === LOG SCREEN END ===
        log_event('landmark_end', land)

        exp.addData('chosen_identity', identity)
        exp.addData('landmark', land)
        exp.addData('question_time', rt_clock.getTime())
        exp.nextEntry()
    win.flip()


# === 4. RUN PHASES ===
log_event('experiment_start')
start_eyetracking(exp_info['participant'])

show_text(
    "Welcome!\n\nPress [space] to begin.",
    label='welcome'
)

show_text(
    "Welcome!\n\nPress [space] to begin.",
    label='welcome'
)

show_image_with_caption(
    'face.png',
    "On the left is Helly and on the right is Mark.\nPlease memorize their faces.",
    label='faces_shown'
)

show_text(
    "You may now take a short break.\nPress [space] to continue.",
    label='break'
)

log_event('eyetracking_start')
with open(eyetrack_file_path, 'a') as lf:
    lf.write(f"{time.time()}\tEXPERIMENT_MARKER: Landmark questions started\n")

landmark_names = [
    'nose','left eye','right eye','mouth',
    'left ear','right ear','chin','top of head'
]

for identity in ['Mark', 'Helly']:
    show_text(
        f"Now, recall and imagine {identity}’s face as if they were right in front of you.\nPress [space] when ready.",
        label=f'visualization_prompt_{identity.lower()}'
    )
    ask_landmarks(landmark_names, identity)

show_text(
    "Press [space] to end the experiment.",
    label='experiment_exit'
)

log_event('experiment_end')

# Save and clean up
exp.saveAsWideText(exp.dataFileName + '.csv')
exp.saveAsPickle(exp.dataFileName + '.psydat')
logging.flush()
stop_eyetracking()

event_log_file.close()
core.wait(0.5)
win.close()
core.quit()
