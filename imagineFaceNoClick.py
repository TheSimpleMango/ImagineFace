#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Face-Landmark Drawing Experiment
• Robust Escape via globalKeys
• Per-phase landmark-by-landmark drawing with persistent strokes
• Records full drawn-pixel sequences per landmark and phase
• Single-frame screenshot of each phase’s cumulative drawing
"""

import os
import json
import csv
from collections import OrderedDict
from psychopy import prefs, core, visual, event, data, gui, logging, monitors, sound

# === Force PTB Audio Backend ===
prefs.hardware['audioLib'] = ['PTB', 'sounddevice', 'pyo', 'pygame']

# === 0. SETUP & SHUTDOWN ===
clock = core.Clock()
exp = None
sound_dict = {}

def shutdown():
    """Stop everything cleanly and quit."""
    logging.flush()
    for snd in sound_dict.values():
        try:
            snd.stop()
        except Exception:
            pass
    try:
        event_log_file.close()
    except Exception:
        pass
    try:
        if exp:
            exp.abort()
    except Exception:
        pass
    try:
        win.close()
    except Exception:
        pass
    core.quit()

event.globalKeys.add('escape', shutdown, name='shutdown')

# === 1. PATHS & AUDIO MAPPING ===
_thisDir = os.path.abspath(os.path.dirname(__file__))
origin_path = __file__ if '__file__' in globals() else None

# phase prompts + standard audio
audio_files = OrderedDict([
    ('welcome',                   'welcome.mp3'),
    ('faces_shown',               'faces.mp3'),
    ('break',                     'break.mp3'),
    ('visualization_prompt_mark', 'markvis.mp3'),
    ('visualization_prompt_helly','hellyvis.mp3'),
    ('thank_you',                 'thankyou.mp3'),
])

# individual landmark cues
landmark_audio = OrderedDict([
    ('nose',     'nose.mp3'),
    ('mouth',    'mouth.mp3'),
    ('lefteye',  'lefteye.mp3'),
    ('righteye', 'righteye.mp3'),
    ('face',     'face.mp3')
])

# combine and load
_all_audio = OrderedDict()
_all_audio.update(audio_files)
_all_audio.update(landmark_audio)
for label, fname in _all_audio.items():
    path = os.path.join(_thisDir, fname)
    if not os.path.isfile(path):
        raise RuntimeError(f"Missing audio file '{fname}' in {_thisDir}")
    sound_dict[label] = sound.Sound(path, stereo=True)


def play_interruptible(label):
    """Play audio, allow S to skip audio only, Space to skip and proceed, Escape to quit."""
    snd = sound_dict[label]
    snd.play()
    event.clearEvents(eventType='keyboard')
    proceed = False
    while snd.isPlaying:
        keys = event.getKeys(keyList=['s', 'space', 'escape'])
        if 'escape' in keys:
            shutdown()
        if 'space' in keys:
            snd.stop()
            log_event('sound_skipped', label)
            proceed = True
            break
        if 's' in keys:
            snd.stop()
            log_event('sound_skipped', label)
            break
        core.wait(0.01)
    return proceed

# === 2. EXPERIMENT SETUP ===
exp_info = {'participant': ''}
dlg = gui.DlgFromDict(exp_info, title='Face-Landmark Drawing')
if not dlg.OK:
    shutdown()

data_dir = os.path.join(_thisDir, 'data')
os.makedirs(data_dir, exist_ok=True)
file_base = f"{exp_info['participant']}_faceDrawing"
exp = data.ExperimentHandler(
    name='FaceDrawing', version='1.0',
    extraInfo=exp_info, originPath=origin_path,
    savePickle=True, saveWideText=True,
    dataFileName=os.path.join(data_dir, file_base)
)

# === 3. EVENT LOGGING ===
event_log_file = open(
    os.path.join(data_dir, f"{exp_info['participant']}_events.csv"),
    'w', newline=''
)
event_log = csv.writer(event_log_file)
event_log.writerow(['event', 'label', 'time'])

def log_event(event_name, label=''):
    event_log.writerow([event_name, label, clock.getTime()])
    event_log_file.flush()

# === 4. MONITOR & DISPLAY SETUP ===
if 'FaceDrawingMonitor' not in monitors.getAllMonitors():
    mon = monitors.Monitor('FaceDrawingMonitor')
    mon.setWidth(53.0)
    mon.setDistance(100.0)
    mon.setSizePix([1920, 1080])
    mon.saveMon()

win = visual.Window(
    size=[1920, 1080], fullscr=True,
    monitor='FaceDrawingMonitor', units='pix',
    color=(0, 0, 0), allowGUI=False
)

# helper to show text with audio
def show_text(msg, label):
    log_event(f"{label}_start", label)
    stim = visual.TextStim(win, text=msg, wrapWidth=800,
                           height=24, color='white')
    stim.draw(); win.flip()
    proceeded = play_interruptible(label)
    log_event(f"{label}_audio_end", label)
    event.clearEvents(eventType='keyboard')
    if not proceeded:
        event.waitKeys(keyList=['space'])
    log_event(f"{label}_end", label)

# helper to show image with audio
def show_image(fname, caption, label):
    log_event(f"{label}_start", label)
    img = visual.ImageStim(win, image=os.path.join(_thisDir, fname))
    cap = visual.TextStim(win, text=caption, pos=(0, -400),
                          height=24, wrapWidth=800, color='white')
    img.draw(); cap.draw(); win.flip()
    proceeded = play_interruptible(label)
    log_event(f"{label}_audio_end", label)
    event.clearEvents(eventType='keyboard')
    if not proceeded:
        event.waitKeys(keyList=['space'])
    log_event(f"{label}_end", label)

# helper for per-landmark drawing with persistent strokes
def phase_landmark_draw(phase_label, landmarks):
    log_event(f"{phase_label}_start")
    event.clearEvents(eventType='keyboard')
    mouse = event.Mouse(win=win, visible=True)
    all_strokes = []
    for lm in landmarks:
        log_event(f"{phase_label}_{lm}_start", lm)
        play_interruptible(lm)
        log_event(f"{phase_label}_{lm}_audio_end", lm)
        pts = []
        drawing = True
        while drawing:
            if mouse.getPressed()[0]:
                x, y = mouse.getPos(); pts.append((float(x), float(y)))
            for stroke in all_strokes:
                for i in range(1, len(stroke)):
                    visual.Line(win, start=stroke[i-1], end=stroke[i],
                                lineColor='white', lineWidth=3).draw()
            for i in range(1, len(pts)):
                visual.Line(win, start=pts[i-1], end=pts[i],
                            lineColor='white', lineWidth=3).draw()
            win.flip()
            if 'space' in event.getKeys(['space']):
                drawing = False
        log_event(f"{phase_label}_{lm}_end", lm)
        all_strokes.append(pts)
        exp.addData('phase', phase_label)
        exp.addData('landmark', lm)
        exp.addData('drawn_pixels', json.dumps(pts))
        exp.nextEntry()
    log_event(f"{phase_label}_end")
    return all_strokes

# === 5. RUN EXPERIMENT ===
log_event('experiment_start')

show_text(" ", 'welcome')
show_image('room_with_people.png', " ", 'faces_shown')
show_text("Take a short break.\nPress [space] to continue.", 'break')
win.flip()

landmarks = list(landmark_audio.keys())
# MARK phase
play_interruptible('visualization_prompt_mark')
mark_strokes = phase_landmark_draw('mark', landmarks)
win.getMovieFrame()
mark_file = os.path.join(data_dir, f"{exp_info['participant']}_mark.png")
win.saveMovieFrames(mark_file)
win.flip()

# HELLY phase
play_interruptible('visualization_prompt_helly')
helly_strokes = phase_landmark_draw('helly', landmarks)
win.getMovieFrame()
helly_file = os.path.join(data_dir, f"{exp_info['participant']}_helly.png")
win.saveMovieFrames(helly_file)

# final thank-you
show_text("Thank you for participating!\nPress [space] to exit.", 'thank_you')

# === 6. CLEANUP & SAVE ===
exp.saveAsWideText(os.path.join(data_dir, file_base + '.csv'))
exp.saveAsPickle(os.path.join(data_dir, file_base + '.psydat'))
log_event('experiment_end')
event_log_file.close()
core.wait(0.5)
win.close()
core.quit()
