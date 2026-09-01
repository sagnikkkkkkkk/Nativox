"""
Curated stopword lists for the three supported languages.

These lists are intentionally hand-curated rather than pulled from a
dependency, so the extractor has zero external data downloads at runtime
and the word lists themselves are auditable for the project report.

English list follows the common "RAKE / SMART" style stopword set.
Hindi and Bengali lists cover pronouns, postpositions, conjunctions,
auxiliary verb forms and question words, which is what matters most for
RAKE-style phrase boundary detection (content words are what should
*remain* after this filtering).
"""

ENGLISH_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "did", "do", "does", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "has",
    "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "itself", "just", "me", "more", "most", "my", "myself", "no", "nor",
    "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "will", "with", "would", "you",
    "your", "yours", "yourself", "yourselves", "also", "get", "got",
    "like", "one", "us", "shall", "let", "may", "might", "must",
}

HINDI_STOPWORDS = {
    "और", "का", "के", "की", "है", "हैं", "था", "थी", "थे", "को", "से",
    "में", "पर", "यह", "वह", "ये", "वो", "कि", "तो", "भी", "ही", "न",
    "नहीं", "क्या", "कौन", "कब", "कहाँ", "क्यों", "कैसे", "इस", "उस",
    "इन", "उन", "एक", "दो", "आदि", "हो", "हुआ", "हुई", "हुए", "रहा",
    "रही", "रहे", "जो", "जिस", "जिन", "अगर", "लेकिन", "परन्तु", "या",
    "एवं", "तथा", "साथ", "लिए", "द्वारा", "बिना", "ऊपर", "नीचे",
    "अंदर", "बाहर", "पहले", "बाद", "आज", "कल", "अभी", "फिर", "यहाँ",
    "वहाँ", "कुछ", "सब", "सभी", "हर", "कोई", "अपना", "अपनी", "अपने",
    "मेरा", "मेरी", "मेरे", "तुम्हारा", "तुम्हारी", "तुम्हारे",
    "उसका", "उसकी", "उसके", "हमारा", "हमारी", "हमारे", "आप", "तुम",
    "हम", "मैं", "वे", "इनका", "इनकी", "इनके", "जाता", "जाती", "जाते",
    "गया", "गई", "गए", "करता", "करती", "करते", "किया", "किए", "किन्तु",
    "तक", "मगर", "क्योंकि", "बल्कि", "इसलिए", "जब", "तब", "जहाँ",
    "वहीं", "ना", "जी", "जैसे", "वैसे", "यानी", "अथवा",
}

BENGALI_STOPWORDS = {
    "এবং", "বা", "কিন্তু", "তবে", "যে", "যা", "যিনি", "যাঁর", "এই",
    "ওই", "সেই", "তার", "তাঁর", "তাদের", "আমার", "আমাদের", "তোমার",
    "তোমাদের", "আপনার", "আছে", "ছিল", "ছিলেন", "হবে", "হয়", "হয়েছে",
    "করে", "করেছে", "করতে", "করার", "না", "নেই", "কি", "কেন",
    "কীভাবে", "কখন", "কোথায়", "কে", "কার", "একটি", "একটা", "দুটি",
    "সব", "সবাই", "কিছু", "অনেক", "খুব", "আরও", "শুধু", "শুধুমাত্র",
    "মধ্যে", "উপরে", "নিচে", "ভিতরে", "বাইরে", "আগে", "পরে", "আজ",
    "কাল", "এখন", "তখন", "এখানে", "সেখানে", "থেকে", "দিয়ে", "জন্য",
    "সাথে", "প্রতি", "মতো", "যদি", "তাহলে", "ইত্যাদি", "আমি", "তুমি",
    "আপনি", "সে", "তিনি", "আমরা", "তোমরা", "আপনারা", "তারা", "এটি",
    "এটা", "ওটা", "যেমন", "হয়ে", "হচ্ছে", "করছে", "করেছিল", "গিয়ে",
    "গেল", "যাবে", "নয়", "ও", "কেউ", "কোনো", "প্রায়",
}

# Combined, lower-cased lookup set used by the extractor. Hindi/Bengali
# have no case distinction, so lower() is a no-op for them.
ALL_STOPWORDS = (
    {w.lower() for w in ENGLISH_STOPWORDS}
    | HINDI_STOPWORDS
    | BENGALI_STOPWORDS
)
