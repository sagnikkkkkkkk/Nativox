"""
Script-aware multilingual keyword extraction (single-word output).

Approach
--------
This is a RAKE (Rapid Automatic Keyword Extraction) variant adapted to
work across English, Hindi, Bengali and free code-mixing of the three,
without running separate per-language NLP pipelines and merging results.

Standard RAKE scores multi-word phrases. This project only needs
single-word keywords, so the algorithm keeps RAKE's *scoring* idea but
changes what gets returned:

  1. Split text into sentences on punctuation.
  2. Within each sentence, cut at stopwords - a maximal run of
     consecutive content (non-stopword) words is a "candidate phrase".
     This step is still needed even for single-word output, because it
     is what guarantees a stopword can never end up in the result: a
     word only ever enters a candidate phrase if it is NOT in the
     combined English + Hindi + Bengali stopword set.
  3. Score each unique word by degree(word) / frequency(word), where
     degree counts how often a word co-occurs with other words inside
     candidate phrases (a proxy for how "central"/important it is,
     rather than plain frequency).
  4. Rank individual words by that score and return the top N - never
     multi-word phrases.

The multilingual part is in step 2: because the stopword set is the
*union* of English, Hindi and Bengali stopwords, a single pass finds
content words correctly regardless of which script(s) a sentence
mixes - no language identification of the whole sentence is needed up
front, only per-word script tagging (used afterwards, purely for the
EN/HI/BN/Mixed label shown in the UI).
"""

import re
from collections import defaultdict

from .stopwords import ALL_STOPWORDS
from .language_utils import detect_word_lang

# Sentence/phrase-breaking punctuation, including the Devanagari/Bengali
# "purna virama" danda (।) and double danda (॥) used as full stops.
_SENTENCE_DELIMS = re.compile(
    r"[.!?,;:\n\r\t।॥\-\u2013\u2014\"'()\[\]{}<>/\\|~`^*_=+@#$%&]+"
)

# Unicode-aware "word" = a run of alphabetic characters drawn from
# Latin, Devanagari, or Bengali. Note: Python's built-in re module does
# NOT treat combining marks (vowel signs / matras, virama) as "\w", so
# a plain \w-based pattern silently shreds Devanagari/Bengali words into
# their consonant skeletons. We match the full Unicode blocks instead,
# which keeps matras and virama attached to their base consonant.
_WORD_RE = re.compile(
    r"[A-Za-zÀ-ÖØ-öø-ÿ\u0900-\u097F\u0980-\u09FF]+",
    re.UNICODE,
)

_MIN_WORD_LEN = 1
_MAX_PHRASE_WORDS = 5  # guard against pathological one-giant-phrase input


def _split_into_candidate_phrases(text: str):
    """Return a list of phrases, each a list of original-case word strings."""
    phrases = []
    for sentence in _SENTENCE_DELIMS.split(text):
        words = _WORD_RE.findall(sentence)
        current = []
        for w in words:
            if len(w) < _MIN_WORD_LEN:
                continue
            if w.lower() in ALL_STOPWORDS:
                if current:
                    phrases.append(current)
                    current = []
            else:
                current.append(w)
                if len(current) >= _MAX_PHRASE_WORDS:
                    phrases.append(current)
                    current = []
        if current:
            phrases.append(current)
    return phrases


def extract_keywords(text: str, top_n: int = 15):
    text = (text or "").strip()
    if not text:
        return []

    # Candidate phrases are built the same way as before - this is what
    # keeps stopwords out entirely, and lets word importance be scored
    # by co-occurrence rather than plain frequency. Only the OUTPUT is
    # different: single words instead of the phrases themselves.
    phrases = _split_into_candidate_phrases(text)
    if not phrases:
        return []

    freq = defaultdict(int)
    degree = defaultdict(int)
    surface_form = {}  # lowercase word -> first-seen original casing
    for phrase in phrases:
        length = len(phrase)
        for w in phrase:
            wl = w.lower()
            freq[wl] += 1
            degree[wl] += length  # co-occurrence with every word in the phrase, incl. itself
            surface_form.setdefault(wl, w)

    word_score = {w: degree[w] / freq[w] for w in freq}

    results = []
    for wl, score in word_score.items():
        surface = surface_form[wl]
        results.append({
            "word": surface,
            "score": score,
            "language": detect_word_lang(surface),
        })

    # Rank by score, breaking ties by raw frequency (more mentions wins).
    ranked = sorted(results, key=lambda r: (r["score"], freq[r["word"].lower()]), reverse=True)
    top = ranked[:top_n]

    max_score = top[0]["score"] if top else 1.0
    for r in top:
        r["score"] = round(r["score"], 2)
        r["relative_score"] = round(100 * r["score"] / max_score, 1) if max_score else 0.0

    return top
