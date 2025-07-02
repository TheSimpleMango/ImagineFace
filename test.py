from psychopy import prefs

# 1) (Optional) force PsychoPy to use PsychPortAudio (lowest latency)
prefs.hardware['audioLib'] = ['PTB']

# 2) Point at your speakers by name or by device‐index
#    You can list all output devices like this:
from pprint import pprint
import psychtoolbox.audio as pta
pprint(pta.get_devices())

# Suppose your speakers show up as index 2 in that list:
prefs.hardware['audioDevice'] = 2
#—or— by name:
# prefs.hardware['audioDevice'] = 'Speakers (Realtek High Definition Audio)'
