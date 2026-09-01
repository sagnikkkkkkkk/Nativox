"""
Nativox Transcribe — standalone audio-to-text service.

Run with:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000 in a browser.
"""
from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    ALLOWED_EXTENSIONS,
    DEFAULT_MODEL_SIZE,
    MAX_UPLOAD_MB,
    SUPPORTED_LANGUAGES,
)
from app.transcriber import transcribe_audio

app = FastAPI(title="Nativox Transcribe", version="1.0.0")

# Wide-open CORS is fine for a local prototype; tighten this before any
# real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/api/languages")
def get_languages():
    """Languages the frontend should offer in its selector."""
    return {"languages": SUPPORTED_LANGUAGES}


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model_size: str = Form(DEFAULT_MODEL_SIZE),
):
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language '{language}'.")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # Stream to a temp file while enforcing the size cap, rather than
    # reading the whole upload into memory first.
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    written = 0

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                tmp.close()
                os.unlink(tmp_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds the {MAX_UPLOAD_MB}MB limit.",
                )
            tmp.write(chunk)

    try:
        start = time.perf_counter()
        result = transcribe_audio(tmp_path, language=language, model_size=model_size)
        elapsed = time.perf_counter() - start
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the client
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    finally:
        os.unlink(tmp_path)

    return {
        "text": result.text,
        "language": result.language,
        "language_label": SUPPORTED_LANGUAGES.get(result.language, result.language),
        "language_probability": round(result.language_probability, 3),
        "audio_duration_sec": round(result.duration, 2),
        "processing_time_sec": round(elapsed, 2),
        "segments": [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text}
            for s in result.segments
        ],
    }


# --- Serve the frontend from the same process ---------------------------
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
