"""
Stage: Keyword Translation
Translates a word/keyword between English, Hindi, and Bengali,
and adds a Roman-script pronunciation guide for the Hindi/Bengali output.
"""

from deep_translator import GoogleTranslator
from indic_transliteration import sanscript

from .config import LANG_CODES, LANG_LABELS
from .detect import detect_language

# Which sanscript scheme to use per language, for transliteration
# INTO Roman letters (pronunciation guide).
SCRIPT_SCHEME = {
    "hindi": sanscript.DEVANAGARI,
    "bengali": sanscript.BENGALI,
}


def _translate_text(text: str, source_lang: str, target_lang: str) -> str:
    source_code = LANG_CODES[source_lang]
    target_code = LANG_CODES[target_lang]
    translator = GoogleTranslator(source=source_code, target=target_code)
    return translator.translate(text)


def _pronunciation(text: str, language: str) -> str | None:
    """Roman-script pronunciation guide. None for English (not needed)."""
    if language not in SCRIPT_SCHEME:
        return None
    try:
        romanized = sanscript.transliterate(
            text, SCRIPT_SCHEME[language], sanscript.ITRANS
        )
        return romanized.lower()
    except Exception:
        # Transliteration is a nice-to-have; never let it break the request.
        return None


def translate_keyword_to(text: str, target_lang: str) -> dict:
    """
    Detects the language of `text`, then translates it into ONE
    specific target language (used by the batch endpoint, where the
    caller picks a single target for the whole list of keywords).

    If the detected language already IS the target language, no
    translation call is made — the original text is returned as-is.
    """
    text = text.strip()
    detected = detect_language(text)

    if detected == target_lang:
        translated_text = text
    else:
        translated_text = _translate_text(text, detected, target_lang)

    return {
        "original": text,
        "detected_language": detected,
        "detected_label": LANG_LABELS[detected],
        "translated_text": translated_text,
        "target_language": target_lang,
        "target_label": LANG_LABELS[target_lang],
        "pronunciation": _pronunciation(translated_text, target_lang),
    }


def translate_keywords_batch(keywords: list[str], target_lang: str) -> list[dict]:
    """
    Translates a list of keywords, IN ORDER, into a single target language.
    Each keyword's source language is detected independently, so a mixed
    list (some English, some Hindi, some Bengali) works fine.
    """
    results = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        results.append(translate_keyword_to(kw, target_lang))
    return results


def translate_keyword(text: str) -> dict:
    """
    Detects the language of `text` (English / Hindi / Bengali),
    then translates it into the other two languages.

    Returns a dict shaped like:
    {
        "original": "पानी",
        "detected_language": "hindi",
        "detected_label": "Hindi",
        "translations": [
            {"language": "english", "label": "English", "text": "water", "pronunciation": None},
            {"language": "bengali", "label": "Bengali", "text": "জল", "pronunciation": "jala"}
        ]
    }
    """
    text = text.strip()
    detected = detect_language(text)

    other_languages = [lang for lang in LANG_CODES.keys() if lang != detected]

    translations = []
    for target_lang in other_languages:
        translated_text = _translate_text(text, detected, target_lang)
        translations.append({
            "language": target_lang,
            "label": LANG_LABELS[target_lang],
            "text": translated_text,
            "pronunciation": _pronunciation(translated_text, target_lang),
        })

    return {
        "original": text,
        "detected_language": detected,
        "detected_label": LANG_LABELS[detected],
        "translations": translations,
    }
