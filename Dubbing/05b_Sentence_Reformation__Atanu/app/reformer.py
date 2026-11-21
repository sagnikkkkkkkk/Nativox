"""
Sentence Reformation Engine: Disfluency cleaner and meaningful sentence reconstructor.
Converts broken, fragmented, or filler-laden sentences into grammatical, natural, and precise Hindi sentences.
"""
import re
from .config import ENGLISH_DISFLUENCIES, HINDI_DISFLUENCIES, TECHNICAL_GLOSSARY
from .translator import clean_hindi_output, translate_to_english, translate_to_hindi

# Comprehensive set of common English finite verbs to recognize predicates reliably
COMMON_FINITE_VERBS = {
    "is", "are", "was", "were", "am", "be", "been",
    "have", "has", "had",
    "do", "does", "did",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "train", "trains", "trained",
    "learn", "learns", "learned",
    "build", "builds", "built",
    "use", "uses", "used",
    "work", "works", "worked",
    "explain", "explains", "explained",
    "explore", "explores", "explored",
    "understand", "understands", "understood",
    "discuss", "discusses", "discussed",
    "see", "sees", "saw", "seen",
    "show", "shows", "showed", "shown",
    "let", "make", "makes", "made",
    "take", "takes", "took", "taken",
    "give", "gives", "gave",
    "create", "creates", "created",
    "find", "finds", "found",
    "help", "helps", "helped",
    "run", "runs", "ran",
    "convert", "converts", "converted",
    "classify", "classifies", "classified",
    "decrease", "decreases", "decreased",
    "increase", "increases", "increased",
    "need", "needs", "needed",
    "want", "wants", "wanted",
    "like", "likes", "liked",
}


