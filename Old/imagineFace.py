#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import core, visual, event, data, gui, logging
import os
import math
import random

# --- 1. EXPERIMENT SETUP ---------------------------------------------------

# Participant dialog
exp_info = {'participant': ''}
dlg = gui.DlgFromDict(exp_info, title='Face-Landmark Experiment')
if not dlg.OK:
    core.quit()

# Where we live
_thisDir = os.path.dirname(os.path.abspath(__file__))

# Data folder & ExperimentHandler
data_dir = os.path.join(_thisDir, 'data')
os.makedirs(data_dir, exist_ok=True)
file_base = f"{exp_info['participant']}_faceLandmarks"
exp = data.ExperimentHandler(name='FaceSize',
                             version='1.0',
                             extraInfo=exp_info,
                             originPath=__file__,
                             savePickle=True,
                             saveWideText=True,
                             dataFileName=os.path.join(data_dir, file_base))

# Window (pixel units so mouse coords are in px)
win = visual.Window(fullscr=True,
                    allowGUI=False,
                    color=(0, 0, 0),
                    units='pix')

# Mouse
mouse = event.Mouse(visible=True, win=win)

# Dictionary to hold pixel coordinates for each landmark
declared_coords = {}

# --- 2. HELPER FUNCTIONS ---------------------------------------------------

def show_text(message):
    """Draw a block of text, wait for SPACE."""
    txt = visual.TextStim(win, text=message,
                          wrapWidth=800, height=24, color='white')
    txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])


def show_image_with_caption(image_name, caption_text):
    """Display an image with a caption below, wait for SPACE."""
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


def collect_landmarks(landmark_names):
    """
    For each landmark:
      1) show prompt
      2) wait for click
      3) mark and record
    """
    markers = []
    for land in landmark_names:
        instr = visual.TextStim(win,
                               text=f"Please click on the {land}.",
                               pos=(0,300), height=24,
                               wrapWidth=800, color='white')
        instr.draw()
        win.flip()

        event.clearEvents(eventType='mouse')
        while True:
            if mouse.getPressed()[0]:
                x, y = mouse.getPos()
                core.wait(0.2)
                break

        marker = visual.Circle(win, radius=3,
                               fillColor='red', lineColor='red',
                               pos=(x, y))
        markers.append(marker)
        declared_coords[land] = (x, y)

        exp.addData('landmark', land)
        exp.addData('x_pix', x)
        exp.addData('y_pix', y)
        exp.nextEntry()

    win.flip()
    return markers

# --- 3. RUN PHASES ---------------------------------------------------------

# a) Welcome instructions
show_text(
    "Welcome!\n\n"
    "In this experiment, you'll click landmarks on three faces.\n\n"
    "Press [space] to begin."
)

# b) Memorization screen with caption
show_image_with_caption(
    'face2.png',
    "From left to right: Lucia, Mark, and Donald.\n"
    "Please memorize their faces."
)

# c) Mid-experiment break
show_text(
    "You may now take a short break to complete an outside task.\n\n"
    "Press [space] when ready to continue."
)

# d) Pre-landmark visualization prompt
chosen = random.choice(['Lucia', 'Mark', 'Donald'])
show_text(
    f"Now, please recall and imagine {chosen}’s face in front of you on the screen.\n"
    "Try to visualize it as close to reality as possible.\n\n"
    "Press [space] to continue."
)

# e) Collect landmarks
landmark_names = [
    'left ear', 'right ear',
#    'left eye', 'right eye',
#    'nose', 'mouth',
    'chin', 'top of head'
]
markers = collect_landmarks(landmark_names)

# f) Compute face size and record
# pixel distances
y_chin = declared_coords['chin'][1]
y_top = declared_coords['top of head'][1]
height_px = abs(y_chin - y_top)
x_left = declared_coords['left ear'][0]
x_right = declared_coords['right ear'][0]
width_px = abs(x_right - x_left)

# convert using 55" 4K display PPI
ppi = math.hypot(3840, 2160) / 55
cm_per_px = 2.54 / ppi
height_cm = height_px * cm_per_px
width_cm = width_px * cm_per_px

exp.addData('face_height_cm', round(height_cm,1))
exp.addData('face_width_cm', round(width_cm,1))
exp.nextEntry()

# g) Review points with exit prompt
for m in markers:
    m.draw()
exit_instr = visual.TextStim(win,
                              text="Press [space] to end the experiment.",
                              pos=(0,-350), height=24,
                              wrapWidth=800, color='white')
exit_instr.draw()
win.flip()
event.waitKeys(keyList=['space'])

# h) Thank-you and clean up
exp.saveAsWideText(exp.dataFileName + '.csv')
exp.saveAsPickle(exp.dataFileName + '.psydat')
logging.flush()
win.close()
core.quit()
