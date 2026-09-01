"""
Thin wrapper around faster-whisper.

Loading a Whisper model is expensive (seconds to tens of seconds), so we
load each model size exactly once per process and cache it. This module
has no FastAPI-specific code so it can be unit tested or reused from a
CLI script if needed.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass, field

from faster_whisper import WhisperModel

from .config import DEVICE, COMPUTE_TYPE


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    language: str
    language_probability: float
    duration: float
    segments: list[Segment] = field(default_factory=list)


@functools.lru_cache(maxsize=2)
def _load_model(model_size: str) -> WhisperModel:
    """
    Cached model loader. lru_cache means the (potentially large) model
    weights are only loaded into memory once per model_size, the first
    time they're needed, then reused for every subsequent request.
    """
    return WhisperModel(model_size, device=DEVICE, compute_type=COMPUTE_TYPE)


def transcribe_audio(
    file_path: str,
    language: str | None,
    model_size: str,
) -> TranscriptionResult:
    """
    Run ASR on an audio file.

    language: a Whisper language code ("en", "hi", "bn") to force
        transcription in that language, or None to let Whisper
        auto-detect the spoken language.
    """
    model = _load_model(model_size)

    lang_arg = None if language in (None, "auto") else language

    segments_iter, info = model.transcribe(
        file_path,
        language=lang_arg,
        vad_filter=True,          # trims silence, improves segment quality
        beam_size=5,
    )

    segments: list[Segment] = []
    text_parts: list[str] = []
    for seg in segments_iter:
        cleaned = seg.text.strip()
        segments.append(Segment(start=seg.start, end=seg.end, text=cleaned))
        text_parts.append(cleaned)

    full_text = " ".join(text_parts).strip()

    return TranscriptionResult(
        text=full_text,
        language=info.language,
        language_probability=info.language_probability,
        duration=info.duration,
        segments=segments,
    )
