"""
Nativox — Keyword Translation stage
FastAPI backend + single-page frontend served from the same process.

Run from inside the backend/ folder:
    uvicorn main:app --reload --port 8011
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import LANG_CODES, LANG_LABELS
from app.schemas import (
    TranslateRequest,
    TranslateResponse,
    BatchTranslateRequest,
    BatchTranslateResponse,
)
from app.translate_service import translate_keyword, translate_keywords_batch

app = FastAPI(title="Nativox — Keyword Translation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "keyword-translation"}


@app.post("/api/translate", response_model=TranslateResponse)
def translate(request: TranslateRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        result = translate_keyword(text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Translation failed: {exc}")
    return result


@app.post("/api/translate-batch", response_model=BatchTranslateResponse)
def translate_batch(request: BatchTranslateRequest):
    target = request.target_language.strip().lower()
    if target not in LANG_CODES:
        raise HTTPException(
            status_code=400,
            detail=f"target_language must be one of: {', '.join(LANG_CODES.keys())}",
        )

    cleaned_keywords = [k for k in request.keywords if k and k.strip()]
    if not cleaned_keywords:
        raise HTTPException(status_code=400, detail="No non-empty keywords provided.")

    try:
        results = translate_keywords_batch(cleaned_keywords, target)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Translation failed: {exc}")

    return {
        "target_language": target,
        "target_label": LANG_LABELS[target],
        "results": results,
    }


# Serve the frontend's static assets (if any grow later: css/js files, etc.)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
