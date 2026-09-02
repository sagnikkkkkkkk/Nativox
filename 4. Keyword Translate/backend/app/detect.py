"""
Script-based language detection for a single word or short phrase.

Rather than a statistical language-detection library (which is unreliable
on very short, single-word inputs), this counts which Unicode script the
characters belong to. For English/Hindi/Bengali this is fast and accurate,
since the three scripts don't overlap.
"""

from .config import DEVANAGARI_RANGE, BENGALI_RANGE


def detect_language(text: str) -> str:
    """
    Returns one of: "hindi", "bengali", "english".
    Falls back to "english" if the text has no letters at all
    (e.g. only punctuation or numbers).
    """
    devanagari_count = 0
    bengali_count = 0
    latin_count = 0

    for ch in text:
        code = ord(ch)
        if DEVANAGARI_RANGE[0] <= code <= DEVANAGARI_RANGE[1]:
            devanagari_count += 1
        elif BENGALI_RANGE[0] <= code <= BENGALI_RANGE[1]:
            bengali_count += 1
        elif ch.isalpha():
            latin_count += 1

    counts = {
        "hindi": devanagari_count,
        "bengali": bengali_count,
        "english": latin_count,
    }

    detected = max(counts, key=counts.get)

    # If every count is zero (no letters found), default to English.
    if counts[detected] == 0:
        return "english"

    return detected
