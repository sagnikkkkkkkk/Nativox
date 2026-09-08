"""
Resilient translation engine with English-to-Hindi support and fallbacks.
"""
import json
import re
import urllib.parse
import urllib.request

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


def translate_to_hindi(text: str) -> str:
    """
    Translates text (sentence or paragraph) from English/Auto to Hindi.
    Includes automatic retry and fallback to MyMemory API if deep-translator fails.
    """
    text = (text or "").strip()
    if not text:
        return ""

    # 1. Primary: GoogleTranslator via deep-translator
    if GoogleTranslator is not None:
        try:
            translator = GoogleTranslator(source="auto", target="hi")
            result = translator.translate(text)
            if result and not result.startswith("Error"):
                return clean_hindi_output(result)
        except Exception:
            pass

    # 2. Resilient Fallback: MyMemory API
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|hi"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText")
            if translated and not translated.startswith("MYMEMORY WARNING"):
                return clean_hindi_output(translated)
    except Exception:
        pass

    # Fallback: return original text if all networks fail
    return text


def translate_to_english(text: str) -> str:
    """
    Translates text from Hindi/Auto to English.
    """
    text = (text or "").strip()
    if not text:
        return ""

    if GoogleTranslator is not None:
        try:
            translator = GoogleTranslator(source="auto", target="en")
            result = translator.translate(text)
            if result and not result.startswith("Error"):
                return result.strip()
        except Exception:
            pass

    try:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=hi|en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText")
            if translated and not translated.startswith("MYMEMORY WARNING"):
                return translated.strip()
    except Exception:
        pass

    return text


def clean_hindi_output(text: str) -> str:
    """
    Cleans punctuation and spacing artifacts in Hindi translation.
    Ensures standard Purna Virama (।) or period and trims extra whitespace.
    """
    text = re.sub(r"\s+", " ", text).strip()
    # Normalize ending punctuation
    if text and not text.endswith(("।", ".", "!", "?")):
        text += "।"
    return text

