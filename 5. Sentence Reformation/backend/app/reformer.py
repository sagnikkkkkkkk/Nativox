"""
Sentence Reformation Engine: Disfluency cleaner and meaningful sentence reconstructor.
Converts broken, fragmented, or filler-laden sentences into grammatical, natural Hindi sentences.
"""
import re
from .config import ENGLISH_DISFLUENCIES, HINDI_DISFLUENCIES
from .translator import clean_hindi_output, translate_to_english, translate_to_hindi


def clean_disfluencies(text: str) -> tuple[str, list[str]]:
    """
    Strips spoken disfluencies, verbal pauses, and fillers.
    Returns the cleaned text along with a list of detected/removed fillers.
    """
    removed: list[str] = []
    cleaned = text

    # Strip English disfluencies
    for pattern in ENGLISH_DISFLUENCIES:
        matches = re.findall(pattern, cleaned, flags=re.IGNORECASE)
        if matches:
            removed.extend([m.strip() for m in matches])
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Strip Hindi disfluencies
    for pattern in HINDI_DISFLUENCIES:
        matches = re.findall(pattern, cleaned, flags=re.IGNORECASE)
        if matches:
            removed.extend([m.strip() for m in matches])
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Remove repeated consecutive words (e.g. "we we", "to to")
    cleaned = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", cleaned, flags=re.IGNORECASE)

    # Clean double spaces, collapsed commas, and punctuation
    cleaned = re.sub(r"(\s*,\s*)+", ", ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Clean leading/trailing punctuation artifacts
    cleaned = re.sub(r"^[,;.\s]+", "", cleaned)
    cleaned = re.sub(r"[,;]+$", "", cleaned)

    return cleaned, list(set(removed))


def reconstruct_english_syntax(text: str) -> str:
    """
    Restructures fragmented clauses or keyword sequences into a well-formed sentence
    with appropriate capitalization, punctuation, and predicate flow.
    """
    text = text.strip()
    if not text:
        return ""

    is_hindi = bool(re.search(r"[\u0900-\u097F]", text))

    # Check if input is explicitly a comma-separated or newline-separated keyword list
    is_delimited_list = ("," in text or "\n" in text)
    if is_delimited_list:
        raw_tokens = re.split(r"[\n,]+", text)
        tokens = [t.strip() for t in raw_tokens if t.strip()]
    else:
        tokens = text.split()

    words = text.split()
    lower_words = [w.lower().rstrip(",;.") for w in words]

    pronouns = {"we", "i", "you", "they", "he", "she", "it", "this", "that"}
    finite_verbs = {
        "is", "are", "was", "were", "will", "can", "should", "have", "has",
        "do", "does", "did", "trains", "trained", "builds", "built", "uses",
        "used", "works", "explains", "discusses", "creates", "demonstrates"
    }

    has_pronoun = any(w in pronouns for w in lower_words)
    has_finite_verb = any(w in finite_verbs for w in lower_words)

    # 1. If input is Hindi keywords (from Stage 4) where stopwords are already removed
    if is_hindi and (not has_pronoun or not has_finite_verb) and len(tokens) >= 2:
        joined_hi = ", ".join(tokens[:-1]) + " और " + tokens[-1]
        return f"यह {joined_hi} की पड़ताल करता है।"

    # 2. If input is a comma-delimited English keyword list from Stage 3/4
    if not is_hindi and is_delimited_list and (not has_pronoun or not has_finite_verb) and len(tokens) >= 2:
        if "video" in lower_words:
            content_words = " ".join([t for t in tokens if t.lower() != "video"])
            return f"In this video, we examine {content_words}."
        if len(tokens) == 2:
            return f"This explores {tokens[0]} and {tokens[1]}."
        joined = ", ".join(tokens[:-1])
        return f"This explores {joined}, and {tokens[-1]}."

    # 3. If space-separated keywords without pronouns and finite verbs
    verbs = {
        "train", "learn", "build", "use", "create", "make", "explore",
        "show", "see", "work", "find", "explain", "discuss", "is", "are",
        "was", "were", "have", "has", "do", "does", "will", "can", "understand"
    }
    has_any_verb = any(w in verbs or w.endswith(("ing", "ed", "ize", "ise", "ate")) for w in lower_words)

    if len(words) >= 2 and not has_pronoun and not has_any_verb:
        joined = ", ".join(words[:-1])
        return f"This explores {joined} and {words[-1]}."

    # If it has "video" at or near start, restore introductory prepositional phrase
    if lower_words and lower_words[0] == "video":
        text = "In this video, " + " ".join(words[1:])
    elif "video" in lower_words[:3] and not text.lower().startswith("in this"):
        text = re.sub(r"\bvideo\b", "in this video,", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()

    reconstructed = text

    # Clean leading punctuation and ensure capitalization
    reconstructed = re.sub(r"^[,;.\s]+", "", reconstructed).strip()
    if not reconstructed.endswith((".", "!", "?", "।")):
        reconstructed += "।" if is_hindi else "."
    if reconstructed and not is_hindi:
        reconstructed = reconstructed[0].upper() + reconstructed[1:]

    return reconstructed


def reconstruct_sentence(raw_text: str, target_lang: str = "hindi") -> dict:
    """
    Main entry point for Task 1:
    Takes a meaningless or fragmented sentence, cleans it, restructures it into
    grammatically sound syntax, and translates it into a natural, meaningful Hindi sentence.
    """
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return {
            "original_text": "",
            "cleaned_english": "",
            "meaningful_hindi": "",
            "removed_fillers": [],
            "input_word_count": 0,
            "output_word_count": 0,
            "notes": "Empty input provided.",
        }

    # Step 1: Remove speech fillers, stutters, and disfluencies
    cleaned, removed_fillers = clean_disfluencies(raw_text)

    # Step 2: Ensure proper grammatical framing in English
    well_formed_english = reconstruct_english_syntax(cleaned)
    is_hindi = bool(re.search(r"[\u0900-\u097F]", cleaned))
    well_formed = reconstruct_english_syntax(cleaned)

    # Step 3: Produce idiomatic, grammatically sound Hindi sentence
    meaningful_hindi = translate_to_hindi(well_formed_english)
    if is_hindi:
        meaningful_hindi = clean_hindi_output(well_formed)
        cleaned_english = translate_to_english(meaningful_hindi)
    else:
        cleaned_english = well_formed
        meaningful_hindi = translate_to_hindi(cleaned_english)

    input_word_count = len(raw_text.split())
    output_word_count = len(meaningful_hindi.split())

    notes = "Disfluencies removed and sentence syntax restored with proper SOV grammar in Hindi."
    if removed_fillers:
        notes += f" Filtered verbal fillers: {', '.join(removed_fillers)}."

    return {
        "original_text": raw_text,
        "cleaned_english": well_formed_english,
        "cleaned_english": cleaned_english,
        "meaningful_hindi": meaningful_hindi,
        "removed_fillers": removed_fillers,
        "input_word_count": input_word_count,
        "output_word_count": output_word_count,
        "notes": notes,
    }
