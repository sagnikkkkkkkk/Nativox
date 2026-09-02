"""
Config for the Keyword Translation stage.

Only three languages are supported anywhere in this app:
English, Hindi, Bengali.
"""

# Google Translate language codes used by deep-translator
LANG_CODES = {
    "english": "en",
    "hindi": "hi",
    "bengali": "bn",
}

# Human-readable labels, in the order shown in the UI
LANG_LABELS = {
    "english": "English",
    "hindi": "Hindi",
    "bengali": "Bengali",
}

# Unicode block ranges used for script-based language detection.
# (Same idea as the script-aware detection already used in the
# Text-to-Keyword stage — no external ML model needed.)
DEVANAGARI_RANGE = (0x0900, 0x097F)   # Hindi
BENGALI_RANGE = (0x0980, 0x09FF)      # Bengali
