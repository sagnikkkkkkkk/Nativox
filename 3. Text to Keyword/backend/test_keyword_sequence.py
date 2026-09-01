import unittest

from app.keyword_extractor import extract_keywords_in_sequence


class KeywordSequenceTests(unittest.TestCase):
    def test_keeps_content_words_in_original_order_and_preserves_duplicates(self):
        text = "machine learning and machine translation for speech recognition"
        result = extract_keywords_in_sequence(text)

        self.assertEqual(
            result,
            ["machine", "learning", "machine", "translation", "speech", "recognition"],
        )


if __name__ == "__main__":
    unittest.main()
