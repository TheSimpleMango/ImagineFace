import os
import glob
import matplotlib.pyplot as plt
import numpy as np
import csv

# === User‐adjustable variables ===
monitor_res = (1920, 1080)
screen_w, screen_h = monitor_res
aspect = screen_w / screen_h

# Scale factor (inches) for figure height; width is computed via aspect ratio
scale = 10.0  # ← adjust this as needed
fig_width = scale * aspect
fig_height = scale

viewing_distance_m = 0.6
viewing_distance_mm = viewing_distance_m * 1000.0

data_folder = "data"
# Figures folder as a sibling to data_folder (e.g., if data_folder="data", figures_folder="figures")
figures_folder = os.path.join(os.path.dirname(data_folder), "figures")


# === Helper Functions ===

def find_participants(folder):
    """
    Scan for all '*_event_log.csv' files in 'folder' and return
    a sorted list of participant IDs (filename prefix before '_event_log.csv').
    """
    pattern = os.path.join(folder, "*_event_log.csv")
    files = glob.glob(pattern)
    participants = []
    for path in files:
        base = os.path.basename(path)
        pid = base.replace("_event_log.csv", "")
        participants.append(pid)
    return sorted(set(participants))


def get_file_paths(participant, folder):
    """
    Given a participant ID and folder, return full paths to:
      - EVENT_FILE: '<participant>_event_log.csv'
      - EYE_FILE: the first file matching '<participant>_*FaceLandmark_Eye_Tracking.txt'
    Raises FileNotFoundError if either is not found.
    """
    event_path = os.path.join(folder, f"{participant}_event_log.csv")
    if not os.path.isfile(event_path):
        raise FileNotFoundError(f"No event log found for '{participant}'")
    eye_pattern = os.path.join(folder, f"{participant}_*FaceLandmark_Eye_Tracking.txt")
    eye_matches = glob.glob(eye_pattern)
    if len(eye_matches) == 0:
        raise FileNotFoundError(f"No eye‐tracking file found for '{participant}'")
    eye_path = eye_matches[0]
    return event_path, eye_path


def load_eye_data(eye_file):
    """
    Read eye‐tracking lines with 'TobiiStream' and return an Nx3 numpy array:
      [unix_time, x, y]
    """
    data = []
    with open(eye_file, "r") as f:
        for line in f:
            if "TobiiStream" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    unix_time = float(parts[0])
                    x = float(parts[3])
                    y = float(parts[4])
                    data.append([unix_time, x, y])
    return np.array(data)


def load_event_log(event_file):
    """
    Return a list of event dicts from the CSV. Each dict has string keys.
    """
    events = []
    with open(event_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)
    return events


def extract_faces_shown_window(events):
    """
    Scan events for 'faces_shown_start' and 'faces_shown_end' and return
    (start_time, end_time) as floats. Raises ValueError if not found.
    """
    start = None
    end = None
    for ev in events:
        if ev["event"] == "faces_shown_start":
            start = float(ev["unix_time"])
        if ev["event"] == "faces_shown_end":
            end = float(ev["unix_time"])
    if start is None or end is None:
        raise ValueError("Missing 'faces_shown_start' or 'faces_shown_end'")
    return start, end


def normalize_time(eye_data, events, t0):
    """
    Subtract t0 from eye_data[:,0] and from each ev['unix_time'].
    Modifies eye_data and events in place.
    """
    eye_data[:, 0] -= t0
    for ev in events:
        ev["unix_time"] = float(ev["unix_time"]) - t0


