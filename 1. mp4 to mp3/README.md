# MP4 → MP3 Extractor

A tiny full-stack app: upload a video, get its audio track back as an MP3 — no
translation, no dubbing, just clean extraction. This is effectively a
standalone version of Stage 0 (Extract audio) from the Nativox pipeline.

## Stack

- **Backend:** FastAPI (Python) + ffmpeg (via subprocess)
- **Frontend:** Single-page HTML/CSS/JS, no build step, served directly by FastAPI

## Requirements

- Python 3.9+ (3.11 recommended)
- **ffmpeg** installed and available on your system PATH
  - Mac: `brew install ffmpeg`
  - Windows: `winget install Gyan.FFmpeg` (then restart your terminal/PC so PATH updates)
  - Linux: `sudo apt install ffmpeg`

## Quick start

**Mac/Linux:**
```bash
./run.sh
```

**Windows:**
```bat
run.bat
```

Either script creates a virtual environment, installs dependencies, and
starts the server. Once you see `Uvicorn running on http://127.0.0.1:8000`,
open that URL in your browser.

## Manual setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## How it works

1. You drop/select a video file (.mp4, .mov, .mkv, .avi, .webm, .m4v) in the browser.
2. The frontend POSTs it to `/extract`.
3. The backend saves it temporarily, runs:
   ```
   ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 2 output.mp3
   ```
4. The resulting MP3 is streamed back and the uploaded video is deleted.
5. You can preview it in the built-in audio player or download it.

## Project structure

```
mp4-to-mp3/
├── run.sh / run.bat
├── README.md
├── backend/
│   ├── main.py            # FastAPI app + /extract route
│   └── requirements.txt
├── frontend/
│   └── index.html         # Upload UI
└── storage/
    ├── uploads/            # Temp video storage (auto-cleared per request)
    └── outputs/            # Generated MP3s
```

## Notes / limitations

- Files are capped at 500 MB by default (edit `MAX_FILE_SIZE_MB` in `main.py` to change).
- Output MP3s accumulate in `storage/outputs/` — fine for a class project/demo,
  but for anything longer-lived you'd want a cleanup job or move to temp files.
- No auth — this is meant to run locally for a demo, not be exposed to the internet as-is.
