"""
Lightweight, dependency-free language detection based on Unicode script
ranges. This is what lets the extractor handle English/Hindi/Bengali
*and* code-mixed text in a single pass: every word is classified by
which script its characters belong to, rather than trying to guess the
language of the whole sentence up front.
"""

DEVANAGARI_RANGE = (0x0900, 0x097F)   # Hindi (and other Devanagari-script langs)
BENGALI_RANGE = (0x0980, 0x09FF)      # Bengali / Assamese script

LANG_LABELS = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "mixed": "Mixed",
}


def char_script(ch: str):
    """Return 'hi', 'bn', 'en', or None for a single character."""
    cp = ord(ch)
    if DEVANAGARI_RANGE[0] <= cp <= DEVANAGARI_RANGE[1]:
        return "hi"
    if BENGALI_RANGE[0] <= cp <= BENGALI_RANGE[1]:
        return "bn"
    if ch.isalpha():
        # Any other alphabetic character (Latin, accented Latin, etc.)
        # is treated as English for this project's scope.
        return "en"
    return None


def detect_word_lang(word: str):
    """Classify a single token by the majority script of its characters."""
    counts = {"en": 0, "hi": 0, "bn": 0}
    for ch in word:
        script = char_script(ch)
        if script:
            counts[script] += 1
    total = sum(counts.values())
    if total == 0:
        return None
    return max(counts, key=counts.get)


def detect_phrase_lang(word_langs):
    """
    Given the per-word language tags of a candidate phrase, decide the
    phrase's overall label: a single language if every word agrees,
    otherwise 'mixed'.
    """
    langs = {l for l in word_langs if l}
    if not langs:
        return None
    if len(langs) == 1:
        return next(iter(langs))
    return "mixed"
