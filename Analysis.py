import pandas as pd
import matplotlib.pyplot as plt
import os

# — paths —
csv_path  = r'c:/Users/mingd/Downloads/imagineFaceExp/Data/mingda_faceLandmarks.csv'
eye_file  = r'c:/Users/mingd/Downloads/imagineFaceExp/Data/mingda_05_13_F1_Sentence_Eye_Tracking_SM_Eye_Tracking.txt'

# 1. Load landmarks (PsychoPy times in seconds)
landmarks = pd.read_csv(csv_path, comment='#')[['landmark','question_time']]

# 2. Read start_time + TobiiStream lines
tobii = []
with open(eye_file, 'r') as f:
    # 2a) the very first line is your Unix epoch start_time
    start_time = float(f.readline().strip())
    # 2b) now read through the rest, picking only TobiiStream samples
    for line in f:
        if not line.startswith('TobiiStream'):
            continue
        parts = line.split()
        try:
            ts_ns = float(parts[1])    # device-clock nanoseconds
            x     = float(parts[2])
            y     = float(parts[3])
        except ValueError:
            continue
        tobii.append({'t_ns': ts_ns, 'x': x, 'y': y})

tobii_df = pd.DataFrame(tobii)

# 3. Convert ms → seconds since stream start
tobii_df['t_s'] = tobii_df['t_ns'] / 1e3

# 4. Align the two clocks into a unified “experiment time”
#    assume landmark[0] (in PsychoPy secs) lines up with gaze[0] (in t_s)
first_q    = landmarks['question_time'].iloc[0]
first_gaze = tobii_df['t_s'].iloc[0]
offset     = first_q - first_gaze
tobii_df['t_exp'] = tobii_df['t_s'] + offset

# 5. Plot gaze from 1 s before up to each landmark, on a 1920×1080 coordinate frame
pre_window = 1.0  # seconds before landmark
for _, row in landmarks.iterrows():
    tq   = row['question_time']
    mask = (tobii_df['t_exp'] >= tq - pre_window) & (tobii_df['t_exp'] <= tq)
    seg  = tobii_df[mask]

    plt.figure()
    plt.scatter(seg['x'], seg['y'])
    # set the axis to full screen resolution:
    plt.xlim(0, 1920)
    plt.ylim(0,1080)             # inverted y (origin top-left)
    plt.title(f'Gaze in the 1 s before “{row["landmark"]}”')
    plt.xlabel('x (pixels)')
    plt.ylabel('y (pixels)')
    plt.show()



# 6. Compute and print normalized Unix-time spans
# 6a) Landmarks
landmark_unix      = start_time + landmarks['question_time']
landmark_unix_norm = landmark_unix - landmark_unix.iloc[0]
print(
    f'Landmarks Unix-time (normed): '
    f'first = {landmark_unix_norm.iloc[0]:.6f}s, '
    f'last  = {landmark_unix_norm.iloc[-1]:.6f}s'
)

# 6b) Tobii samples
tobii_unix      = start_time + tobii_df['t_s']
tobii_unix_norm = tobii_unix - tobii_unix.iloc[0]
print(
    f'Tobii   Unix-time (normed): '
    f'first = {tobii_unix_norm.iloc[0]:.6f}s, '
    f'last  = {tobii_unix_norm.iloc[-1]:.6f}s'
)
