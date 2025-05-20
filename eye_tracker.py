import psychopy
from psychopy import gui, core
import os, time
import subprocess

# --- experiment info --------------------------------
date    = time.strftime("%m_%d")
expName = 'F1_Sentence_Eye_Tracking_SM'
expInfo = {'Subject Name': ''}

dlg = gui.DlgFromDict(dictionary=expInfo, title=expName, sortKeys=False)
if not dlg.OK:
    core.quit()

# --- make sure Data/ exists ------------------------
data_dir = os.path.join(os.getcwd(), 'Data')
os.makedirs(data_dir, exist_ok=True)

# --- define output file path -----------------------
file_name = f"{expInfo['Subject Name']}_{date}_{expName}_Eye_Tracking.txt"
file_path = os.path.join(data_dir, file_name)

# --- record Unix start time at top of file ---------
start_time = time.time()
with open(file_path, 'w') as f:
    f.write(f"{start_time}\n")

# --- launch TobiiStream, appending to that file ----
command_line = f'cmd /k TobiiStream\\TobiiStream.exe >> "{file_path}"'
os.system(command_line)
