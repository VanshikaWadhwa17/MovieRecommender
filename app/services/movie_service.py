
import logging
import requests

from sqlalchemy.orm import Session

from app.services.query_parser import parse_query
from app.repositories.movie_repository import get_movies
from app.services.llm_service import generate_movie_response


logger = logging.getLogger(__name__)


def search_movies(question: str, db: Session):

    # Step 1: Understand the user's question
    parsed_query = parse_query(question, db)

    # Step 2: Extract all matching movie titles
    titles = parsed_query["titles"]

    # Step 3: Check whether this is a recommendation request
    sort_by_rating = parsed_query["intent"] == "recommend"

    # Step 4: Retrieve matching movies from the database
    if parsed_query["intent"] == "movie_details" and not titles:

        # A specific movie was requested, but no title was identified
        movies = []

    else:
        movies = get_movies(
            db=db,
            titles=titles if titles else None,
            year=parsed_query["year"],
            genre=parsed_query["genre"],
            sort_by_rating=sort_by_rating
        )

    # Step 5: Generate a response
    if not movies:
        response = "Sorry, no matching movies were found in the database."

    else:
        try:
            response = generate_movie_response(question, movies)

        except requests.exceptions.RequestException:
            logger.exception(
                "Failed to generate movie response using Ollama."
            )
            response = (
                "The matching movies were found, but the AI response "
                "could not be generated. Please try again later."
            )

    # Step 6: Return parsed query, database results and response
    return {
        "parsed_query": parsed_query,
        "movies": movies,
        "response": response
    }
