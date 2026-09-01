"""
Text to Keyword - backend entrypoint.

Run with:
    uvicorn main:app --reload --port 8010

Then open http://127.0.0.1:8010 in a browser - this same process serves
both the API (under /api) and the static frontend (everything else).
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.keyword_extractor import extract_keywords
from app.language_utils import LANG_LABELS

app = FastAPI(
    title="Text to Keyword",
    description=(
        "Extracts single-word keywords (no stopwords, no multi-word "
        "phrases) from English, Hindi, Bengali, and freely code-mixed "
        "text using a script-aware RAKE scoring algorithm."
    ),
    version="1.0.0",
)

# Permissive CORS so the frontend can be served separately during
# development (e.g. opened as a plain file, or from a different port).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    text: str = Field(..., description="Input text - English, Hindi, Bengali, or a mix")
    top_n: int = Field(15, ge=1, le=50, description="Maximum number of keywords to return")


class KeywordOut(BaseModel):
    word: str
    score: float
    relative_score: float
    language: str | None


class ExtractResponse(BaseModel):
    keywords: list[KeywordOut]
    language_labels: dict


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/extract-keywords", response_model=ExtractResponse)
def extract(req: ExtractRequest):
    keywords = extract_keywords(req.text, top_n=req.top_n)
    return {"keywords": keywords, "language_labels": LANG_LABELS}


# --- Serve the static frontend from the same process -----------------
_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
