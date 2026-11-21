"""
Unit tests for Stage 5(b): Sentence Reformation & Meaningful Precise Hindi Synthesis.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.precis import compress_paragraph_to_budget, generate_precis
from app.reformer import clean_disfluencies, reconstruct_english_syntax, reconstruct_sentence
from app.translator import translate_to_hindi


class TestSentenceReformation(unittest.TestCase):
    def test_clean_disfluencies_removes_fillers_and_stutters_safely(self):
        raw = "uh basically we we need to understand neural networks you know"
        cleaned, removed = clean_disfluencies(raw)

        self.assertNotIn("uh", cleaned.lower().split())
        self.assertNotIn("we we", cleaned.lower())
        self.assertIn("we need to understand neural networks", cleaned)
        self.assertTrue(len(removed) > 0)

    def test_clean_disfluencies_preserves_valid_words_like_and_right_now(self):
        raw = "I like this video and right now we are learning deep learning."
        cleaned, removed = clean_disfluencies(raw)

        # 'like' as a verb and 'right now' as a time phrase must NEVER be removed
        self.assertIn("like", cleaned)
        self.assertIn("right now", cleaned)
        self.assertIn("deep learning", cleaned)
        self.assertEqual(len(removed), 0)

    def test_reconstruct_english_syntax_preserves_already_complete_sentences(self):
        raw = "In this video we are training a computer vision model."
        reconstructed = reconstruct_english_syntax(raw)

        self.assertTrue(reconstructed.endswith("."))
        self.assertTrue(reconstructed[0].isupper())
        # Must not insert extra spurious words like duplicate 'in this video'
        self.assertEqual(reconstructed.lower().count("in this video"), 1)

    def test_reconstruct_english_syntax_keyword_sequence(self):
        keywords = "speech recognition machine translation natural language processing"
        reconstructed = reconstruct_english_syntax(keywords)

        self.assertTrue(reconstructed.endswith("."))
        self.assertTrue(reconstructed[0].isupper())
        self.assertIn("speech recognition", reconstructed.lower())

    def test_reconstruct_sentence_end_to_end(self):
        raw = "uh in this video we train deep neural network computer vision"
        res = reconstruct_sentence(raw, target_lang="hindi")

        self.assertIn("meaningful_hindi", res)
        self.assertTrue(len(res["meaningful_hindi"]) > 0)
        self.assertTrue(res["cleaned_english"][0].isupper())
        self.assertTrue(res["cleaned_english"].endswith("."))
        # Verify Hindi has Devanagari script
        self.assertTrue(any("\u0900" <= c <= "\u097f" for c in res["meaningful_hindi"]))

    def test_reconstruct_from_comma_separated_keywords(self):
        keywords = "machine learning, neural networks, speech recognition"
        res = reconstruct_sentence(keywords, target_lang="hindi")

        self.assertIn("This explores", res["cleaned_english"])
        self.assertTrue(len(res["meaningful_hindi"]) > 0)
        # Verify Devanagari script is present
        self.assertTrue(any("\u0900" <= c <= "\u097f" for c in res["meaningful_hindi"]))

    def test_translate_to_hindi_meaningful_and_precise(self):
        eng = "We train computer vision models to classify images accurately."
        hi = translate_to_hindi(eng)
        self.assertTrue(len(hi) > 0)
        self.assertTrue(hi.endswith("।") or hi.endswith("."))

    def test_dramatic_dialogue_reformation(self):
        raw = "I will look for you, I will find you, and I will kill you"
        res = reconstruct_sentence(raw)
        hi = res["meaningful_hindi"]
        # Must produce valid Hindi output
        self.assertTrue(len(hi) > 0)
        self.assertTrue(hi.endswith("।") or hi.endswith("!"))
        # Must contain Devanagari characters
        import re
        self.assertTrue(re.search(r"[\u0900-\u097F]", hi), "Output must be in Hindi")
        # 'look for', 'find', 'kill' must map to 3 semantically distinct Hindi verbs
        # MyMemoryTranslator naturally produces: तलाश/खोज (search) + ढूँढ (find) + मार (kill)
        # We check that at least 2 of the 3 search/find/kill verb roots appear distinctly
        search_verbs = ["तलाश", "खोज", "ढूँढ", "ढूंढ"]
        kill_verbs = ["मार", "हत्या"]
        has_search = any(v in hi for v in search_verbs)
        has_kill = any(v in hi for v in kill_verbs)
        self.assertTrue(has_search, f"Expected a search/find verb in: {hi}")
        self.assertTrue(has_kill, f"Expected a kill verb in: {hi}")


class TestPrecisCompression(unittest.TestCase):
    def setUp(self):
        self.sample_paragraph = (
            "Welcome back guys, in this particular tutorial today, what we are basically going to do is explore "
            "how deep learning and artificial neural networks actually work under the hood. You know, many people think "
            "that neural networks are like a magic black box, but actually, it is just basic linear algebra, matrix "
            "multiplication, and calculus with gradient descent. We will take a sample dataset of images, write a Python "
            "script using PyTorch, and see how the loss function decreases step by step until the computer learns to "
            "classify cats and dogs accurately."
        )

    def test_precis_preserves_coherent_sentences(self):
        res = generate_precis(self.sample_paragraph, min_ratio=0.35, max_ratio=0.50, target_lang="hindi")
        self.assertTrue(len(res["precis_english"]) > 0)
        self.assertTrue(len(res["precis_hindi"]) > 0)
        # Sentences must be complete and grammatically punctuated
        self.assertTrue(res["precis_english"].endswith("."))
        self.assertTrue(res["precis_hindi"].endswith("।") or res["precis_hindi"].endswith("."))


if __name__ == "__main__":
    unittest.main()