def extract_landmark_windows(events):
    """
    Parse events to build a list of dicts:
      {'identity': str, 'landmark': str, 'start': float, 'end': float}
    For each 'landmark_start'..'landmark_end' pair, capturing the most recent
    'visualization_prompt_<identity>_start' prior to landmark_start.
    """
    windows = []
    current = None
    identity = None

    for idx, ev in enumerate(events):
        if ev["event"] == "landmark_start":
            current = {
                "landmark": ev["label"],
                "start": float(ev["unix_time"])
            }
            # find most recent visualization_prompt_<id>_start
            for j in range(idx - 1, -1, -1):
                if events[j]["event"].startswith("visualization_prompt_") and "_start" in events[j]["event"]:
                    identity = events[j]["event"].replace("visualization_prompt_", "").replace("_start", "").capitalize()
                    break
            current["identity"] = identity
        elif ev["event"] == "landmark_end" and current is not None:
            current["end"] = float(ev["unix_time"])
            windows.append(current)
            current = None

    return windows


def compute_avg_gaze(eye_data, landmark_windows):
    """
    For each landmark window, compute the mean gaze x,y over the last 0.5s.
    Returns a list of dicts: {'identity','landmark','mean_x','mean_y','t_end'}.
    """
    results = []
    for lw in landmark_windows:
        t_end = lw["end"]
        t_start = t_end - 0.5
        mask = (eye_data[:, 0] >= t_start) & (eye_data[:, 0] <= t_end)
        pts = eye_data[mask]
        if len(pts) > 0:
            mx = np.mean(pts[:, 1])
            my = np.mean(pts[:, 2])
        else:
            mx, my = np.nan, np.nan
        results.append({
            "identity": lw["identity"],
            "landmark": lw["landmark"],
            "mean_x": mx,
            "mean_y": my,
            "t_end": t_end
        })
    return results


def get_gaze_coord(avg_points, identity, landmark):
    """
    Return (x,y) tuple for avg gaze where pt['identity'] matches identity
    and pt['landmark'] matches (ignoring case/underscores). Returns None if not found.
    """
    targets = [landmark.strip().lower(), landmark.strip().replace("_", " ")]
    for pt in avg_points:
        if pt["identity"] and pt["landmark"]:
            if (pt["identity"].strip().lower() == identity.strip().lower() and
                pt["landmark"].strip().lower() in targets):
                if not np.isnan(pt["mean_x"]) and not np.isnan(pt["mean_y"]):
                    return (pt["mean_x"], pt["mean_y"])
    return None


def angular_size_xy(p1, p2, px_x, px_y, vd_mm):
    """
    Compute angular size (in degrees) between two screen points p1, p2.
    p1, p2 are (x,y) in pixels. px_x, px_y are pixel sizes in mm. vd_mm is viewing distance in mm.
    """
    dx = (p2[0] - p1[0]) * px_x
    dy = (p2[1] - p1[1]) * px_y
    dist_mm = np.sqrt(dx**2 + dy**2)
    angle_rad = 2 * np.arctan2(dist_mm / 2, vd_mm)
    return np.degrees(angle_rad)


def face_height_cm(chin, top_head, px_x, px_y):
    """
    Compute physical face height (cm) between chin and top of head.
    chin, top_head are (x,y) in pixels. px_x, px_y are pixel sizes in mm.
    """
    dx = (chin[0] - top_head[0]) * px_x
    dy = (chin[1] - top_head[1]) * px_y
    dist_mm = np.sqrt(dx**2 + dy**2)
    return dist_mm / 10.0  # convert mm to cm


