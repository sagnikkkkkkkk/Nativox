"""
Configuration and constants for Stage 5: Sentence Reformation & Précis Compression.
"""
from pathlib import Path

# Server settings
DEFAULT_PORT = 8012

# Compression Targets (Sir's directive: 35% - 40% for paragraph summarization)
DEFAULT_MIN_COMPRESSION = 0.35
DEFAULT_MAX_COMPRESSION = 0.40

# Spoken English fillers & vocal disfluencies to eliminate safely.
# NOTE: Never include valid lexical verbs, adverbs, or nouns like 'like', 'right now', 'video' here.
ENGLISH_DISFLUENCIES = [
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\bah+\b",
    r"\bhm+\b",
    r"\buhm+\b",
    r"\buh-huh\b",
    r"\bbasically\b",
    r"\bi\s+mean\b",
    r"\bkind\s+of\b",
    r"\bsort\s+of\b",
    r"\bso\s+yeah\b",
    r",\s*like\s*,",
    r"^like,\s*",
    r"(?:,\s*)?\byou\s+know\b[.?!\s]*$",
    r"^(?:you\s+know)[,\s]+",
    r",\s*you\s+know\s*,",
]

# Spoken Hindi fillers if any code-mixed speech arrives
HINDI_DISFLUENCIES = [
    r"\bमतलब\b",
    r"\bयानी\b",
    r"\bजैसे कि\b",
    r"\bअरे\b",
    r"\bतो बेसिकली\b",
]

# Standard technical terminology glossary for audio/video dubbing into Hindi.
# Ensures precise, natural technical terminology used by professional translators.
TECHNICAL_GLOSSARY = {
    "machine learning": "मशीन लर्निंग",
    "deep learning": "डीप लर्निंग",
    "neural network": "न्यूरल नेटवर्क",
    "neural networks": "न्यूरल नेटवर्क",
    "artificial neural network": "आर्टिफिशियल न्यूरल नेटवर्क",
    "artificial neural networks": "आर्टिफिशियल न्यूरल नेटवर्क",
    "artificial intelligence": "आर्टिफिशियल इंटेलिजेंस",
    "computer vision": "कंप्यूटर विज़न",
    "natural language processing": "नेचुरल लैंग्वेज प्रोसेसिंग",
    "speech recognition": "स्पीच रिकग्निशन",
    "machine translation": "मशीन ट्रांसलेशन",
    "data science": "डेटा साइंस",
    "dataset": "डेटासेट",
    "data set": "डेटासेट",
    "loss function": "लॉस फ़ंक्शन",
    "gradient descent": "ग्रेडिएंट डिसेंट",
    "backpropagation": "बैकप्रॉपैगैशन",
    "weights and biases": "वेट्स और बायस",
    "hyperparameter": "हाइपरपैरामीटर",
    "hyperparameters": "हाइपरपैरामीटर",
    "learning rate": "लर्निंग रेट",
    "overfitting": "ओवरफ़िटिंग",
    "underfitting": "अंडरफ़िटिंग",
    "linear algebra": "रैखिक बीजगणित",
    "matrix multiplication": "मैट्रिक्स गुणा",
    "calculus": "कैलकुलस",
    "microservices": "माइक्रोसर्विसिस",
    "microservice": "माइक्रोसर्विस",
    "architecture": "आर्किटेक्चर",
    "monolithic": "मोनोलिथिक",
    "backend": "बैकएंड",
    "frontend": "फ़्रंटएंड",
    "database": "डेटाबेस",
    "framework": "फ़्रेमवर्क",
    "open source": "ओपन सोर्स",
    "python": "पायथन",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "api": "API",
}

# Heuristic refinement rules to fix awkward literal machine translations in Hindi
HINDI_REFINEMENT_RULES = [
    (r"हुड के नीचे|हुड के तहत", "पर्दे के पीछे"),
    (r"कला की स्थिति", "अत्याधुनिक"),
    (r"गौर करते हैं", "समझेंगे"),
    (r"सीखना नहीं सीख लेता", "सीख नहीं लेता"),
    (r"\bकलन\b", "कैलकुलस"),
    (r"गहरे तंत्रिका नेटवर्क|गहरा तंत्रिका नेटवर्क", "डीप न्यूरल नेटवर्क"),
    (r"तंत्रिका नेटवर्क", "न्यूरल नेटवर्क"),
    (r"वाक् पहचान", "स्पीच रिकग्निशन"),
    (r"मशीनी अनुवाद", "मशीन ट्रांसलेशन"),
    (r"प्राकृतिक भाषा प्रसंस्करण", "नेचुरल लैंग्वेज प्रोसेसिंग"),
    (r"खोज करता है कि", "बताता है कि"),
    (r"की खोज करता है", "को समझाता है"),
    (r"दिन के अंत में", "आखिरकार"),
    (r"का आंकड़ा लगाना", "का हल निकालना"),
    (r"\bके के\b", "के"),
    (r"\bमें में\b", "में"),
    (r"\bको को\b", "को"),
    (r"\bका का\b", "का"),
    (r"\bकी की\b", "की"),
    (r"\bसे से\b", "से"),
]
