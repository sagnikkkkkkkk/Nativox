"""
Précis Compression Engine: Compresses a spoken transcript paragraph
into a budgeted summary while preserving core meaning, complete sentence grammar, and translating to Hindi.
"""
import math
import re
from .translator import translate_to_hindi

# Conversational meta-phrases commonly occurring in video/podcast transcripts to trim cleanly
META_DISCOURSE_PATTERNS = [
    r"^welcome\s+(?:back\s+)?(?:guys|everyone|folks|viewers)[,!.\s]+",
    r"^in this (?:particular\s+)?(?:video|tutorial|session|lecture|guide|walkthrough)[,:\s]+",
    r"what we are (?:basically\s+)?going to (?:do|talk about|discuss|cover) is\s*",
    r"as (?:you|we) (?:all\s+)?know[,:\s]+",
    r"don't forget to like and subscribe[,!.\s]*",
    r"without further ado[,:\s]+",
]


def split_sentences(text: str) -> list[str]:
    """Split text into sentences cleanly."""
    sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [s.strip() for s in sentences if s.strip()]


def clean_meta_discourse(sentence: str) -> str:
    """Removes video preamble and conversational clutter from a sentence."""
    cleaned = sentence
    for pat in META_DISCOURSE_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def extract_core_keywords(text: str) -> list[str]:
    """Extracts prominent nouns and technical terms to ensure retention in précis."""
    words = re.findall(r"[A-Za-z0-9\-_]{3,}", text.lower())
    stopwords = {
        "the", "and", "this", "that", "with", "from", "for", "are", "was", "were",
        "will", "have", "been", "they", "what", "when", "where", "which", "into",
        "about", "more", "some", "very", "just", "also", "your", "them", "then",
    }
    content_words = [w for w in words if w not in stopwords]
    counts = {}
    for w in content_words:
        counts[w] = counts.get(w, 0) + 1
    sorted_words = sorted(counts.keys(), key=lambda w: counts[w], reverse=True)
    return sorted_words[:5]


def score_sentences(sentences: list[str]) -> list[tuple[int, str, float]]:
    """
    Ranks complete sentences based on informational salience, keyword density, and structural position.
    Returns list of (original_index, cleaned_sentence, score).
    """
    scored = []
    total = len(sentences)
    if total == 0:
        return []

    full_text = " ".join(sentences)
    top_keywords = set(extract_core_keywords(full_text))

    for idx, raw_s in enumerate(sentences):
        cleaned = clean_meta_discourse(raw_s)
        if not cleaned:
            continue

        words = re.findall(r"\w+", cleaned.lower())
        word_count = len(words)
        if word_count < 3:
            continue

        # Position score (introductory thesis and conclusion carry higher weight)
        pos_score = 1.3 if (idx == 0 or idx == total - 1) else 1.0

        # Keyword density score
        kw_matches = sum(1 for w in words if w in top_keywords)
        density_score = (kw_matches / word_count) if word_count else 0

        # Length penalty: avoid single giant run-on sentences dominating
        length_factor = 1.0 if 8 <= word_count <= 28 else 0.85

        final_score = (density_score * 2.0 + pos_score) * length_factor
        scored.append((idx, cleaned, final_score))

    # Sort descending by score
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored


def compress_paragraph_to_budget(
    paragraph: str,
    min_ratio: float = 0.35,
    max_ratio: float = 0.40,
) -> tuple[str, list[str]]:
    """
    Condenses the English paragraph into a grammatically coherent précis.
    Preserves complete sentence structures so meaning is never destroyed.
    """
    raw_words = re.findall(r"\w+", paragraph)
    orig_words = len(raw_words)
    if orig_words == 0:
        return "", []

    key_points = extract_core_keywords(paragraph)
    raw_sentences = split_sentences(paragraph)

    # For short inputs (<= 25 words or single sentence), preserve full sentence
    if orig_words <= 25 or len(raw_sentences) <= 1:
        clean_s = clean_meta_discourse(paragraph)
        if not clean_s.endswith((".", "!", "?")):
            clean_s += "."
        return clean_s, key_points

    target_min = max(6, math.floor(orig_words * min_ratio))
    target_max = max(target_min, math.ceil(orig_words * max_ratio))

    scored = score_sentences(raw_sentences)
    if not scored:
        return paragraph, key_points

    # Pick complete sentences up to target_max
    chosen_sentences = []
    current_words = 0
    upper_limit = target_max + max(3, int(orig_words * 0.04))

    for orig_idx, s, score in scored:
        w_count = len(re.findall(r"\w+", s))
        if current_words + w_count <= upper_limit:
            chosen_sentences.append((orig_idx, s, w_count))
            current_words += w_count
            if current_words >= target_min:
                break

    # If nothing fit under upper limit, take top scoring sentence
    if not chosen_sentences and scored:
        top_idx, top_s, _ = scored[0]
        chosen_sentences.append((top_idx, top_s, len(re.findall(r"\w+", top_s))))

    # Sort chosen sentences back into chronological order
    chosen_sentences.sort(key=lambda x: x[0])

    result_text = " ".join([x[1] for x in chosen_sentences]).strip()
    if not result_text.endswith((".", "!", "?")):
        result_text += "."

    return result_text, key_points


def generate_precis(
    raw_paragraph: str,
    min_ratio: float = 0.35,
    max_ratio: float = 0.40,
    target_lang: str = "hindi",
) -> dict:
    """
    Précis summary generator:
    Compresses long paragraph transcripts into a coherent précis while preserving complete sentences,
    and produces both refined English and meaningful Hindi translations.
    """
    raw_paragraph = (raw_paragraph or "").strip()
    if not raw_paragraph:
        return {
            "original_text": "",
            "original_word_count": 0,
            "precis_english": "",
            "precis_hindi": "",
            "precis_word_count": 0,
            "retention_ratio_pct": 0.0,
            "target_ratio_range": f"{int(min_ratio*100)}% - {int(max_ratio*100)}%",
            "is_within_budget": False,
            "key_points_retained": [],
        }

    orig_word_count = len(re.findall(r"\w+", raw_paragraph))

    # Step 1: Compute coherent English précis
    english_precis, key_points = compress_paragraph_to_budget(
        raw_paragraph, min_ratio=min_ratio, max_ratio=max_ratio
    )

    # Step 2: Translate into natural, fluent Hindi
    hindi_precis = translate_to_hindi(english_precis)

    precis_word_count = len(re.findall(r"\w+", english_precis))
    ratio_pct = round((precis_word_count / orig_word_count) * 100, 1) if orig_word_count else 0.0
    is_within_budget = (min_ratio * 100 - 5.0) <= ratio_pct <= (max_ratio * 100 + 5.0) or orig_word_count <= 25

    return {
        "original_text": raw_paragraph,
        "original_word_count": orig_word_count,
        "precis_english": english_precis,
        "precis_hindi": hindi_precis,
        "precis_word_count": precis_word_count,
        "retention_ratio_pct": ratio_pct,
        "target_ratio_range": f"{int(min_ratio*100)}% - {int(max_ratio*100)}%",
        "is_within_budget": is_within_budget,
        "key_points_retained": key_points,
    }
