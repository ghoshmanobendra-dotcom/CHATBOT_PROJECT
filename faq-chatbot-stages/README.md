# Stages 3 & 4 — NLP Preprocessing and TF-IDF Matching

These follow on from your Stage 1 (rule-based, `if/elif`) and Stage 2
(dictionary knowledge base) chatbots. Each file below is standalone —
run it directly, no other files needed.

## Stage 3 — `stage3_nlp_preprocessing.py`

**Problem it solves:** Stage 2 matched a keyword only if it was an exact
substring of the question. "library" matches "where is the library",
but not if the user says "when does it open" with no "library" word at all
in a follow-up, or phrases things in an unexpected way.

**What it adds:** a `preprocess()` function that lowercases the sentence,
splits it into words (tokenization), and throws away both punctuation and
"stopwords" — common words like *the, is, does, what* that carry no topic
meaning. The chatbot then compares the *set of remaining words* in the
question against the set of remaining words in each FAQ entry, and answers
with whichever entry shares the most words. That's a real improvement:
"where can I find the library" and "what are the library timings" now both
correctly hit the library entry, which plain substring matching in Stage 2
could not guarantee.

**Known limitation** (worth mentioning in your report): it still needs the
*exact same word form*. "exam" and "examination" are two different tokens
to this code, so a question about "examination" won't match a FAQ entry
keyed on "exam". Stage 4 works around this differently.

```bash
pip install nltk
python stage3_nlp_preprocessing.py
```

## Stage 4 — `stage4_tfidf_chatbot.py`

**Problem it solves:** Stage 3's fix still relies on exact word matches.
Real questions get asked in many different ways.

**What it adds:** instead of one keyword per topic, we store several real
example questions per topic (`questions[]` / `answers[]`). **TF-IDF**
converts every question — the stored ones and the user's new one — into a
vector of numbers that weighs distinctive words (like "library") higher
than filler words. **Cosine similarity** then finds which stored question
is numerically closest to what the user typed, and we return that
question's answer.

```
User Question -> Preprocessing -> TF-IDF -> Cosine Similarity
             -> Find Most Similar Stored Question -> Return its Answer
```

```bash
pip install scikit-learn
python stage4_tfidf_chatbot.py
```

Two details worth knowing (and worth mentioning if your evaluator asks
"why not just use TF-IDF for everything?"):

- **`stop_words="english"`** on the vectorizer matters a lot here. Without
  it, common words like "who", "is", "the" get counted too, and a totally
  unrelated question like "what is the capital of India" can accidentally
  score high against an FAQ entry just because they share "is" and "the".
- TF-IDF cosine similarity can still be thrown off by **short questions**:
  a stored question with only one matching word can score *higher* than a
  longer, more relevant one, because cosine similarity normalizes by
  sentence length. This — plus the exact-word-form issue from Stage 3 — is
  exactly why the later stages (intent classification with a real ML
  classifier, which I already built for you as the full FastAPI project)
  are more robust: they learn from many phrasings per topic instead of
  nearest-neighbor matching against single stored sentences.

## Where this fits with what you already have

You already have a full working Stages 5-8 implementation (intent
classification with Logistic Regression, FastAPI backend, web UI, Docker)
in the `college-chatbot` project from earlier. These two files are the
missing middle steps — useful on their own to demonstrate progressive
learning in a report or viva, even though the final deployed chatbot uses
the stronger approach from Stage 5 onward.

## Stage 5 — `intents.json`

**Problem it solves:** Stage 4 stored questions and answers as two parallel
lists (`questions[]` / `answers[]`) — easy to get out of sync, and no
natural place to store more than one response per topic.

**What it adds:** a proper structure used in real conversational systems —
each topic ("intent") has a `tag`, a list of example `patterns` (ways
someone might ask about it), and a list of possible `responses`. This is
just data, not code — but it's the data Stage 6's classifier learns from.

## Stage 6 — `stage6_train_classifier.py`

**Problem it solves:** Stage 4's TF-IDF approach finds the closest *stored*
question — it can't generalize to a phrasing that doesn't resemble anything
in its list. This stage trains an actual **classifier**: TF-IDF features
feed into **Logistic Regression**, which learns a general notion of what
words are associated with each intent, not just a lookup table.

```
User question -> TF-IDF features -> Logistic Regression -> predicted intent
```

```bash
pip install scikit-learn
python stage6_train_classifier.py
```

This stage deliberately stops at **printing the detected intent** — wiring
that intent to an actual answer is Stage 7, the natural next step once
you've shown the classifier works.

**Known limitation, and it's a real one I found while testing:** with only
31 example patterns across 8 intents, the classifier sometimes gets it
wrong on phrasing it hasn't seen — in my test run, "who heads this
department" was misclassified as `greeting` at only 0.18 confidence
(barely above the 1-in-8 random baseline of 0.125). This isn't a bug, it's
what a classifier trained on a handful of examples per class looks like.
The fix is exactly the "training loop" from before: more patterns per
intent. The full FastAPI project I built earlier already applies this fix
(204 patterns, tuned regularization, character n-grams) and gets it right.

## Stage 7 — `stage7_chatbot.py`

**Problem it solves:** Stage 6 could tell you *which* intent a question
belonged to, but that's not an answer a user can actually read.

**What it adds:** the exact same TF-IDF + Logistic Regression model as
Stage 6, but now the predicted intent is used to look up that intent's
`responses` list in `intents.json`, and one is picked at random and
printed. This is the "core" terminal chatbot — everything after this is
about how it's delivered, not how it thinks.

```bash
pip install scikit-learn
python stage7_chatbot.py
```

**Known limitation, confirmed by testing it:** I asked it "what is the
weather today" and it confidently answered with the exam schedule
response anyway. `model.predict()` always returns its single best guess,
however wrong — there's no "I don't know" here. That's intentional for
this stage (it matches what Stage 7 is meant to teach), but it's worth
naming as a gap if you're asked about it, and it's exactly what the fuller
FastAPI project (from earlier) fixes with a confidence threshold.

## Stage 8 — `stage8_app.py` + `templates/index.html` + `static/style.css`

**Problem it solves:** Stage 7 only runs in a terminal — not something you
can demo to someone without them having Python installed.

**What it adds:** the identical chatbot logic from Stage 7, wrapped in a
small **Flask** web app. The browser page posts the user's question to a
`/chat` endpoint as JSON; Flask predicts the intent, picks a response, and
sends it back as JSON; a few lines of JavaScript update the page — no
reload needed.

```
Browser (index.html)
   -> POST /chat  {"message": "..."}
   -> Flask route
   -> TF-IDF + Logistic Regression (same model as Stage 6/7)
   -> JSON response
   -> JavaScript updates the page
```

```bash
pip install flask scikit-learn
python stage8_app.py
```

Then open the address it prints — usually **http://127.0.0.1:5000**.

I ran this one end-to-end (not just read the code): started the server,
sent it real HTTP requests for "when does the library close" and "who is
the HOD", and both came back correctly through `/chat` as JSON, with the
homepage and stylesheet serving correctly too.

This completes the same 8-stage progression as the original project brief
you uploaded, with each stage's real limitations called out rather than
glossed over — and the fuller FastAPI/Docker version from earlier already
shows where you'd take it next (confidence thresholds, a richer dataset,
containerized deployment).
