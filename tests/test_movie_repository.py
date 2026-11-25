
from typing import cast

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.models import Movie, Genre, MovieGenre, Rating
from app.repositories.movie_repository import get_movies, get_movie_by_id

from unittest.mock import patch

from app.services.movie_service import search_movies


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    movies = [
        Movie(
            id=1,
            title="Inception",
            year=2010,
            popularity=90.0
        ),
        Movie(
            id=2,
            title="The Dark Knight",
            year=2008,
            popularity=95.0
        ),
        Movie(
            id=3,
            title="Interstellar",
            year=2014,
            popularity=85.0
        )
    ]

    action = Genre(id=1, name="Action")
    science_fiction = Genre(id=2, name="Science Fiction")

    session.add_all(movies + [action, science_fiction])
    session.commit()

    session.add_all([
        MovieGenre(movie_id=1, genre_id=1),
        MovieGenre(movie_id=2, genre_id=1),
        MovieGenre(movie_id=1, genre_id=2),
        MovieGenre(movie_id=3, genre_id=2)
    ])

    session.commit()

    # Add ratings for recommendation tests
    session.add_all([
        Rating(
            movie_id=1,
            vote_average=8.1,
            vote_count=13752
        ),
        Rating(
            movie_id=2,
            vote_average=8.2,
            vote_count=12002
        ),
        Rating(
            movie_id=3,
            vote_average=9.0,
            vote_count=50
        )
    ])

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_get_movies_returns_all_movies(db):
    movies = get_movies(db)

    assert len(movies) == 3


def test_get_movies_filters_by_title(db):
    movies = get_movies(db, titles=["Inception"])

    assert len(movies) == 1
    assert cast(str, movies[0].title) == "Inception"


def test_get_movies_filters_by_year(db):
    movies = get_movies(db, year=2010)

    assert len(movies) == 1
    assert cast(str, movies[0].title) == "Inception"


def test_get_movies_filters_by_genre(db):
    movies = get_movies(db, genre="Action")

    titles = [movie.title for movie in movies]

    assert len(movies) == 2
    assert "Inception" in titles
    assert "The Dark Knight" in titles


def test_get_movies_sorts_by_popularity(db):
    movies = get_movies(db)

    assert [movie.title for movie in movies] == [
        "The Dark Knight",
        "Inception",
        "Interstellar"
    ]


def test_get_movies_applies_pagination(db):
    movies = get_movies(db, skip=1, limit=1)

    assert len(movies) == 1
    assert cast(str, movies[0].title) == "Inception"


def test_get_movie_by_id_returns_movie(db):
    movie = get_movie_by_id(db, 1)

    assert movie is not None
    assert cast(str, movie.title) == "Inception"


def test_get_movie_by_id_returns_none_for_missing_movie(db):
    movie = get_movie_by_id(db, 99999)

    assert movie is None


def test_get_movies_sorts_recommendations_by_rating_and_vote_count(db):
    movies = get_movies(db, sort_by_rating=True)

    titles = [movie.title for movie in movies]

    # Movies with fewer than 100 votes should be excluded
    assert "Interstellar" not in titles

    # Remaining movies should be sorted by rating
    assert titles == [
        "The Dark Knight",
        "Inception"
    ]
@patch("app.services.movie_service.generate_movie_response")
def test_search_movies_integration(
    mock_generate_response,
    db,
    monkeypatch
):
    # Reset the movie title cache so titles are loaded from the test database.
    monkeypatch.setattr(
        "app.services.query_parser._MOVIE_TITLES_CACHE",
        None
    )

    # Mock only the external LLM response.
    mock_generate_response.return_value = (
        "Inception is a science fiction film."
    )

    # Execute the real query parser, service and repository.
    result = search_movies(
        "Tell me about Inception",
        db
    )

    # Verify query parsing.
    assert result["parsed_query"]["intent"] == "movie_details"
    assert result["parsed_query"]["titles"] == ["Inception"]

    # Verify actual SQLite retrieval.
    assert len(result["movies"]) == 1
    assert result["movies"][0].title == "Inception"
    assert result["movies"][0].year == 2010

    # Verify the generated response.
    assert result["response"] == (
        "Inception is a science fiction film."
    )

    # Verify the LLM received the actual retrieved movie.
    mock_generate_response.assert_called_once()

    call_kwargs = mock_generate_response.call_args.kwargs

    assert call_kwargs["intent"] == "movie_details"
    assert call_kwargs["movies"][0].title == "Inception"