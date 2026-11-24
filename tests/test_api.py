
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Movie Recommendation API is running"
    }


@patch("app.main.get_movies")
def test_search_movies_endpoint(mock_get_movies):
    mock_movie = MagicMock()
    mock_movie.id = 1
    mock_movie.title = "Inception"
    mock_movie.year = 2010
    mock_movie.overview = "A thief enters people's dreams."

    mock_get_movies.return_value = [mock_movie]

    response = client.get("/movies?title=Inception")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Inception"

    mock_get_movies.assert_called_once()


@patch("app.main.get_movie_by_id")
def test_get_movie_details_endpoint(mock_get_movie):
    mock_movie = MagicMock()
    mock_movie.id = 1
    mock_movie.title = "Inception"
    mock_movie.year = 2010
    mock_movie.overview = "A thief enters people's dreams."

    mock_get_movie.return_value = mock_movie

    response = client.get("/movies/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Inception"


@patch("app.main.get_movie_by_id")
def test_get_movie_details_not_found(mock_get_movie):
    mock_get_movie.return_value = None

    response = client.get("/movies/99999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Movie not found"
    }


@patch("app.main.process_movie_query")
def test_chat_endpoint(mock_process_query):
    mock_movie = MagicMock()
    mock_movie.id = 1
    mock_movie.title = "Inception"
    mock_movie.year = 2010
    mock_movie.overview = "A thief enters people's dreams."

    mock_process_query.return_value = {
        "parsed_query": {
            "intent": "movie_details",
            "genre": None,
            "year": None,
            "titles": ["Inception"]
        },
        "movies": [mock_movie],
        "response": "Inception is a science fiction film."
    }

    response = client.post(
        "/chat",
        json={"question": "Tell me about Inception"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "Tell me about Inception"
    assert data["parsed_query"]["titles"] == ["Inception"]
    assert data["movies"][0]["title"] == "Inception"
    assert data["response"] == "Inception is a science fiction film."


def test_chat_endpoint_requires_question():
    response = client.post("/chat", json={})

    assert response.status_code == 422
