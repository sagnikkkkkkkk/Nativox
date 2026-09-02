# Nativox — Keyword Translation Stage

Translates a **list of keywords** — in any mix of **English**, **Hindi**, and **Bengali** —
into ONE target language you choose, all at once, preserving the order you gave them in.

Each keyword's source language is auto-detected individually (so a mixed list works fine),
but the target is a single choice for the whole batch — that's the piece that only makes
sense as a manual choice, since with multiple keywords "translate into the other two" isn't
well-defined the way it is for a single word.

Standalone full-stack sub-project (FastAPI backend + single-page frontend), same
pattern as the other Nativox pipeline stages (MP4→MP3, Transcribe, Text-to-Keyword).

Runs on **port 8011**, so it can run alongside the other stages without conflicts.

---

## How it works

1. **Detect** — checks which Unicode script the input uses (Devanagari → Hindi,
   Bengali script → Bengali, otherwise → English). No ML model needed, works
   reliably on single words.
2. **Translate** — sends the word to Google Translate (via `deep-translator`,
   same as the main Nativox pipeline's Translate stage) for the other two languages.
3. **Pronunciation guide** — the Hindi/Bengali translations are also transliterated
   into Roman letters (via `indic-transliteration`) so the pronunciation is readable
   even if you can't read the native script yet.

---

## Requirements

- Python 3.11 (not 3.14 — some dependencies don't have prebuilt wheels for it yet)
- Internet connection (Google Translate is a free public endpoint, no API key needed)

---

## Quick start

**Windows:**
```
.\run.bat
```

**Mac/Linux:**
```
./run.sh
```

Either script creates a virtual environment, installs dependencies, and starts the
server. Once it prints `Uvicorn running on http://127.0.0.1:8011`, open that URL in
a browser.

### If PowerShell blocks the script (Windows)

If you see an error about execution policies when running `.\run.bat`, that's a
PowerShell restriction on running local scripts. Fix it once with:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then run `.\run.bat` again.

---

## Manual setup (if you don't want to use the script)

```
cd backend
py -3.11 -m venv venv
venv\Scripts\activate        (Windows)   |   source venv/bin/activate   (Mac/Linux)
pip install -r requirements.txt
uvicorn main:app --reload --port 8011
```

**Important:** the `uvicorn` command must be run from inside the `backend/` folder,
not the project root — same rule as the other Nativox stages.

---

## API

### `POST /api/translate-batch`  (main endpoint, used by the frontend)

Request:
```json
{
  "keywords": ["water", "पानी", "আকাশ", "house"],
  "target_language": "hindi"
}
```

Response:
```json
{
  "target_language": "hindi",
  "target_label": "Hindi",
  "results": [
    { "original": "water", "detected_language": "english", "detected_label": "English",
      "translated_text": "पानी", "target_language": "hindi", "target_label": "Hindi", "pronunciation": "pani" },
    { "original": "पानी", "detected_language": "hindi", "detected_label": "Hindi",
      "translated_text": "पानी", "target_language": "hindi", "target_label": "Hindi", "pronunciation": "pani" },
    { "original": "আকাশ", "detected_language": "bengali", "detected_label": "Bengali",
      "translated_text": "आकाश", "target_language": "hindi", "target_label": "Hindi", "pronunciation": "aakaasha" },
    { "original": "house", "detected_language": "english", "detected_label": "English",
      "translated_text": "घर", "target_language": "hindi", "target_label": "Hindi", "pronunciation": "ghara" }
  ]
}
```

Order of `results` always matches the order of `keywords` in the request. If a keyword is
already in the target language, it's returned as-is (no unnecessary translation call).

### `POST /api/translate`  (single-keyword version, kept for the pipeline's other stages)

Request:
```json
{ "text": "पानी" }
```

Response:
```json
{
  "original": "पानी",
  "detected_language": "hindi",
  "detected_label": "Hindi",
  "translations": [
    { "language": "english", "label": "English", "text": "water", "pronunciation": null },
    { "language": "bengali", "label": "Bengali", "text": "জল", "pronunciation": "jala" }
  ]
}
```

### `GET /api/health`

Simple check that the server is up.

---

## Project structure

```
keyword-translate/
├── run.sh / run.bat
├── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── app/
│       ├── config.py            language codes + script Unicode ranges
│       ├── detect.py            script-based language detection
│       ├── translate_service.py translation + pronunciation logic
│       └── schemas.py           request/response models
└── frontend/
    └── index.html                single-page UI
```

---

## Known limitations

- Detection is script-based, not meaning-based — a Hindi and Bengali word that happen
  to share Sanskrit-derived spelling in Latin transliteration wouldn't come up (this
  only matters if you ever add romanized input; native-script input is unambiguous).
- Translation quality depends on Google Translate, same as the main pipeline's
  Translate stage — for a stronger academic contribution, this is a good place to
  plug in the planned IndicTrans2 comparison later.
- Pronunciation guides are algorithmic transliteration, not phonetic IPA — good
  enough for a quick read, not a substitute for hearing the word spoken (which is
  what the later TTS stage is for).

## Next steps toward full integration

- Swap in IndicTrans2 as an alternate translation backend and compare output quality
  against Google Translate for the report's measurable contribution.
- Feed this stage's output directly into the Text-to-Keyword stage's extracted
  keywords, so keyword translation becomes one hop in the full pipeline rather than
  a standalone lookup.