def plot_gaze_trajectory(fs_eye, participant, save_path):
    """
    Create and save a figure showing the gaze trajectory during faces_shown.
    """
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    if len(fs_eye) > 0:
        sc = ax.scatter(fs_eye[:, 1], fs_eye[:, 2], c=fs_eye[:, 0], cmap="plasma", s=4)
        ax.plot(fs_eye[:, 1], fs_eye[:, 2], alpha=0.1, color="gray")
        plt.colorbar(sc, ax=ax, label="Time (s, normalized)")
    ax.set_xlim(0, screen_w)
    ax.set_ylim(screen_h, 0)  # invert Y‐axis so (0,0) is top‐left
    ax.set_title(f"{participant}: Gaze Trajectory (Faces Memorization)")
    ax.set_xlabel("Screen X (pixels)")
    ax.set_ylabel("Screen Y (pixels)")
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def plot_identity_landmarks(avg_points, identity, color, save_path):
    """
    Create and save a figure plotting average gaze points for all landmarks of one identity.
    """
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    for pt in avg_points:
        if pt["identity"] and pt["identity"].lower() == identity.lower():
            mx, my = pt["mean_x"], pt["mean_y"]
            if not np.isnan(mx) and not np.isnan(my):
                ax.plot(mx, my, "o", color=color, markersize=15)
                ax.text(mx, my, pt["landmark"], fontsize=10, ha="center", va="center", color="black")
    ax.set_xlim(0, screen_w)
    ax.set_ylim(screen_h, 0)
    ax.set_title(f"{identity.capitalize()}: Landmark Averages")
    ax.set_xlabel("Screen X (pixels)")
    ax.set_ylabel("Screen Y (pixels)")
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def plot_landmark_trajectory(eye_data, lw, participant, save_path):
    """
    Create and save a figure showing the full gaze trajectory for a single landmark.
    lw is a dict with keys: 'identity', 'landmark', 'start', 'end' (all times normalized).
    """
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    mask = (eye_data[:, 0] >= lw["start"]) & (eye_data[:, 0] <= lw["end"])
    pts = eye_data[mask]
    if len(pts) > 0:
        sc = ax.scatter(pts[:, 1], pts[:, 2], c=pts[:, 0], cmap="plasma", s=4)
        ax.plot(pts[:, 1], pts[:, 2], alpha=0.1, color="gray")
        plt.colorbar(sc, ax=ax, label="Time (s, normalized)")
    ax.set_xlim(0, screen_w)
    ax.set_ylim(screen_h, 0)
    identity = lw["identity"].capitalize() if lw["identity"] else "Unknown"
    landmark = lw["landmark"]
    ax.set_title(f"{participant}: {identity} {landmark} Trajectory")
    ax.set_xlabel("Screen X (pixels)")
    ax.set_ylabel("Screen Y (pixels)")
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def compute_and_report_face_sizes(avg_points, participant):
    """
    Compute and print angular and physical face sizes for Mark and Helly if possible.
    """
    # Determine pixel size in mm
    monitor_diagonal_in = 24.0
    monitor_width_in = monitor_diagonal_in / np.sqrt(aspect**2 + 1) * aspect
    monitor_height_in = monitor_diagonal_in / np.sqrt(aspect**2 + 1)
    monitor_width_mm = monitor_width_in * 25.4
    monitor_height_mm = monitor_height_in * 25.4
    px_x = monitor_width_mm / screen_w
    px_y = monitor_height_mm / screen_h

    def compute_for(identity):
        chin = get_gaze_coord(avg_points, identity, "chin")
        top_head = get_gaze_coord(avg_points, identity, "top of head")
        left_ear = get_gaze_coord(avg_points, identity, "left ear")
        right_ear = get_gaze_coord(avg_points, identity, "right ear")
        if None not in [chin, top_head, left_ear, right_ear]:
            h_deg = angular_size_xy(chin, top_head, px_x, px_y, viewing_distance_mm)
            w_deg = angular_size_xy(left_ear, right_ear, px_x, px_y, viewing_distance_mm)
            h_cm = face_height_cm(chin, top_head, px_x, px_y)
            print(f"{participant} – {identity.capitalize()} – Gaze Height: {h_deg:.2f}° | "
                  f"Width: {w_deg:.2f}° | Height: {h_cm:.2f} cm")
        else:
            print(f"{participant} – {identity.capitalize()}: insufficient data for face‐size calculation.")

    print(f"\n=== Face Angular & Physical Size Results for {participant} (Gaze‐based) ===")
    print(f"Participant viewing distance: {viewing_distance_m:.2f} m")
    compute_for("mark")
    compute_for("helly")
    print("")


