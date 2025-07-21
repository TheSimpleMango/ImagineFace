#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face-Landmark Drawing Experiment with Audio-Only Instructions & Eye Tracking

Sections:
0.  Setup & Shutdown
1.  Paths & Audio Mapping
2.  Eye Tracking Setup
3.  Experiment Setup (Dialog + Data Folders)
4.  Monitor & Display Setup & Keyboard Initialization
5.  Helper Functions (show_text, show_image, draw_landmarks_and_ellipse)
6.  Run Experiment Flow
7.  Cleanup & Save
"""

import os
import csv
import time
import subprocess
import threading
from collections import OrderedDict
from psychopy import prefs, core, visual, event, data, gui, logging, monitors, sound
from psychopy.hardware import keyboard

# === 0. SETUP & SHUTDOWN ===
prefs.general['syncTests'] = []  # disable sync tests
prefs.hardware['audioLib'] = ['PTB', 'sounddevice', 'pyo', 'pygame']  # force PTB audio

clock = core.Clock()
exp = None
sound_dict = {}
eyetrack_proc = None
eyetrack_thread = None
eyetrack_stop_flag = {'stop': False}
eyetrack_file_path = None
kb = None  # low-level keyboard

def shutdown():
    """Clean shutdown: stop audio, eyetracking, and close window."""
    logging.flush()
    for snd in sound_dict.values():
        try:
            snd.stop()
        except:
            pass
    try:
        exp.abort()
    except:
        pass
    stop_eyetracking()
    try:
        win.close()
    except:
        pass
    core.quit()

# Bind Escape globally
event.globalKeys.add('escape', shutdown, name='shutdown')

# === 1. PATHS & AUDIO MAPPING ===
_thisDir = os.path.abspath(os.path.dirname(__file__))

audio_files = OrderedDict([
    ('welcome', 'Welcome.mp3'),
    ('faces_shown', 'Faces.mp3'),
    ('break', 'Break.mp3'),
    ('visualization_prompt_mark', 'Mark.mp3'),
    ('visualization_prompt_helly', 'Helly.mp3'),
    ('thank_you', 'End.mp3'),
])
landmark_audio = OrderedDict([
    ('nose', 'Nose.mp3'),
    ('lefteye', 'Left Eye.mp3'),
    ('righteye', 'Right Eye.mp3'),
    ('mouth', 'Mouth.mp3'),
    ('face', 'Face.mp3'),
])
_all_audio = OrderedDict()
_all_audio.update(audio_files)
_all_audio.update(landmark_audio)
for label, fname in _all_audio.items():
    path = os.path.join(_thisDir, fname)
    if not os.path.isfile(path):
        raise RuntimeError(f"Missing audio file '{fname}' in {_thisDir}")
    sound_dict[label] = sound.Sound(path, stereo=True)

# === 2. EYE TRACKING SETUP ===
def tobii_reader(proc, logfile_path, stop_flag):
    with open(logfile_path, 'a') as logfile:
        while not stop_flag['stop']:
            line = proc.stdout.readline()
            if not line:
                break
            logfile.write(f"{time.time()}\t{line.strip()}\n")
            logfile.flush()

def start_eyetracking(participant_name):
    global eyetrack_proc, eyetrack_thread, eyetrack_stop_flag, eyetrack_file_path
    now = time.strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(_thisDir, 'eyetracking')
    os.makedirs(log_dir, exist_ok=True)
    eyetrack_file_path = os.path.join(log_dir, f"{participant_name}_{now}_eyetrack.txt")
    with open(eyetrack_file_path, 'a') as lf:
        lf.write(f"{time.time()}\tEYE_TRACK_START\n")
    try:
        eyetrack_proc = subprocess.Popen([
            'TobiiStream\\TobiiStream.exe'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    except FileNotFoundError:
        logging.error("TobiiStream.exe not found; skipping eye tracking.")
        return
    eyetrack_stop_flag = {'stop': False}
    eyetrack_thread = threading.Thread(
        target=tobii_reader,
        args=(eyetrack_proc, eyetrack_file_path, eyetrack_stop_flag),
        daemon=True
    )
    eyetrack_thread.start()

def stop_eyetracking():
    global eyetrack_proc, eyetrack_thread, eyetrack_stop_flag
    if eyetrack_proc:
        with open(eyetrack_file_path, 'a') as lf:
            lf.write(f"{time.time()}\tEYE_TRACK_STOP\n")
        eyetrack_stop_flag['stop'] = True
        try:
            eyetrack_proc.terminate()
        except:
            pass
        eyetrack_thread.join(timeout=2)

# === 3. EXPERIMENT SETUP ===
exp_info = {'participant': ''}
dlg = gui.DlgFromDict(exp_info, title='Face-Landmark Drawing')
if not dlg.OK:
    shutdown()

data_root = os.path.join(_thisDir, 'data')
timestamp = time.strftime("%Y%m%d_%H%M")
participant_dir = os.path.join(data_root, f"{exp_info['participant']}_{timestamp}")
os.makedirs(participant_dir, exist_ok=True)

exp = data.ExperimentHandler(
    name='FaceDrawing', version='1.0', extraInfo=exp_info,
    originPath=__file__, savePickle=True, saveWideText=True,
    dataFileName=os.path.join(participant_dir, f"{exp_info['participant']}_faceDrawing")
)
coords_file = open(os.path.join(participant_dir, f"{exp_info['participant']}_coordinates.csv"), 'w', newline='')
coords_writer = csv.writer(coords_file)
coords_writer.writerow([
    'identity', 'nose_x', 'nose_y', 'ellipse_w', 'ellipse_h',
    'lefteye_x', 'lefteye_y', 'righteye_x', 'righteye_y', 'mouth_x', 'mouth_y'
])
event_log_file = open(os.path.join(participant_dir, f"{exp_info['participant']}_events.csv"), 'w', newline='')
event_log = csv.writer(event_log_file)
event_log.writerow(['event', 'label', 'time'])

def log_event(event_name, label=''):
    event_log.writerow([event_name, label, clock.getTime()])
    event_log_file.flush()

# === 4. DISPLAY & KEYBOARD ===
if 'FaceDrawingMonitor' not in monitors.getAllMonitors():
    mon = monitors.Monitor('FaceDrawingMonitor')
    mon.setWidth(53.0); mon.setDistance(100.0); mon.setSizePix([1920,1080]); mon.saveMon()
win = visual.Window(size=[1920,1080], fullscr=True, monitor='FaceDrawingMonitor', units='pix', color=(0,0,0), allowGUI=False, checkTiming=False)
win.winHandle.activate()
kb = keyboard.Keyboard()

# === 5. HELPERS ===
def play_interruptible(label):
    """Play audio; space skips & proceeds, 's' skips, 'escape' aborts."""
    snd = sound_dict[label]
    snd.play()
    kb.clearEvents()
    proceeded = False
    while snd.isPlaying:
        keys = kb.getKeys(['space','s','escape'], waitRelease=False)
        if 'escape' in keys:
            shutdown()
        if 'space' in keys:
            snd.stop(); proceeded = True; break
        if 's' in keys:
            snd.stop(); break
        core.wait(0.01)
    return proceeded

def show_text(msg, label):
    log_event(f"{label}_start", label)
    stim = visual.TextStim(win, text=msg, wrapWidth=800, height=24, color='white')
    stim.draw()
    win.flip()
    win.winHandle.activate()  # ensure window has focus for keypresses
    proceeded = play_interruptible(label)
    log_event(f"{label}_audio_end", label)
    kb.clearEvents()
    if not proceeded:
        kb.waitKeys(keyList=['space'])
    log_event(f"{label}_end", label)

def show_image(fname, caption, label):
    log_event(f"{label}_start", label)
    img = visual.ImageStim(win, image=os.path.join(_thisDir, fname))
    cap = visual.TextStim(win, text=caption, pos=(0,-400), height=24, wrapWidth=800, color='white')
    img.draw(); cap.draw()
    win.flip()
    win.winHandle.activate()  # ensure window has focus for keypresses
    proceeded = play_interruptible(label)
    log_event(f"{label}_audio_end", label)
    kb.clearEvents()
    if not proceeded:
        kb.waitKeys(keyList=['space'])
    log_event(f"{label}_end", label)

def draw_landmarks_and_ellipse(identity):
    """Draw nose, ellipse, other landmarks, screenshot, clear, and log."""
    win.flip(); core.wait(0.05)
    stims = []
    # Nose
    log_event(f"{identity}_nose_start", 'nose')
    play_interruptible('nose')
    mouse = event.Mouse(visible=True); mouse.clickReset(); prev=False
    while True:
        cur = mouse.getPressed()[0]
        if cur and not prev: break
        prev = cur; core.wait(0.01)
    nose_x, nose_y = mouse.getPos()
    dot_nose = visual.Circle(win, radius=5, pos=(nose_x, nose_y), fillColor='red', lineColor='red')
    dot_nose.autoDraw = True; stims.append(dot_nose)
    win.flip(); core.wait(0.1); log_event(f"{identity}_nose_end", 'nose')
    # Ellipse
    log_event(f"{identity}_ellipse_start", 'face')
    ellipse = visual.Polygon(win, edges=64, size=(1,1), pos=(nose_x, nose_y), fillColor=None, lineColor='white')
    ellipse.autoDraw = True; stims.append(ellipse)
    play_interruptible('face')
    mouse.clickReset(); prev=False
    while True:
        x,y = mouse.getPos(); ellipse.size = (abs(x-nose_x)*2, abs(y-nose_y)*2)
        win.flip(); pressed = mouse.getPressed()[0]
        if pressed and not prev: final_w, final_h = ellipse.size; break
        prev = pressed; core.wait(0.01)
    win.flip(); core.wait(0.05); log_event(f"{identity}_ellipse_end", 'face')
    # Other landmarks
    markers = {'nose': (nose_x,nose_y)}
    for lbl in ['lefteye','righteye','mouth']:
        log_event(f"{identity}_{lbl}_start", lbl)
        play_interruptible(lbl)
        mouse.clickReset(); prev=False
        while True:
            cur = mouse.getPressed()[0]
            if cur and not prev: break
            prev = cur; core.wait(0.01)
        x,y = mouse.getPos(); markers[lbl] = (x,y)
        dot = visual.Circle(win, radius=5, pos=(x,y), fillColor='red', lineColor='red')
        dot.autoDraw = True; stims.append(dot)
        win.flip(); core.wait(0.1); log_event(f"{identity}_{lbl}_end", lbl)
    # Screenshot
    shot = os.path.join(participant_dir, f"{exp_info['participant']}_{identity}.png")
    win.getMovieFrame(); win.saveMovieFrames(shot)
    # Clear
    for s in stims: s.autoDraw = False
    win.flip(); core.wait(0.1)
    # Log
    coords_writer.writerow([
        identity, nose_x, nose_y, final_w, final_h,
        markers['lefteye'][0],markers['lefteye'][1],markers['righteye'][0],markers['righteye'][1],markers['mouth'][0],markers['mouth'][1]
    ]); coords_file.flush()
    exp.addData('identity',identity); exp.addData('ellipse_size',f"{final_w:.1f}x{final_h:.1f}")
    for lbl,pos in markers.items(): exp.addData(f"{lbl}_pos",f"{pos[0]:.1f},{pos[1]:.1f}")
    exp.nextEntry()

# === 6. RUN EXPERIMENT ===
log_event('experiment_start'); start_eyetracking(exp_info['participant'])
show_text(" ", 'welcome'); show_image('room_with_people.png', " ", 'faces_shown')
show_text("Take a short break.\nPress [space] to continue.", 'break'); win.flip()
show_text(" ", 'visualization_prompt_mark'); draw_landmarks_and_ellipse('Mark')
show_text(" ", 'visualization_prompt_helly'); draw_landmarks_and_ellipse('Helly')
show_text("Thank you for participating!\n\nPress [space] to exit.", 'thank_you')

# === 7. CLEANUP & SAVE ===
log_event('experiment_end')
exp.saveAsWideText(os.path.join(participant_dir, f"{exp_info['participant']}_faceDrawing.csv"))
exp.saveAsPickle(os.path.join(participant_dir, f"{exp_info['participant']}_faceDrawing.psydat"))
stop_eyetracking()
event_log_file.close()
coords_file.close()
core.wait(0.5)
win.close()
core.quit()
