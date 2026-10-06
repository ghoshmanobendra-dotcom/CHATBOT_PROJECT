"""
Stage 7 — Connect Intent to Response
=====================================
Stage 6 trained a classifier and proved it could predict an intent — but
it stopped at printing the intent's name, not an actual answer. This
stage closes that loop: once we know the intent, we look up that intent's
`responses` list in intents.json and reply with one (chosen at random, so
the bot doesn't sound robotic if you ask the same thing twice).

    User question -> TF-IDF -> Logistic Regression -> predicted intent
                  -> look up responses[intent] -> reply

This is the same model as Stage 6 — nothing about the ML changes here,
only what we DO with its prediction.

Run:
    pip install scikit-learn
    python stage7_chatbot.py
"""
import json
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

with open("intents.json", "r", encoding="utf-8") as file:
    data = json.load(file)

sentences = []
labels = []
responses = {}

for intent in data["intents"]:
    tag = intent["tag"]
    responses[tag] = intent["responses"]
    for pattern in intent["patterns"]:
        sentences.append(pattern)
        labels.append(tag)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(sentences)

model = LogisticRegression(max_iter=1000)
model.fit(X, labels)

print("=" * 40)
print("      COLLEGE CHATBOT")
print("=" * 40)
print("Type 'bye' to exit.")

while True:
    question = input("\nYou: ")
    if question.lower() == "bye":
        print("Bot: Goodbye!")
        break

    X_test = vectorizer.transform([question])
    intent = model.predict(X_test)[0]
    answer = random.choice(responses[intent])
    print("Bot:", answer)

# ---------------------------------------------------------------------------
# Known limitation, worth stating plainly rather than hiding: this always
# answers with SOME intent's response, even for a totally off-topic question
# like "what's the weather today" — there's no "I don't know" fallback here,
# because model.predict() always returns its single best guess, however
# unconfident. The full FastAPI project (from earlier) adds exactly this:
# it checks model.predict_proba()'s top score against a threshold, and
# only answers if the model is actually confident. That's a reasonable
# thing to add here too once you're comfortable with this version — but
# the plain version above matches what this stage is meant to teach:
# "an intent now produces an answer", full stop.
# ---------------------------------------------------------------------------
