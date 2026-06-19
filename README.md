# Smart Face Attendance

A desktop attendance system built with CustomTkinter and insightface (ArcFace). Uses face recognition to mark attendance — no manual roll calls.[](output.png)

## How it works

1. Register a student with their name and ID. The app captures 100 face samples from the webcam.
2. Train the model — computes face embeddings for each sample using ArcFace.
3. When you take attendance, the app opens the camera, detects faces via SCRFD, and matches embeddings against the trained set.
4. Attendance is saved to both SQLite and a date-wise CSV file.

## What I used

- Python 3.9+
- **CustomTkinter** — UI framework (modern tkinter wrapper)
- **insightface** (ArcFace MobileFaceNet + SCRFD detection) — face recognition pipeline
- **ONNX Runtime** — inference engine for the face model
- **OpenCV** (`opencv-contrib-python`) — camera capture, image processing
- **SQLite3** — local database (no server setup)
- **Pillow** — image handling for the UI

## Project structure

```
Smart Face Attendance/
├── main.py                          # Entry point
├── ui_theme.py                      # All UI and logic
├── database.py                      # SQLite CRUD operations
├── requirements.txt                 # Dependencies
├── .gitignore                       # Git ignore rules
├── attendance.db                    # SQLite database (auto-created)
├── TrainingImage/                   # Captured face samples (auto-created)
├── TrainingImageLabel/              # Trained embeddings .pkl (auto-created)
└── Attendance/                      # Date-wise CSV export (auto-created)
```

Only `main.py`, `ui_theme.py`, and `database.py` need to be in your repo. Everything else gets created automatically when you run the app.

## Setup

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Fix opencv conflict (insightface pulls both, keep only contrib)
pip uninstall opencv-python -y

# 5. Run
python main.py
```

**Note:** The first run will download the face model (~15MB) from GitHub to `~/.insightface/models/buffalo_sc/`. Internet required for first-time setup.

> `insightface` pulls `opencv-python` as a dependency, which conflicts with `opencv-contrib-python`. Just run `pip uninstall opencv-python -y` after installing requirements to fix it.

## How to use

### First time setup
- When you run the app, it will ask you to set a password. This is used for admin actions like clearing attendance.

### Register a student
1. Enter the student's Enrollment ID and Name.
2. Click **Take Images**. The camera opens and captures 100 face images.
3. Click **Save Profile** to train the recognizer on all saved profiles.

### Take attendance
1. Click **Take Attendance**. The camera opens.
2. It detects faces and marks them present if they match a trained profile.
3. Press **Q** to stop. Attendance is saved to both SQLite and a CSV file.

### Export / Refresh
- **Export Report** (File menu) — exports all attendance records to CSV.
- **Refresh** — reloads today's attendance from the database.
- **Clear Attendance** — deletes all attendance records (requires password).

## Tables (SQLite)

**students** — `serial`, `student_id`, `name`, `created_at`

**attendance** — `student_id`, `name`, `date`, `time`, `status`, `created_at`

**settings** — `key`, `value` (stores password and other config)

## Notes

- Face images are stored locally in `TrainingImage/` as color crops, not in the database.
- Face embeddings (512-dim vectors from ArcFace) are stored in `TrainingImageLabel/encodings.pkl`.
- The face recognition model (SCRFD + MobileFaceNet) is downloaded once from insightface's official repo.
- CSV exports are written to `Attendance/Attendance_DD-MM-YYYY.csv` every time attendance is taken.
- The app starts with an empty attendance table each day. All history is still in the database.
- Camera window shows "Press Q to quit" — make sure to press Q, not Escape.
- Minimum 1 student must be trained before Take Attendance works.
