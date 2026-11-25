
import pytest

from app.services.query_parser import (
    detect_intent,
    extract_genre,
    extract_year,
    extract_titles,
    parse_query
)
from app.services import query_parser
from app.database.connection import SessionLocal


@pytest.mark.parametrize(
    "question, expected",
    [
        ("Recommend action movies", "recommend"),
        ("Suggest some good movies", "recommend"),
        ("What should I watch?", "recommend"),
        ("Tell me about Inception", "movie_details"),
        ("Show me movies from 2015", "search"),
    ]
)
def test_detect_intent(question, expected):
    assert detect_intent(question) == expected


@pytest.mark.parametrize(
    "question, expected",
    [
        ("Recommend action movies", "Action"),
        ("Show me comedy movies", "Comedy"),
        ("Find science fiction movies", "Science Fiction"),
        ("Tell me about Inception", None),
    ]
)
def test_extract_genre(question, expected):
    assert extract_genre(question) == expected


@pytest.mark.parametrize(
    "question, expected",
    [
        ("Recommend action movies from 2020", 2020),
        ("Show comedy movies released in 2015", 2015),
        ("Find movies from 1999", 1999),
        ("Tell me about Inception", None),
        ("Recommend movies from 2024", 2024),
    ]
)
def test_extract_year(question, expected):
    assert extract_year(question) == expected


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.parametrize(
    "question, expected",
    [
        ("Tell me about Inception", ["Inception"]),
        ("Who is in Avatar?", ["Avatar"]),
        ("Show me The Dark Knight Rises", ["The Dark Knight Rises"]),
        (
            "I want to watch The Lord of the Rings",
            [
                "The Lord of the Rings: The Fellowship of the Ring",
                "The Lord of the Rings: The Return of the King",
                "The Lord of the Rings: The Two Towers",
            ]
        ),
        ("Recommend some good movies", []),
    ]
)
def test_extract_titles(question, expected, db):
    assert extract_titles(question, db) == expected


def test_parse_query(db):
    result = parse_query("Recommend action movies from 2020", db)

    assert result == {
        "intent": "recommend",
        "genre": "Action",
        "year": 2020,
        "titles": []
    }


def test_movie_title_cache(db):
    query_parser._MOVIE_TITLES_CACHE = None

    first_call = query_parser.get_movie_titles(db)
    second_call = query_parser.get_movie_titles(db)

    assert len(first_call) > 0
    assert first_call is second_call
