
from unittest.mock import patch, MagicMock

import requests

from app.services.movie_service import search_movies


@patch("app.services.movie_service.generate_movie_response")
@patch("app.services.movie_service.get_movies")
@patch("app.services.movie_service.parse_query")
def test_search_movies_success(
    mock_parse_query,
    mock_get_movies,
    mock_generate_response
):
    # Arrange: prepare the expected query and database results
    mock_parse_query.return_value = {
        "intent": "movie_details",
        "genre": None,
        "year": None,
        "titles": ["Inception"]
    }

    mock_movie = MagicMock()
    mock_movie.title = "Inception"
    mock_movie.year = 2010

    mock_get_movies.return_value = [mock_movie]
    mock_generate_response.return_value = "Inception is a science fiction film."

    # Act: execute the service
    result = search_movies("Tell me about Inception", MagicMock())

    # Assert: verify the result
    assert len(result["movies"]) == 1
    assert result["movies"][0].title == "Inception"
    assert result["response"] == "Inception is a science fiction film."


@patch("app.services.movie_service.generate_movie_response")
@patch("app.services.movie_service.get_movies")
@patch("app.services.movie_service.parse_query")
def test_search_movies_no_results(
    mock_parse_query,
    mock_get_movies,
    mock_generate_response
):
    mock_parse_query.return_value = {
        "intent": "movie_details",
        "genre": None,
        "year": None,
        "titles": []
    }

    result = search_movies("Tell me about Interstellar 2", MagicMock())

    assert result["movies"] == []
    assert result["response"] == (
        "Sorry, no matching movies were found in the database."
    )

    # Ollama should not be called when no movies are found
    mock_generate_response.assert_not_called()


@patch("app.services.movie_service.generate_movie_response")
@patch("app.services.movie_service.get_movies")
@patch("app.services.movie_service.parse_query")
def test_search_movies_ollama_failure(
    mock_parse_query,
    mock_get_movies,
    mock_generate_response
):
    mock_parse_query.return_value = {
        "intent": "movie_details",
        "genre": None,
        "year": None,
        "titles": ["Inception"]
    }

    mock_movie = MagicMock()
    mock_movie.title = "Inception"
    mock_movie.year = 2010

    mock_get_movies.return_value = [mock_movie]

    mock_generate_response.side_effect = requests.exceptions.ConnectionError(
        "Ollama is unavailable"
    )

    result = search_movies("Tell me about Inception", MagicMock())

    assert len(result["movies"]) == 1
    assert result["movies"][0].title == "Inception"
    assert result["response"] == (
        "The matching movies were found, but the AI response "
        "could not be generated. Please try again later."
    )
