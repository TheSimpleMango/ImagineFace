#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import core, visual, event, data, gui, logging
import os
import random
import time
import subprocess
import threading
import csv

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

def log_event(event, label=''):
    t = time.time()
    event_log_writer.writerow([event, label, t])
    event_log_file.flush()

# === VISUAL WINDOW ===

win = visual.Window(fullscr=True,
                    allowGUI=False,
                    color=(0, 0, 0),
                    units='pix')

event.globalKeys.add(key='escape', func=core.quit, name='shutdown')

# === 2. EYE TRACKING SETUP ===

def tobii_reader(proc, logfile_path, stop_flag):
    with open(logfile_path, 'a') as logfile:
        while not stop_flag['stop']:
            line = proc.stdout.readline()
            if not line:
                break
            unix_time = time.time()
            logfile.write(f"{unix_time}\t{line.strip()}\n")
            logfile.flush()

eyetrack_proc = None
eyetrack_thread = None
eyetrack_stop_flag = {'stop': False}
eyetrack_file_path = None

def start_eyetracking(participant_name):
    global eyetrack_proc, eyetrack_thread, eyetrack_stop_flag, eyetrack_file_path
    date    = time.strftime("%m_%d")
    expName = 'FaceLandmark'
    log_dir = os.path.join(os.getcwd(), 'Data')
    os.makedirs(log_dir, exist_ok=True)
    file_name = f"{participant_name}_{date}_{expName}_Eye_Tracking.txt"
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
    global eyetrack_proc, eyetrack_thread, eyetrack_stop_flag, eyetrack_file_path
    if eyetrack_proc is not None:
        with open(eyetrack_file_path, 'a') as logfile:
            logfile.write(f"{time.time()}\tEXPERIMENT_MARKER: Eye tracking stopped\n")
        eyetrack_stop_flag['stop'] = True
        try:
            eyetrack_proc.terminate()
        except Exception:
            pass
        if eyetrack_thread is not None:
            eyetrack_thread.join(timeout=2)
        eytrack_proc = None
        eyetrack_thread = None

# === 3. HELPER FUNCTIONS ===

def show_text(message, event_label=None):
    if event_label:
        log_event(f"{event_label}_start")
    txt = visual.TextStim(win, text=message,
                          wrapWidth=800, height=24, color='white')
    txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    if event_label:
        log_event(f"{event_label}_end")

def show_image_with_caption(image_name, caption_text, event_label=None):
    if event_label:
        log_event(f"{event_label}_start")
    image_path = os.path.join(_thisDir, image_name)
    if not os.path.isfile(image_path):
        raise IOError(f"Image not found: {image_path}")
    img = visual.ImageStim(win, image=image_path, pos=(0,150))
    caption = visual.TextStim(win, text=caption_text,
                              pos=(0,-400), height=24,
                              wrapWidth=800, color='white')
    img.draw()
    caption.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    if event_label:
        log_event(f"{event_label}_end")

def ask_landmarks(landmark_names, chosen_identity):
    rt_clock = core.Clock()
    rt_clock.reset()
    for land in landmark_names:
        log_event('landmark_instruction_start', land)
        instr = visual.TextStim(win,
                                text=f"Please look at the {land} and press [space] when ready.",
                                pos=(0,300), height=24,
                                wrapWidth=800, color='white')
        instr.draw()
        win.flip()
        event.waitKeys(keyList=['space'])
        log_event('landmark_instruction_end', land)
        question_timestamp = rt_clock.getTime()
        exp.addData('chosen_identity', chosen_identity)
        exp.addData('landmark', land)
        exp.addData('question_time', question_timestamp)
        exp.nextEntry()
    win.flip()

# === 4. RUN PHASES ===

log_event('experiment_start')

# a) Welcome
show_text(
    "Welcome!\n\n"
    "In this experiment, you'll respond to a series of landmark prompts.\n\n"
    "Press [space] to begin.",
    event_label='welcome'
)

# b) Memorization (faces shown)
show_image_with_caption(
    'face3.png',
    "On the left is Helly and on the right is Mark.\nPlease memorize their faces.",
    event_label='faces_shown'
)

# c) Break
show_text(
    "You may now take a short break to complete an outside task.\n\n"
    "Press [space] when ready to continue.",
    event_label='break'
)

# d) Visualization prompt
chosen = random.choice(['Lucia','Mark','Donald'])
show_text(
    f"Now, please recall and imagine {chosen}’s face on the screen.\n"
    "Press [space] when you're ready.",
    event_label='visualization_prompt'
)

# e) Landmark questions (start eye tracking here!)
log_event('eyetracking_start')
start_eyetracking(exp_info['participant'])

with open(eyetrack_file_path, 'a') as logfile:
    logfile.write(f"{time.time()}\tEXPERIMENT_MARKER: Landmark questions started\n")

landmark_names = [
    'nose', 'left eye', 'right eye', 'mouth', 'left ear', 'right ear',
    'chin', 'top of head'
]
ask_landmarks(landmark_names, chosen)

# f) Exit prompt
show_text(
    "Press [space] to end the experiment.",
    event_label='experiment_exit'
)

log_event('experiment_end')

# g) Save & clean up
exp.saveAsWideText(exp.dataFileName + '.csv')
exp.saveAsPickle(exp.dataFileName + '.psydat')
logging.flush()

stop_eyetracking()

event_log_file.close()
core.wait(0.5)
win.close()
core.quit()
