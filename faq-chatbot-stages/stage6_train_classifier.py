"""
Stage 6 — Train a Machine Learning Classifier
==============================================
Stage 4's TF-IDF chatbot compared a new question against a fixed list of
stored questions one at a time (nearest-neighbor matching). This stage
takes a different, more standard NLP approach: train an actual ML
*classifier* that learns, from intents.json, which category ("intent")
a sentence belongs to — then it can classify sentences it has never
seen, not just find the closest stored one.

    User question -> NLP (TF-IDF) -> feature extraction -> ML classification -> intent

This stage deliberately stops at PRINTING the detected intent — connecting
that intent to an actual answer is Stage 7 (the natural next step, since
by then you'll have proven the classifier works on its own).

Run:
    pip install scikit-learn
    python stage6_train_classifier.py
"""
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

with open("intents.json", "r", encoding="utf-8") as file:
    data = json.load(file)

sentences = []
labels = []

for intent in data["intents"]:
    for pattern in intent["patterns"]:
        sentences.append(pattern)
        labels.append(intent["tag"])

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(sentences)

model = LogisticRegression(max_iter=1000)
model.fit(X, labels)

print("Chatbot model trained successfully!")
print(f"Learned {len(set(labels))} intents from {len(sentences)} example patterns.\n")

# ---------------------------------------------------------------------------
# A quick check BEFORE the interactive loop: feed it a few questions that are
# NOT word-for-word copies of anything in intents.json, and see if it still
# gets the intent right. This is what makes it a classifier and not just a
# lookup table — Stage 4's TF-IDF matcher could only ever return a stored
# question's answer; this model generalizes to new phrasing.
# ---------------------------------------------------------------------------
sanity_checks = [
    "hey there, how are you",
    "what time does the library shut",
    "who heads this department",
    "how do I apply to join",
]
print("Sanity checks (none of these sentences appear in intents.json):")
for question in sanity_checks:
    X_test = vectorizer.transform([question])
    prediction = model.predict(X_test)[0]
    confidence = model.predict_proba(X_test).max()
    print(f"  {question!r:38} -> {prediction:12} (confidence {confidence:.2f})")

print("\nCollege Chatbot (Stage 6 — ML intent classifier)")
print("Type 'bye' to exit.")
while True:
    question = input("\nYou: ")
    if question.lower() == "bye":
        print("Bot: Goodbye!")
        break

    X_test = vectorizer.transform([question])
    prediction = model.predict(X_test)[0]
    confidence = model.predict_proba(X_test).max()
    print(f"Detected Intent: {prediction}  (confidence {confidence:.2f})")
