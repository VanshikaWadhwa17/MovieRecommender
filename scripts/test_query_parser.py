
from app.database.connection import SessionLocal
from app.services.query_parser import (
    detect_intent,
    extract_genre,
    extract_year,
    extract_titles,
    parse_query
)
from app.services import query_parser

questions = [
    "Recommend action movies from 2020",
    "Suggest some good movies",
    "Tell me about Inception",
    "Show me movies from 2015",
    "Who is in Avatar?"
]

for question in questions:
    intent = detect_intent(question)
    print(f"Question: {question}")
    print(f"Intent: {intent}")
    print()


print("\n--- Testing genre extraction ---")

genre_questions = [
    "Recommend action movies from 2020",
    "Show me comedy movies",
    "Find science fiction movies",
    "I want to watch horror films",
    "Tell me about Inception"
]

for question in genre_questions:
    genre = extract_genre(question)
    print(f"Question: {question}")
    print(f"Genre: {genre}")
    print()



print("\n--- Testing year extraction ---")

year_questions = [
    "Recommend action movies from 2020",
    "Show comedy movies released in 2015",
    "Find movies from 1999",
    "Tell me about Inception",
    "Recommend movies from 2024"
]

for question in year_questions:
    year = extract_year(question)
    print(f"Question: {question}")
    print(f"Year: {year}")
    print()


print("\n--- Testing movie title extraction ---")

db = SessionLocal()

try:
    title_questions = [
        "Tell me about Inception",
        "Who is in Avatar?",
        "Show me The Dark Knight Rises",
        "I want to watch The Lord of the Rings",
        "Recommend some good movies"
    ]

    for question in title_questions:
        titles = extract_titles(question, db)
        print(f"Question: {question}")
        print(f"Titles: {titles}")
        print()
        

finally:
    db.close()


# Test combined query parsing
print("\n--- Testing combined query parsing ---")

questions = [
    "Tell me about Inception",
    "Who is in Avatar?",
    "Show me The Dark Knight Rises",
    "I want to watch The Lord of the Rings",
    "Recommend some good movies",
    "Show me action movies",
    "Recommend something good"
]

for question in questions:
    result = parse_query(question, db)

    print(f"\nQuestion: {question}")
    print(f"Parsed result: {result}")


# --- Testing movie title cache ---

print("\n--- Testing movie title cache ---")

query_parser._MOVIE_TITLES_CACHE = None

first_call = query_parser.get_movie_titles(db)
second_call = query_parser.get_movie_titles(db)

print("First call title count:", len(first_call))
print("Second call title count:", len(second_call))
print("Same cached object:", first_call is second_call)
