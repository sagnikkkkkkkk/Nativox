"""
Central configuration for the transcription service.
"""

# Languages exposed to the frontend.
# Keys are Whisper language codes (what faster-whisper expects).
SUPPORTED_LANGUAGES = {
    "auto": "Auto-detect",
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
}

# faster-whisper model size. "small" is a good CPU-friendly default;
# bump to "medium" or "large-v3" if a GPU is available and accuracy
# matters more than speed.
DEFAULT_MODEL_SIZE = "small"

# Device / compute type. "cpu" + "int8" runs everywhere with no GPU
# required. Switch to "cuda" + "float16" if a GPU is present.
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# Max upload size in megabytes (safety limit for the demo/prototype).
MAX_UPLOAD_MB = 100

# Audio file types accepted from the browser.
ALLOWED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".webm", ".mp4", ".mov"
}
