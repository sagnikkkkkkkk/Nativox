"""
Nativox — Stage 5: Sentence Reformation & Précis Compression Service
Handles:
  1. Task 1: Reconstructing meaningless/broken sentences into meaningful Hindi.
  2. Task 2: Compressing full spoken MP3 transcript paragraphs into a 35% - 40% Hindi Précis.
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.precis import generate_precis
from app.reformer import reconstruct_sentence
from app.schemas import (
    PipelineRequest,
    PipelineResponse,
    PrecisRequest,
    PrecisResponse,
    ReconstructRequest,
    ReconstructResponse,
)

app = FastAPI(
    title="Nativox — Sentence Reformation & Précis",
    description="Transforms disfluent or fragmented speech into meaningful Hindi, and compresses full MP3 transcripts into 35%-40% précis summaries.",
    version="1.0.0",
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "stage-5-sentence-reformation-precis",
        "supported_pair": "english-to-hindi",
    }


@app.post("/api/reconstruct", response_model=ReconstructResponse)
def reconstruct_endpoint(request: ReconstructRequest):
    """
    Task 1: Meaningless / Fragmented Sentence -> Meaningful Hindi Sentence.
    Removes verbal fillers, repairs syntax, and produces grammatically sound Hindi.
    """
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        result = reconstruct_sentence(text, target_lang=request.target_language)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reconstruction error: {exc}") from exc


@app.post("/api/precis", response_model=PrecisResponse)
def precis_endpoint(request: PrecisRequest):
    """
    Task 2: Full MP3 Paragraph -> 35% to 40% Précis Compression in Hindi.
    Extracts key information while enforcing strict word budgeting.
    """
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input paragraph cannot be empty.")

    try:
        result = generate_precis(
            text,
            min_ratio=request.min_ratio,
            max_ratio=request.max_ratio,
            target_lang=request.target_language,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Précis generation error: {exc}") from exc


@app.post("/api/pipeline", response_model=PipelineResponse)
def pipeline_endpoint(request: PipelineRequest):
    """
    Unified 2-Step Pipeline requested by Sir:
    Step 1: First, make the sentence meaningful from input keywords or speech.
    Step 2: Then, generate the precise (35%-40% compressed) output in Hindi and English.
    """
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        # Step 1: Meaningful Sentence Formulation
        reconstruct_res = reconstruct_sentence(text, target_lang=request.target_language)
        step1_eng = reconstruct_res["cleaned_english"]
        step1_hi = reconstruct_res["meaningful_hindi"]
        removed_fillers = reconstruct_res["removed_fillers"]

        # Step 2: Precise 35%-40% Condensation
        orig_words = len(text.split())
        if orig_words > 20:
            precis_res = generate_precis(
                text,
                min_ratio=request.min_ratio,
                max_ratio=request.max_ratio,
                target_lang=request.target_language,
            )
            step2_eng = precis_res["precis_english"]
            step2_hi = precis_res["precis_hindi"]
            precise_words = precis_res["precis_word_count"]
            ratio_pct = precis_res["retention_ratio_pct"]
            is_budget = precis_res["is_within_budget"]
        else:
            step2_eng = step1_eng
            step2_hi = step1_hi
            precise_words = len(step2_eng.split())
            ratio_pct = round((precise_words / orig_words) * 100, 1) if orig_words else 100.0
            is_budget = True

        return {
            "original_input": text,
            "original_words": orig_words,
            "step1_meaningful_english": step1_eng,
            "step1_meaningful_hindi": step1_hi,
            "step1_removed_fillers": removed_fillers,
            "step2_precise_english": step2_eng,
            "step2_precise_hindi": step2_hi,
            "precise_words": precise_words,
            "retention_ratio_pct": ratio_pct,
            "is_within_budget": is_budget,
            "notes": "Step 1: Meaning restored from keywords. Step 2: Precise budget applied.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc


# Serve frontend static assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Nativox Stage 5 Backend is Running. Frontend not found."}


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.webp", include_in_schema=False)
def favicon():
    fav = FRONTEND_DIR / "favicon.webp"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/webp")
    raise HTTPException(status_code=404, detail="Favicon not found")

