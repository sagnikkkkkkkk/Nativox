"""
MP4 -> MP3 Extractor
---------------------
A tiny FastAPI backend that takes an uploaded video file, pulls out the
audio track with ffmpeg, and hands back an untouched MP3.

Run with:  uvicorn main:app --reload   (from the backend/ folder)
"""

import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
OUTPUT_DIR = BASE_DIR / "storage" / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
MAX_FILE_SIZE_MB = 500  # simple sanity cap

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="MP4 -> MP3 Extractor")

# Serve any static assets (css/js/images) the frontend might use later
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_frontend() -> str:
    """Serve the single-page frontend."""
    return (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/extract")
async def extract_audio(file: UploadFile = File(...)):
    """
    Accepts a video file, extracts its audio track as-is (re-encoded to
    MP3 without changing volume, speed, or content), and returns the file.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    job_id = uuid.uuid4().hex[:10]
    input_path = UPLOAD_DIR / f"{job_id}{suffix}"
    output_path = OUTPUT_DIR / f"{job_id}.mp3"

    # Save the upload to disk (streamed in chunks so large files don't blow up memory)
    size = 0
    with open(input_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                out_file.close()
                input_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit.")
            out_file.write(chunk)

    # Extract audio with ffmpeg: -vn drops video, libmp3lame + -q:a 2 is high-quality MP3
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    input_path.unlink(missing_ok=True)  # clean up the uploaded video regardless of outcome

    if result.returncode != 0 or not output_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"ffmpeg failed to extract audio: {result.stderr[-1000:]}",
        )

    download_name = Path(file.filename).stem + ".mp3"
    return FileResponse(
        path=output_path,
        media_type="audio/mpeg",
        filename=download_name,
    )
