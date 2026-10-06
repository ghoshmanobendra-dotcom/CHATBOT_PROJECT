"""
Stage 4 — TF-IDF Based Chatbot
===============================
Stage 3's word-overlap trick is still fragile: "when is the examination"
and "when are the examinations" share zero preprocessed words ("examination"
vs "examinations" are different tokens to a computer, even though they mean
the same thing to us).

TF-IDF fixes the *matching* problem differently: instead of hand-picking one
keyword per topic, we store several REAL example questions per topic. TF-IDF
turns every question (the stored ones, and the user's new one) into a vector
of numbers, weighting words that are distinctive (like "library") higher than
words that appear everywhere (like "the", "is"). We then use cosine
similarity to find which stored question is closest in *meaning-as-vectors*
to what the user typed, and return that question's answer.

    User Question -> Preprocessing -> TF-IDF -> Cosine Similarity
                   -> Find Most Similar Stored Question -> Return its Answer

Run:
    pip install scikit-learn
    python stage4_tfidf_chatbot.py
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Several real phrasings per topic -> TF-IDF has more to compare against,
# which is exactly what makes it more forgiving than Stage 3's single keyword.
questions = [
    "What are the library timings?",
    "When does the library open?",
    "When does the library close?",
    "Where can I find the library?",
    "Who is the HOD?",
    "Who is the head of the department?",
    "Where is the IT department?",
    "Which building is the IT department in?",
    "What courses are offered?",
    "What subjects are taught in the department?",
    "How can I get admission?",
    "What is the admission procedure?",
    "What documents are required for admission?",
    "When are the examinations?",
    "When is the examination?",
    "What is the exam schedule?",
    "What are the department timings?",
    "When does the college open?",
]

answers = [
    "The library is open from 9 AM to 5 PM.",
    "The library is open from 9 AM to 5 PM.",
    "The library is open from 9 AM to 5 PM.",
    "The library is open from 9 AM to 5 PM.",
    "The Head of the Department is available in the department office.",
    "The Head of the Department is available in the department office.",
    "The IT department is located in the main academic building.",
    "The IT department is located in the main academic building.",
    "The department offers undergraduate and postgraduate IT courses.",
    "The department offers undergraduate and postgraduate IT courses.",
    "Please contact the college admission office for admission information.",
    "Please contact the college admission office for admission information.",
    "Please contact the college admission office for admission information.",
    "Please check the examination section for the latest examination schedule.",
    "Please check the examination section for the latest examination schedule.",
    "Please check the examination section for the latest examination schedule.",
    "The department is open from 9 AM to 5 PM on working days.",
    "The department is open from 9 AM to 5 PM on working days.",
]

vectorizer = TfidfVectorizer(stop_words="english")
question_vectors = vectorizer.fit_transform(questions)

SIMILARITY_THRESHOLD = 0.25


def get_answer(user_question: str):
    user_vector = vectorizer.transform([user_question])
    similarity = cosine_similarity(user_vector, question_vectors)
    best_match = similarity.argmax()
    score = similarity[0][best_match]
    if score > SIMILARITY_THRESHOLD:
        return answers[best_match], questions[best_match], score
    return None, None, score


if __name__ == "__main__":
    # A couple of automatic sanity checks before the interactive loop,
    # including the exact phrasing that tripped up Stage 3.
    print("Sanity checks")
    print("-" * 40)
    for test_q in ["when are the examinations", "where can i find the library"]:
        ans, matched, score = get_answer(test_q)
        print(f"{test_q!r:35} -> matched {matched!r} (score {score:.2f})")
    print()

    print("College FAQ Chatbot (Stage 4 — TF-IDF)")
    print("Type 'bye' to exit.")
    while True:
        user_question = input("\nYou: ")
        if user_question.lower() == "bye":
            print("Bot: Goodbye!")
            break
        answer, matched_question, score = get_answer(user_question)
        if answer:
            print("Bot:", answer)
        else:
            print("Bot: Sorry, I could not understand your question.")