def process_participant(participant, folder, figures_root):
    """
    Full pipeline for one participant:
      1. Locate files
      2. Load eye data and compute average tracking rate
      3. Load and normalize event data
      4. Extract landmarks & compute averages
      5. Save plots and report results
    """
    # 1. Locate files
    event_file, eye_file = get_file_paths(participant, folder)
    print(f"\n--- Processing '{participant}' ---")
    print(f"Event log: {event_file}")
    print(f"Eye file:  {eye_file}")

    # 2. Load eye data
    eye_data = load_eye_data(eye_file)

    # Calculate average tracking rate (Hz) over the entire loaded eye_data
    if eye_data.shape[0] >= 2:
        start_t = eye_data[0, 0]
        end_t = eye_data[-1, 0]
        duration = end_t - start_t
        if duration > 0:
            rate_hz = (eye_data.shape[0] - 1) / duration
        else:
            rate_hz = np.nan
        print(f"{participant} – Average Eye‐Tracking Rate: {rate_hz:.2f} Hz")
    else:
        print(f"{participant} – Not enough eye data to compute tracking rate.")

    # 3. Load event log
    events = load_event_log(event_file)

    # 4. Extract faces_shown window
    start_fs, end_fs = extract_faces_shown_window(events)

    # 5. Normalize time (eyes & events)
    normalize_time(eye_data, events, start_fs)
    end_fs -= start_fs
    start_fs = 0.0

    # 6. Subset gaze during faces_shown
    fs_mask = (eye_data[:, 0] >= start_fs) & (eye_data[:, 0] <= end_fs)
    fs_eye = eye_data[fs_mask]

    # 7. Extract landmark windows & compute average gaze
    lm_windows = extract_landmark_windows(events)
    avg_points = compute_avg_gaze(eye_data, lm_windows)

    # 8. Report face sizes to console
    compute_and_report_face_sizes(avg_points, participant)

    # 9. Ensure participant’s figures directory exists
    participant_fig_dir = os.path.join(figures_root, participant)
    os.makedirs(participant_fig_dir, exist_ok=True)

    # 10. Save gaze trajectory plot
    gaze_save_path = os.path.join(participant_fig_dir, f"{participant}_gaze_trajectory.png")
    plot_gaze_trajectory(fs_eye, participant, gaze_save_path)

    # 11. Save landmark‐average plots for each identity if present
    identities = {pt["identity"].lower() for pt in avg_points if pt["identity"]}
    if "mark" in identities:
        mark_save_path = os.path.join(participant_fig_dir, f"{participant}_mark_landmarks.png")
        plot_identity_landmarks(avg_points, "mark", color="deepskyblue", save_path=mark_save_path)
    if "helly" in identities:
        helly_save_path = os.path.join(participant_fig_dir, f"{participant}_helly_landmarks.png")
        plot_identity_landmarks(avg_points, "helly", color="orange", save_path=helly_save_path)

    # 12. Save full trajectory for each landmark (start → end)
    for lw in lm_windows:
        identity_str = lw["identity"].lower() if lw["identity"] else "unknown"
        landmark_str = lw["landmark"].strip().lower().replace(" ", "_")
        filename = f"{participant}_{identity_str}_{landmark_str}_trajectory.png"
        save_path = os.path.join(participant_fig_dir, filename)
        plot_landmark_trajectory(eye_data, lw, participant, save_path)


# === Main Script: Loop through all participants ===
if __name__ == "__main__":
    # 1. Ensure figures_folder exists
    os.makedirs(figures_folder, exist_ok=True)

    # 2. Find participants and process each
    participants = find_participants(data_folder)
    if not participants:
        raise RuntimeError(f"No participants found in '{data_folder}'")
    for pid in participants:
        try:
            process_participant(pid, data_folder, figures_folder)
        except Exception as e:
            print(f"Error processing '{pid}': {e}")
