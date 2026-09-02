from pydantic import BaseModel, Field
from typing import List, Optional


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class Translation(BaseModel):
    language: str
    label: str
    text: str
    pronunciation: Optional[str] = None


class TranslateResponse(BaseModel):
    original: str
    detected_language: str
    detected_label: str
    translations: List[Translation]


class BatchTranslateRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, max_length=200)
    target_language: str = Field(..., description="one of: english, hindi, bengali")


class BatchTranslateItem(BaseModel):
    original: str
    detected_language: str
    detected_label: str
    translated_text: str
    target_language: str
    target_label: str
    pronunciation: Optional[str] = None


class BatchTranslateResponse(BaseModel):
    target_language: str
    target_label: str
    results: List[BatchTranslateItem]
