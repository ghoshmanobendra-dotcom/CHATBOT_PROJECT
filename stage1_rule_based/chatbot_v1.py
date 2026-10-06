import re

EXIT_WORDS = {"bye", "exit", "quit"}


def get_words(text):
    """Lowercase the text and split it into words, ignoring punctuation."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def get_response(words):
    """Return a reply for the given set of words, or None if nothing matches."""
    # Specific rules first, general rules later
    if words & {"hello", "hi", "hey"}:
        return "Hello! How can I help you?"

    if "hod" in words or ("head" in words and "department" in words):
        return "The HOD is available in the department office."

    if "library" in words:
        return "The library is open from 9 AM to 5 PM."

    if "department" in words:
        return "Welcome to the Information Technology Department."

    return None


def main():
    print("College Chatbot")
    print("Type 'bye' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye!")
            break

        if not user_input:
            print("Bot: Please type a question.")
            continue

        words = get_words(user_input)

        if words & EXIT_WORDS:
            print("Bot: Goodbye!")
            break

        reply = get_response(words)
        print("Bot:", reply or "Sorry, I don't understand your question.")


if __name__ == "__main__":
    main()
