
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.models import Movie, Genre, MovieGenre


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

    # Apply pagination
    query = query.offset(skip).limit(limit)

    return query.all()


def get_movie_by_id(db: Session, movie_id: int):
    return db.query(Movie).filter(Movie.id == movie_id).first()
