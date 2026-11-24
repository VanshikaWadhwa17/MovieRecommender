
import re
from sqlalchemy.orm import Session
from app.database.models import Movie

# In-memory cache for movie titles
_MOVIE_TITLES_CACHE = None


def get_movie_titles(db: Session) -> list[str]:
    global _MOVIE_TITLES_CACHE

    # Load titles from the database only the first time
    if _MOVIE_TITLES_CACHE is None:
        movie_titles = db.query(Movie.title).all()
        _MOVIE_TITLES_CACHE = [movie[0] for movie in movie_titles]

    return _MOVIE_TITLES_CACHE

def detect_intent(question: str) -> str:
    question = question.lower()

    recommendation_keywords = [
        "recommend",
        "suggest",
        "recommendation",
        "what should i watch",
        "movies like"
    ]

    details_keywords = [
        "tell me about",
        "details about",
        "information about",
        "who is in",
        "cast of"
    ]

    for keyword in recommendation_keywords:
        if keyword in question:
            return "recommend"

    for keyword in details_keywords:
        if keyword in question:
            return "movie_details"

    return "search"


GENRES = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Music",
    "Mystery",
    "Romance",
    "Science Fiction",
    "TV Movie",
    "Thriller",
    "War",
    "Western",
    "Foreign"
]


def extract_genre(question: str) -> str | None:
    question = question.lower()

    for genre in GENRES:
        if genre.lower() in question:
            return genre

    return None


def extract_year(question: str) -> int | None:
    match = re.search(r"\b(19\d{2}|20\d{2})\b", question)

    if match:
        return int(match.group(1))

    return None



def extract_titles(question: str, db: Session) -> list[str]:
    question_lower = question.lower()

    # Retrieve all movie titles from the database
    # Old approach: fetch all movie titles from the database on every request
    # movie_titles = db.query(Movie.title).all()
    # titles = [movie[0] for movie in movie_titles]

    # New approach: reuse cached movie titles
    titles = get_movie_titles(db)

    matched_titles = []

    # Common instruction phrases that should not be treated as movie titles
    command_prefixes = [
        "show me",
        "find me",
        "recommend",
        "suggest",
        "list",
        "search for"
    ]

    # Tokenise the question and remove punctuation
    words = re.findall(r"\b\w+\b", question_lower)

    # Step 1: Find complete multi-word movie titles
    multi_word_titles = sorted(
        [title for title in titles if len(title.split()) > 1],
        key=len,
        reverse=True
    )

    for title in multi_word_titles:
        title_lower = title.lower()

        pattern = rf"(?<!\w){re.escape(title_lower)}(?!\w)"

        if re.search(pattern, question_lower):
            # Ignore the match if it is immediately followed by a number
            match = re.search(pattern, question_lower)

            if match:
                remaining_text = question_lower[match.end():].lstrip()

                if remaining_text and remaining_text[0].isdigit():
                    continue

            # Ignore command phrases only when they start the question
            if (
                title_lower in command_prefixes
                and question_lower.startswith(title_lower)
            ):
                continue

            matched_titles.append(title)

    # Step 2: Remove shorter titles contained in longer matches
    matched_titles = [
        title for title in matched_titles
        if not any(
            title != other and title.lower() in other.lower()
            for other in matched_titles
        )
    ]

    # Step 3: Find single-word titles using surrounding context
    single_word_titles = [
        title for title in titles if len(title.split()) == 1
    ]

    single_word_context = [
        "about",
        "in",
        "of",
        "watch",
        "film",
        "movie",
        "cast",
        "starring",
        "featuring",
        "directed",
        "director",
        "stars",
        "star",
        "rating",
        "rated",
        "score",
        "ratings",
        "actors",
        "actor"
    ]

    for title in single_word_titles:
        title_lower = title.lower()

        # Find every occurrence of the title in the question
        for title_index, word in enumerate(words):
            if word != title_lower:
                continue

            # Ignore the match if it is immediately followed by a number
            # e.g. "Interstellar 2" should not match "Interstellar"
            if (
                title_index + 1 < len(words)
                and words[title_index + 1].isdigit()
            ):
                continue

            # Inspect up to three words before and after the title
            nearby_words = (
                words[max(0, title_index - 3):title_index]
                + words[title_index + 1:title_index + 4]
            )

            if any(
                context_word in single_word_context
                for context_word in nearby_words
            ):
                matched_titles.append(title)
                break

    # Step 4: Handle the shared partial phrase "The Lord of the Rings"
    if not matched_titles:
        partial_phrases = [
            "the lord of the rings"
        ]

        for phrase in partial_phrases:
            pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"

            if re.search(pattern, question_lower):
                matching_titles = [
                    title for title in titles
                    if phrase in title.lower()
                ]

                matched_titles.extend(matching_titles)

    return matched_titles



def parse_query(question: str, db: Session) -> dict:
    return {
        "intent": detect_intent(question),
        "genre": extract_genre(question),
        "year": extract_year(question),
        "titles": extract_titles(question, db)
    }

