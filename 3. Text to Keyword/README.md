# Text to Keyword

A standalone module (usable on its own, or as Stage 3 — "Keyword
extraction" — of the larger Nativox dubbing pipeline) that extracts
**single-word** keywords — no stopwords, no multi-word phrases — from
text in **English**, **Hindi**, **Bengali**, and **freely code-mixed
combinations of the three**, with a FastAPI backend and a single-page
frontend.

## What makes this a multilingual/code-mixed extractor (not three separate ones)

The naive approach to "support three languages" is to run language
identification on the whole input, route it to one of three separate
per-language NLP pipelines, then merge the outputs. That breaks the
moment a sentence switches languages mid-line — which is exactly how
people actually type in Hindi/Bengali/English contexts.

Instead, this project adapts **RAKE (Rapid Automatic Keyword
Extraction)** so the *language-sensitive* part of the algorithm — the
stopword list used to find content words — is the union of all three
languages' stopwords, applied in a single pass. The output is
**single-word keywords only** — no stopwords, no multi-word phrases:

1. Split the input into sentences (on `. ! ? , ; :` and the Devanagari/
   Bengali danda `।`).
2. Within each sentence, walk word by word. A run of consecutive
   **content words** (i.e. not in the combined English+Hindi+Bengali
   stopword set) forms a **candidate phrase**. This step still matters
   for single-word output: it's what guarantees a word like "am", "is",
   "are", "was", "were" (or their Hindi/Bengali equivalents) can never
   reach the results — they're filtered out before scoring even starts.
3. Score each unique word by `degree(word) / frequency(word)`, where
   `degree` counts how often that word co-occurs with other content
   words inside candidate phrases. This rewards words that show up in
   richer contexts, not just words that repeat a lot.
4. Rank individual words by that score and return the top N.
5. Separately (and only for *display*), each returned word is
   script-tagged by its Unicode block (Latin / Devanagari / Bengali) so
   the UI can label it English, Hindi, or Bengali.

Because step 2 never needs to know "what language is this sentence,"
code-mixed input such as *"ei video ta te amra ekta automated dubbing
system use korchi"* is handled by the exact same code path as a
monolingual sentence — there's no separate "mixed mode."

This is a deliberately lightweight, dependency-free, and auditable
algorithm (good for a viva walkthrough), rather than a black-box
transformer pipeline. The natural "next step" comparison for a project
report is benchmarking this against a transformer-based multilingual
keyphrase model (e.g. a multilingual KeyBERT variant) — see *Future
Work* below.

## Project structure

```
nativox-keyword-extractor/
├── run.sh / run.bat          # one-command launcher
├── backend/
│   ├── main.py                # FastAPI app (serves API + frontend)
│   ├── requirements.txt
│   └── app/
│       ├── keyword_extractor.py   # the RAKE-multilingual algorithm
│       ├── language_utils.py      # Unicode-script word/phrase tagging
│       └── stopwords.py           # curated EN / HI / BN stopword lists
└── frontend/
    └── index.html             # single-page UI (no build step)
```

## Running it

```bash
./run.sh          # Mac/Linux
.\run.bat         # Windows
```

Either script creates a virtual environment, installs dependencies, and
starts the server. Once you see `Uvicorn running on
http://127.0.0.1:8010`, open that URL — the backend serves the frontend
from the same process (no CORS issues, nothing else to run).

**Manual setup**, if you'd rather not use the script:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8010
```

## API

`POST /api/extract-keywords`

```json
{ "text": "your text here", "top_n": 15 }
```

```json
{
  "keywords": [
    {
      "word": "translation",
      "score": 4.0,
      "relative_score": 100.0,
      "language": "en"
    }
  ],
  "language_labels": {"en": "English", "hi": "Hindi", "bn": "Bengali", "mixed": "Mixed"}
}
```

`GET /api/health` — simple liveness check.

## Frontend

`frontend/index.html` is a single static file — a textarea, a "script
mix" meter that live-updates as you type (percentage of Latin /
Devanagari / Bengali characters), sample buttons for each language and
for code-mixed text, and a ranked results list where each keyword's
left border color shows its detected script.

## Known limitations (useful for the report's "Limitations" section)

- Stopword lists are curated by hand (60–100 entries per language) for
  this prototype's scope — a production system would use larger,
  linguistically-reviewed stopword resources.
- Script detection is per-character Unicode-block based; it correctly
  separates Latin/Devanagari/Bengali but doesn't distinguish, e.g.,
  Hindi from other Devanagari-script languages, or English from other
  Latin-script languages — out of scope since only these three
  languages are targeted.
- Output is single words only by design (per project requirements);
  multi-word named entities or fixed phrases (e.g. "machine
  translation") are returned as separate words rather than as one unit.
- No stemming/lemmatization, so morphological variants of a word (e.g.
  Hindi verb forms) are currently scored as distinct tokens.

## Future work

- Compare this RAKE-multilingual approach against a transformer-based
  multilingual keyphrase extractor (e.g. multilingual KeyBERT / YAKE)
  as a measurable evaluation section for the project report.
- Feed extracted keywords into Nativox's keyword-anchored translation
  consistency layer (Stage 4 of the full dubbing pipeline).
- Add simple stemming for Hindi/Bengali to merge morphological
  variants before scoring.
