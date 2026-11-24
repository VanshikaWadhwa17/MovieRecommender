
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload, joinedload

from app.database.models import (
    Movie,
    Genre,
    MovieGenre,
    MovieCast,
    MovieDirector,
    Rating
)


def load_movie_relationships(query):
    return query.options(
        selectinload(Movie.rating),
        selectinload(Movie.cast_members).joinedload(MovieCast.person),
        selectinload(Movie.directors).joinedload(MovieDirector.person)
    )


def get_movies(
    db: Session,
    titles: list[str] | None = None,
    year: int | None = None,
    genre: str | None = None,
    skip: int = 0,
    limit: int = 10,
    sort_by_rating: bool = False
):
    # Start with a query for all movies
    query = db.query(Movie)

    # Filter by titles, if provided
    if titles:
        title_conditions = [
            Movie.title.ilike(f"%{title}%")
            for title in titles
        ]

        query = query.filter(or_(*title_conditions))

    # Filter by release year, if provided
    if year:
        query = query.filter(Movie.year == year)

    # Filter by genre, if provided
    if genre:
        query = (
            query
            .join(MovieGenre, Movie.id == MovieGenre.movie_id)
            .join(Genre, Genre.id == MovieGenre.genre_id)
            .filter(Genre.name.ilike(genre))
            .distinct()
        )

    # Sort recommendations by rating, vote count and popularity
    if sort_by_rating:
        query = (
            query
            .join(Rating, Movie.id == Rating.movie_id)
            .filter(Rating.vote_count >= 100)
            .order_by(
                Rating.vote_average.desc(),
                Rating.vote_count.desc(),
                Movie.popularity.desc()
            )
        )

    # Keep popularity sorting for regular searches
    else:
        query = query.order_by(Movie.popularity.desc())

    # Load ratings, cast and directors
    query = load_movie_relationships(query)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    return query.all()


def get_movie_by_id(db: Session, movie_id: int):
    query = db.query(Movie).filter(Movie.id == movie_id)

    # Load ratings, cast and directors
    query = load_movie_relationships(query)

    return query.first()
