from sqlalchemy.orm import Session

from app.services.query_parser import parse_query
from app.repositories.movie_repository import get_movies
from app.services.llm_service import generate_movie_response


def search_movies(question: str, db: Session):

    # Step 1: Understand the user's question
    parsed_query = parse_query(question, db)

    # Step 2: Extract all matching movie titles
    titles = parsed_query["titles"]

    # Step 3: Retrieve matching movies from the database
    if parsed_query["intent"] == "movie_details" and not titles:

        # A specific movie was requested, but no title was identified
        movies = []

    else:
        movies = get_movies(
            db=db,
            titles=titles if titles else None,
            year=parsed_query["year"],
            genre=parsed_query["genre"]
        )

    # Step 4: Generate a response
    if not movies:
        response = "Sorry, no matching movies were found in the database."
    else:
        response = generate_movie_response(question, movies)

    # Step 5: Return parsed query, database results and LLM response
    return {
        "parsed_query": parsed_query,
        "movies": movies,
        "response": response
    }
