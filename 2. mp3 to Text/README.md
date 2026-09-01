# Nativox Transcribe

A standalone audio-to-text web app for **English, Hindi, and Bengali** — upload
a clip, get clean transcribed text back. Built as a focused, self-contained
piece of the Nativox pipeline (this is Stage 1: ASR, wrapped in its own
frontend and API).

- **Backend:** FastAPI + [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  (CTranslate2 build of OpenAI Whisper), running fully locally, CPU-friendly.
- **Frontend:** a single-page HTML/CSS/JS app, no build step, served directly
  by the backend.
- No paid API keys anywhere in the stack.

## Project structure

```
nativox-transcribe/
├── backend/
│   ├── main.py              FastAPI app: routes + serves the frontend
│   ├── requirements.txt
│   └── app/
│       ├── config.py        Languages, model size, upload limits
│       └── transcriber.py   faster-whisper wrapper (model caching, ASR call)
└── frontend/
    └── index.html           Upload UI, language picker, transcript display
```

## Setup

Requirements: **Python 3.11+** and an internet connection the first time you
run it (to download the Whisper model weights — a few hundred MB, cached
locally after that). `ffmpeg` is not strictly required (faster-whisper
decodes audio itself via PyAV), but having it on PATH helps with unusual
file formats.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000** — the backend serves the frontend from the
same process, so there's nothing else to start.

## How it works

1. You drop in an audio file (mp3, wav, m4a, aac, ogg, flac, or a video's
   audio track) and pick a language, or leave it on **Auto-detect**.
2. The frontend `POST`s the file to `/api/transcribe` as multipart form data.
3. The backend streams the upload to a temp file, runs it through
   faster-whisper (Voice Activity Detection filters silence first), and
   deletes the temp file immediately after.
4. The response includes the full transcript, per-segment timestamps, the
   detected language and confidence, and timing info — the frontend renders
   the transcript in the correct script (Devanagari for Hindi, Bengali script
   for Bengali) automatically.

## Configuration

Edit `backend/app/config.py`:

- `DEFAULT_MODEL_SIZE` — `tiny` / `base` / `small` (default) / `medium` /
  `large-v3`. Bigger = more accurate, slower, more RAM.
- `DEVICE` / `COMPUTE_TYPE` — set `DEVICE = "cuda"` and
  `COMPUTE_TYPE = "float16"` if you have a GPU available; CPU + int8 (the
  default) runs anywhere.
- `MAX_UPLOAD_MB` — upload size cap.

## Notes for the project report / viva

- Whisper (and by extension faster-whisper) was trained on multilingual
  data and supports Hindi and Bengali natively — no separate model per
  language is needed, which keeps this piece of the stack simple to defend.
- Auto-detection uses Whisper's built-in language ID pass; forcing a
  language (skipping auto-detect) is faster and more accurate when you
  already know what's being spoken, which is why the UI exposes both.
- The Whisper model is loaded once per process and cached (`lru_cache`) —
  worth mentioning if asked about performance, since reloading model weights
  per request would make every call several seconds slower.
- This is intentionally scoped to ASR only — no translation or TTS — so it
  can be demoed and evaluated (e.g. WER on English/Hindi/Bengali test clips)
  as its own clean unit, separate from the rest of the Nativox pipeline.
