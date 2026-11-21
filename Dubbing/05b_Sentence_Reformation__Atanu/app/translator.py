"""
Resilient, optimized translation engine with English-to-Hindi support,
high-precision domain vocabulary preservation, multiple fallbacks, and LRU caching.
"""
import functools
import json
import re
import urllib.parse
import urllib.request
from typing import Optional

from .config import HINDI_REFINEMENT_RULES, TECHNICAL_GLOSSARY

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

try:
    from deep_translator import MyMemoryTranslator as _MyMemoryTranslator
except ImportError:
    _MyMemoryTranslator = None

# Singleton MyMemoryTranslator instance (en-US -> hi-IN)
_mymemory_instance: Optional[object] = None


def _get_mymemory_translator():
    """Returns a reusable MyMemoryTranslator instance (en-US -> hi-IN)."""
    global _mymemory_instance
    if _MyMemoryTranslator is None:
        return None
    if _mymemory_instance is None:
        _mymemory_instance = _MyMemoryTranslator(source="en-US", target="hi-IN")
    return _mymemory_instance


# Bilingual phrase mapping for offline/sandbox fallback
OFFLINE_WORD_MAP = {
    "hello": "नमस्ते",
    "world": "दुनिया",
    "this": "यह",
    "is": "है",
    "a": "एक",
    "an": "एक",
    "test": "परीक्षण",
    "video": "वीडियो",
    "we": "हम",
    "i": "मैं",
    "you": "आप",
    "they": "वे",
    "explore": "अन्वेषण करते हैं",
    "explores": "अन्वेषण करता है",
    "discuss": "चर्चा करते हैं",
    "discusses": "चर्चा करता है",
    "explain": "समझाते हैं",
    "explains": "समझाता है",
    "train": "प्रशिक्षित करते हैं",
    "model": "मॉडल",
    "models": "मॉडल",
    "and": "और",
    "or": "या",
    "in": "में",
    "on": "पर",
    "with": "के साथ",
    "to": "को",
    "for": "के लिए",
    "of": "का",
    "learn": "सीखते हैं",
    "learning": "लर्निंग",
    "today": "आज",
    "understand": "समझते हैं",
    "accurate": "सटीक",
    "accurately": "सटीक रूप से",
    "speech": "स्पीच",
    "recognition": "रिकग्निशन",
    "machine": "मशीन",
    "neural": "न्यूरल",
    "network": "नेटवर्क",
    "networks": "नेटवर्क",
    "computer": "कंप्यूटर",
    "vision": "विज़न",
    "natural": "नेचुरल",
    "language": "लैंग्वेज",
    "processing": "प्रोसेसिंग",
    "audio": "ऑडियो",
    "alignment": "संरेखण",
    "deep": "डीप",
    "data": "डेटा",
    "dataset": "डेटासेट",
    "code": "कोड",
    "algorithm": "एल्गोरिदम",
    "architecture": "आर्किटेक्चर",
}


def _offline_translate_fallback(text: str) -> str:
    """
    Offline fallback translator: converts known technical terms and general words
    into Devanagari Hindi so translation never fails even without network access.
    """
    text = (text or "").strip()
    if not text:
        return ""

    if re.search(r"[\u0900-\u097F]", text):
        return clean_hindi_output(text)

    # Replace multi-word technical phrases first
    lowered = text.lower()
    for phrase, hi_equiv in TECHNICAL_GLOSSARY.items():
        pattern = r"\b" + re.escape(phrase) + r"\b"
        lowered = re.sub(pattern, hi_equiv, lowered, flags=re.IGNORECASE)

    # Replace single words
    tokens = re.split(r"(\s+|[,;.!?।])", lowered)
    translated_tokens = []
    for token in tokens:
        stripped = token.strip()
        lower_token = stripped.lower()
        if lower_token in OFFLINE_WORD_MAP:
            translated_tokens.append(token.replace(stripped, OFFLINE_WORD_MAP[lower_token]))
        elif lower_token in TECHNICAL_GLOSSARY:
            translated_tokens.append(token.replace(stripped, TECHNICAL_GLOSSARY[lower_token]))
        else:
            translated_tokens.append(token)

    result = "".join(translated_tokens).strip()
    if not result.endswith(("।", ".", "!", "?")):
        result += "।"
    return clean_hindi_output(result)


@functools.lru_cache(maxsize=4096)
def _fetch_chrome_ext_translation(text: str, target_lang: str = "hi") -> Optional[str]:
    """
    Fast and highly resilient translation via Chrome extension API.
    Does not suffer from 429 rate limits common on the mobile GTX endpoint.
    """
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={target_lang}&q={encoded}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data:
                first = data[0]
                if isinstance(first, list) and first:
                    return str(first[0]).strip()
                elif isinstance(first, str):
                    return first.strip()
    except Exception:
        pass
    return None


@functools.lru_cache(maxsize=4096)
def _fetch_gtx_translation(text: str, source_lang: str = "auto", target_lang: str = "hi") -> Optional[str]:
    """Google Translate GTX endpoint with full multi-part extraction."""
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={encoded}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AndroidTranslate/6.20.0 (Linux; U; Android 11; Pixel 5)"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data and isinstance(data[0], list):
                parts = []
                for part in data[0]:
                    if isinstance(part, list) and part and isinstance(part[0], str):
                        parts.append(part[0])
                    elif isinstance(part, str):
                        parts.append(part)
                out = "".join(parts).strip()
                if out:
                    return out
    except Exception:
        pass
    return None


