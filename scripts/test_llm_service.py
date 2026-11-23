from app.database.connection import SessionLocal
from app.repositories.movie_repository import get_movies
from app.services.llm_service import generate_movie_response


def main():
    db = SessionLocal()

    try:
        # Retrieve actual action movies from SQLite
        movies = get_movies(
            db=db,
            genre="Action",
            limit=3
        )

        question = "Recommend three action movies."

        print("Movies retrieved from database:\n")

        for movie in movies:
            print(f"- {movie.title} ({movie.year})")

        print("\nSending database results to Ollama...\n")

        response = generate_movie_response(question, movies)

        print("LLM Response:\n")
        print(response)

    finally:
        db.close()


if __name__ == "__main__":
    main()


# Previous standalone LLM test (kept for reference):
# from app.services.llm_service import generate_response
#
# def main():
#     prompt = """
#     Recommend three science fiction movies.
#     Give one short reason for each recommendation.
#     """
#     print("Sending prompt to Ollama...\n")
#     response = generate_response(prompt)
#     print("LLM Response:")
#     print(response)