
from app.database.connection import SessionLocal
from app.services.movie_service import search_movies


db = SessionLocal()

try:
    questions = [
    "Recommend action movies",
    "Tell me about Inception",
    "Show me comedy movies from 2015",
    "Tell me about The Lord of the Rings",
    "Tell me about Interstellar 2"
]

    for question in questions:
        print(f"\nQuestion: {question}")

        result = search_movies(question, db)

        print("Parsed query:", result["parsed_query"])

        print("Matching movies:")
        for movie in result["movies"]:
            print(f"- {movie.title} ({movie.year})")
        print("\nLLM Response:")
        print(result["response"])

finally:
    db.close()
