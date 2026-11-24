
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload, joinedload

from app.database.models import (
    Movie,
    Genre,
    MovieGenre,
    MovieCast,
    MovieDirector
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
    limit: int = 10
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

    # Sort by popularity (highest first)
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