def clean_disfluencies(text: str) -> tuple[str, list[str]]:
    """
    Strips spoken disfluencies, verbal pauses, and stutters safely.
    Preserves valid content words (e.g. 'like' as a verb, 'right now' as time phrase).
    Returns the cleaned text along with a list of detected/removed fillers.
    """
    removed: list[str] = []
    cleaned = (text or "").strip()
    if not cleaned:
        return "", []

    # Strip English disfluencies
    for pattern in ENGLISH_DISFLUENCIES:
        matches = re.findall(pattern, cleaned, flags=re.IGNORECASE)
        if matches:
            for m in matches:
                m_str = m.strip(" ,;")
                if m_str:
                    removed.append(m_str)
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Strip Hindi disfluencies if present
    for pattern in HINDI_DISFLUENCIES:
        matches = re.findall(pattern, cleaned, flags=re.IGNORECASE)
        if matches:
            for m in matches:
                m_str = m.strip(" ,;")
                if m_str:
                    removed.append(m_str)
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Remove repeated consecutive stuttered words (e.g. "we we" -> "we", "the the" -> "the")
    cleaned = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", cleaned, flags=re.IGNORECASE)

    # Clean double spaces, collapsed commas, and punctuation
    cleaned = re.sub(r"(\s*,\s*)+", ", ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Clean leading/trailing punctuation artifacts
    cleaned = re.sub(r"^[,;.\s]+", "", cleaned)
    cleaned = re.sub(r"[,;]+$", "", cleaned).strip()

    return cleaned, list(dict.fromkeys(removed))


def extract_keyword_tokens(text: str) -> list[str]:
    """
    Extracts keyword tokens respecting commas/newlines or grouping multi-word technical phrases.
    """
    if "," in text or "\n" in text:
        raw_tokens = re.split(r"[\n,]+", text)
        return [t.strip() for t in raw_tokens if t.strip()]

    # If space-separated, group multi-word technical terms first
    phrases = sorted(TECHNICAL_GLOSSARY.keys(), key=len, reverse=True)
    matched_ranges = []
    for p in phrases:
        if " " in p:
            for m in re.finditer(r"\b" + re.escape(p) + r"\b", text, flags=re.IGNORECASE):
                matched_ranges.append((m.start(), m.end(), m.group()))

    if matched_ranges:
        matched_ranges.sort(key=lambda x: x[0])
        non_overlapping = []
        last_end = 0
        for start, end, match in matched_ranges:
            if start >= last_end:
                non_overlapping.append((start, end, match))
                last_end = end

        tokens = []
        last_pos = 0
        for start, end, match in non_overlapping:
            prefix = text[last_pos:start].strip()
            if prefix:
                tokens.extend(prefix.split())
            tokens.append(match.strip())
            last_pos = end
        suffix = text[last_pos:].strip()
        if suffix:
            tokens.extend(suffix.split())
        return [t for t in tokens if t]

    return text.split()


def reconstruct_english_syntax(text: str) -> str:
    """
    Restructures fragmented clauses or keyword sequences into a well-formed sentence
    with appropriate capitalization, punctuation, and predicate flow.
    Preserves already complete sentences without inserting spurious words.
    """
    text = (text or "").strip()
    if not text:
        return ""

    is_hindi = bool(re.search(r"[\u0900-\u097F]", text))
    tokens = extract_keyword_tokens(text)
    words = text.split()
    lower_words = [w.lower().rstrip(",;.!?") for w in words]

    # Check whether the text contains any finite verb / main predicate
    has_finite_verb = any(
        w in COMMON_FINITE_VERBS or (w.endswith("s") and len(w) > 4 and w[:-1] in COMMON_FINITE_VERBS)
        for w in lower_words
    )

    # 1. If input is Hindi keywords without predicate
    if is_hindi and not has_finite_verb and len(tokens) >= 2:
        joined_hi = ", ".join(tokens[:-1]) + " और " + tokens[-1]
        return f"यह {joined_hi} की पड़ताल करता है।"

    # 2. If input is a keyword list with NO verb (e.g. 'machine learning, neural networks')
    if not is_hindi and not has_finite_verb and len(tokens) >= 2:
        if "video" in lower_words:
            content_words = " ".join([t for t in tokens if t.lower() != "video"])
            return f"In this video, we examine {content_words}."
        if len(tokens) == 2:
            return f"This explores {tokens[0]} and {tokens[1]}."
        joined = ", ".join(tokens[:-1])
        return f"This explores {joined}, and {tokens[-1]}."

    # 3. If the text already has clausal structure, keep it intact!
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
    Main entry point for sentence reformation:
    Takes a broken, disfluent, or fragmented input sentence, cleans fillers safely,
    restructures English syntax cleanly, and translates into a natural, meaningful,
    and precise Hindi sentence with proper SOV grammar.
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

    # Step 1: Remove vocal fillers, stutters, and disfluencies
    cleaned, removed_fillers = clean_disfluencies(raw_text)

    is_hindi = bool(re.search(r"[\u0900-\u097F]", cleaned))

    # Step 2: Ensure proper grammatical framing in English
    well_formed = reconstruct_english_syntax(cleaned)

    # Step 3: Produce idiomatic, grammatically sound Hindi sentence
    if is_hindi:
        meaningful_hindi = clean_hindi_output(well_formed)
        cleaned_english = translate_to_english(meaningful_hindi)
    else:
        cleaned_english = well_formed
        meaningful_hindi = translate_to_hindi(cleaned_english)

    input_word_count = len(raw_text.split())
    output_word_count = len(meaningful_hindi.split())

    notes = "Disfluencies filtered and sentence syntax refined with meaningful, precise Hindi SOV structure."
    if removed_fillers:
        notes += f" Filtered verbal fillers: {', '.join(removed_fillers)}."

    return {
        "original_text": raw_text,
        "cleaned_english": cleaned_english,
        "meaningful_hindi": meaningful_hindi,
        "removed_fillers": removed_fillers,
        "input_word_count": input_word_count,
        "output_word_count": output_word_count,
        "notes": notes,
    }


def refine_meaningful_precise(text: str, target_lang: str = "hindi") -> dict:
    """
    Refines input into high-precision, natural meaningful English and Hindi.
    Ensures complete preservation of semantic meaning, proper terminology,
    and accurate grammatical structure without artificial truncation.
    """
    reconstructed = reconstruct_sentence(text, target_lang=target_lang)
    return {
        "meaningful_english": reconstructed["cleaned_english"],
        "meaningful_hindi": reconstructed["meaningful_hindi"],
        "precise_english": reconstructed["cleaned_english"],
        "precise_hindi": reconstructed["meaningful_hindi"],
        "removed_fillers": reconstructed["removed_fillers"],
    }
