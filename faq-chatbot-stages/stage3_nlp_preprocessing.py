"""
Stage 3 — Introduce NLP
=======================
Stage 2's chatbot matched a keyword only if it appeared as an exact
substring in what the user typed. That breaks the moment someone rephrases
a question:

    "library"                    in "where can i find the library?"   -> matches
    "library timings" (2 words)  in "when does the library open?"     -> does NOT match

This stage fixes that by teaching the bot to understand a sentence as a
*set of meaningful words* instead of raw text: it tokenizes the sentence,
lowercases it, drops punctuation, and removes common "stopwords" (the,
is, are, what, does, ...) that carry no topic information. Two sentences
that share the same meaningful words will now match, even if worded
differently.

Run:
    pip install nltk
    python stage3_nlp_preprocessing.py
"""
import string
import nltk

# Download the two small data packages nltk needs, once.
# (If you're on a machine with no internet access, download these once
#  on a machine that does, then copy the ~/nltk_data folder over.)
for pkg, path in [("punkt_tab", "tokenizers/punkt_tab"), ("stopwords", "corpora/stopwords")]:
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(pkg, quiet=True)

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))


def preprocess(text: str) -> list[str]:
    """Lowercase -> tokenize -> keep only alphanumeric, non-stopword tokens."""
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t.isalnum() and t not in STOP_WORDS]
    return tokens


# ---------------------------------------------------------------------------
# Quick demo of just the preprocessing step (this is what your teacher wants
# to see first: prove the function works before wiring it into the chatbot).
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    demo_sentences = [
        "What are the library timings?",
        "Where can I find the library?",
        "When does the library open?",
    ]
    print("Preprocessing demo")
    print("-" * 40)
    for s in demo_sentences:
        print(f"{s!r:40} -> {preprocess(s)}")

    # ------------------------------------------------------------------
    # A small upgrade over Stage 2: instead of "is this keyword a
    # substring of the question", we now compare the SET of preprocessed
    # words in the question against the set of preprocessed words in
    # each FAQ entry, and answer with whichever FAQ shares the most words.
    # This is still not TF-IDF (that's Stage 4) but it already survives
    # basic rephrasing, which plain substring matching could not.
    # ------------------------------------------------------------------
    faq = {
        "hello": "Hello! How can I help you?",
        "hod": "The Head of the Department is available in the department office.",
        "library": "The library is open from 9 AM to 5 PM.",
        "department": "The Information Technology Department is in the main academic building.",
        "admission": "Admission information is available from the college admission office.",
        "exam": "Examination information is published by the examination section.",
        "courses": "The department offers courses in Information Technology.",
        "bye": "Thank you! Goodbye!",
    }
    # Pre-tokenize the FAQ keys once, so we don't redo it on every question.
    faq_tokens = {key: preprocess(key) for key in faq}

    def best_match(question: str):
        q_tokens = set(preprocess(question))
        if not q_tokens:
            return None, 0
        best_key, best_overlap = None, 0
        for key, tokens in faq_tokens.items():
            overlap = len(q_tokens & set(tokens))
            if overlap > best_overlap:
                best_key, best_overlap = key, overlap
        return best_key, best_overlap

    print("\nCollege FAQ Chatbot (Stage 3 — NLP preprocessing)")
    print("Type 'bye' to exit.")
    while True:
        question = input("You: ")
        if question.lower().strip() == "bye":
            print("Bot:", faq["bye"])
            break
        key, overlap = best_match(question)
        if key and overlap > 0:
            print("Bot:", faq[key])
        else:
            print("Bot: Sorry, I don't understand your question.")
