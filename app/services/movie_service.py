from sqlalchemy.orm import Session

from app.services.query_parser import parse_query
from app.repositories.movie_repository import get_movies




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

    # Step 4: Return both the parsed query and matching movies
    return {
        "parsed_query": parsed_query,
        "movies": movies
    }