@functools.lru_cache(maxsize=1024)
def _fetch_mymemory_translation(text: str, target_lang: str = "hi") -> Optional[str]:
    """Fallback translation via MyMemory raw API."""
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|{target_lang}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText")
            if translated and not translated.startswith("MYMEMORY WARNING"):
                if re.search(r"[\u0900-\u097F]", translated):
                    return translated.strip()
    except Exception:
        pass
    return None


def refine_hindi_translation(english_source: str, hindi_text: str) -> str:
    """
    Lightly refines raw machine-translated Hindi without any hardcoded verb or pronoun rules.
    Only applies:
    1. Bracket/list artifact stripping (e.g. ['...', 'en'])
    2. Domain vocabulary corrections from HINDI_REFINEMENT_RULES (config.py)
    3. Whitespace and punctuation cleanup
    4. Final Devanagari purna virama standardization
    """
    if not hindi_text:
        return ""

    refined = hindi_text

    # Strip any accidental brackets or list artifacts like ['...', 'en']
    if refined.startswith("['") and "']" in refined:
        m = re.match(r"^\[\s*['\"](.+?)['\"]\s*,\s*['\"][a-zA-Z]+['\"]\s*\]", refined)
        if m:
            refined = m.group(1)

    # Apply domain vocabulary refinement rules (e.g. कलन -> कैलकुलस, तंत्रिका नेटवर्क -> न्यूरल नेटवर्क)
    for pattern, replacement in HINDI_REFINEMENT_RULES:
        refined = re.sub(pattern, replacement, refined)

    # Clean double spaces and punctuation artifacts
    refined = re.sub(r"\s+", " ", refined).strip()
    refined = re.sub(r"\s+([।,?!;:])", r"\1", refined)
    refined = re.sub(r"([।,?!])([^\s0-9])", r"\1 \2", refined)

    # Standardize final punctuation to Devanagari purna virama
    if refined and not refined.endswith(("।", "!", "?")):
        if refined.endswith("."):
            refined = refined[:-1] + "।"
        else:
            refined += "।"

    return refined


def translate_to_hindi(text: str) -> str:
    """
    High-fidelity English to Hindi translation.
    Tier order:
      1. MyMemoryTranslator (deep-translator) — primary; semantically accurate, natural NLP
      2. Chrome Extension API — fast Google fallback
      3. GTX (translate.googleapis.com) — fallback
      4. deep-translator GoogleTranslator — fallback
      5. MyMemory raw API — fallback
      6. Offline dictionary — last resort
    """
    text = (text or "").strip()
    if not text:
        return ""

    raw_translated: Optional[str] = None

    # Tier 1: MyMemoryTranslator — genuinely accurate NLP, no hardcoding needed
    translator = _get_mymemory_translator()
    if translator is not None:
        try:
            result = translator.translate(text)
            if result and re.search(r"[\u0900-\u097F]", result) and not result.startswith("MYMEMORY WARNING"):
                raw_translated = result.strip()
        except Exception:
            pass

    # Tier 2: Chrome Extension translation endpoint
    if not raw_translated:
        raw_translated = _fetch_chrome_ext_translation(text, target_lang="hi")

    # Tier 3: Direct Google Translate GTX
    if not raw_translated:
        raw_translated = _fetch_gtx_translation(text, source_lang="auto", target_lang="hi")

    # Tier 4: deep-translator GoogleTranslator if installed
    if not raw_translated and GoogleTranslator is not None:
        try:
            g_translator = GoogleTranslator(source="auto", target="hi")
            result = g_translator.translate(text)
            if result and not result.startswith("Error") and re.search(r"[\u0900-\u097F]", result):
                raw_translated = result.strip()
        except Exception:
            pass

    # Tier 5: MyMemory raw API
    if not raw_translated:
        raw_translated = _fetch_mymemory_translation(text, target_lang="hi")

    # Tier 6: Offline dictionary & transliteration fallback
    if not raw_translated or not re.search(r"[\u0900-\u097F]", raw_translated):
        raw_translated = _offline_translate_fallback(text)

    # Post-processing and refinement
    polished = refine_hindi_translation(text, raw_translated)
    return clean_hindi_output(polished)


def translate_to_english(text: str) -> str:
    """
    Translates Hindi text to English with fallbacks and caching.
    """
    text = (text or "").strip()
    if not text:
        return ""

    # Tier 1: Chrome extension
    res = _fetch_chrome_ext_translation(text, target_lang="en")
    if res:
        return res.strip()

    # Tier 2: GTX
    res = _fetch_gtx_translation(text, source_lang="hi", target_lang="en")
    if res:
        return res.strip()

    # Tier 3: deep-translator
    if GoogleTranslator is not None:
        try:
            translator = GoogleTranslator(source="hi", target="en")
            result = translator.translate(text)
            if result and not result.startswith("Error"):
                return result.strip()
        except Exception:
            pass

    # Tier 4: MyMemory
    res = _fetch_mymemory_translation(text, target_lang="en")
    if res:
        return res.strip()

    return text


def clean_hindi_output(text: str) -> str:
    """
    Cleans punctuation and spacing artifacts in Hindi translation.
    Ensures standard Purna Virama (।) or period and trims extra whitespace.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if text.endswith("."):
        text = text[:-1] + "।"
    elif text and not text.endswith(("।", "!", "?")):
        text += "।"
    return text
