#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import core, visual, event, data, gui, logging
import os
import random
import time    # ← for timestamps

# --- 1. EXPERIMENT SETUP ---------------------------------------------------

#add original 

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

win = visual.Window(fullscr=True,
                    allowGUI=False,
                    color=(0, 0, 0),
                    units='pix')

# --- 2. HELPER FUNCTIONS ---------------------------------------------------

def show_text(message):
    txt = visual.TextStim(win, text=message,
                          wrapWidth=800, height=24, color='white')
    txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])


def show_image_with_caption(image_name, caption_text):
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


def ask_landmarks(landmark_names):
    """
    For each landmark:
      1) show prompt
      2) wait for SPACE
      3) record the timestamp
    """
    for land in landmark_names:
        instr = visual.TextStim(win,
                                text=f"Please look at the {land} and press [space] when ready.",
                                pos=(0,300), height=24,
                                wrapWidth=800, color='white')
        instr.draw()
        win.flip()

        # wait for space, then timestamp
        event.waitKeys(keyList=['space'])
        question_timestamp = time.time()

        exp.addData('landmark', land)
        exp.addData('question_time', question_timestamp)
        exp.nextEntry()

    # clear screen after questions
    win.flip()

# --- 3. RUN PHASES ---------------------------------------------------------

# a) Welcome
show_text(
    "Welcome!\n\n"
    "In this experiment, you'll respond to a series of landmark prompts.\n\n"
    "Press [space] to begin."
)

# b) Memorization
show_image_with_caption(
    'face2.png',
    "From left to right: Lucia, Mark, and Donald.\n"
    "Please memorize their faces."
)

# c) Break
show_text(
    "You may now take a short break to complete an outside task.\n\n"
    "Press [space] when ready to continue."
)

# d) Visualization prompt
chosen = random.choice(['Lucia','Mark','Donald'])
show_text(
    f"Now, please recall and imagine {chosen}’s face on the screen.\n"
    "Press [space] when you're ready."
)

# e) Landmark questions (spacebar for each)
landmark_names = [
    'left ear', 'right ear',
    'chin', 'top of head'
]
ask_landmarks(landmark_names)

# f) Exit prompt
exit_instr = visual.TextStim(win,
                              text="Press [space] to end the experiment.",
                              pos=(0,-350), height=24,
                              wrapWidth=800, color='white')
exit_instr.draw()
win.flip()
event.waitKeys(keyList=['space'])

# g) Save & clean up
exp.saveAsWideText(exp.dataFileName + '.csv')
exp.saveAsPickle(exp.dataFileName + '.psydat')
logging.flush()
win.close()
core.quit()
