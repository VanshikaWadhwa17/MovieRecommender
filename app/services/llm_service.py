
import os
import requests

from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:7b")

OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))


def generate_response(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=OLLAMA_TIMEOUT
    )

    response.raise_for_status()

    result = response.json()

    return result["response"]


def generate_movie_response(question: str, movies: list) -> str:

    # Build movie context from database results
    movie_context = ""

    for movie in movies:

        # Retrieve rating information
        if movie.rating:
            rating = (
                f"{movie.rating.vote_average}/10 "
                f"({movie.rating.vote_count} votes)"
            )
        else:
            rating = "Not available"

        # Retrieve cast information (top 5 members)
        cast = ", ".join(
            f"{member.person.name} as {member.character}"
            if member.character
            else member.person.name
            for member in movie.cast_members[:5]
        )

        if not cast:
            cast = "Not available"

        # Retrieve director information
        directors = ", ".join(
            director.person.name
            for director in movie.directors
        )

        if not directors:
            directors = "Not available"

        movie_context += f"""
        Title: {movie.title}
        Year: {movie.year}
        Overview: {movie.overview or "Not available"}
        Rating: {rating}
        Cast: {cast}
        Directors: {directors}
        ---
        """

    # Build a stricter prompt for the LLM
    prompt = f"""
    You are a movie information assistant.

    Your task is to answer the user's movie-related question
    using the information provided by the database.

    IMPORTANT:
    The database is your ONLY source of information.
    Do not use your pretrained knowledge.

    RULES:

    1. Only use information explicitly present in the database records.
    2. Use the overview when describing a movie.
    3. Use the cast field when answering questions about actors.
    4. Use the directors field when answering questions about directors.
    5. Use the rating field when answering questions about ratings.
    6. Do not invent facts, actors, characters, ratings or other details.
    7. If information is unavailable, clearly say so.
    8. Do not add promotional language or subjective claims.
    9. Preserve the exact order of the database records.
    10. Write a maximum of TWO sentences per movie.
    11. Do not recommend movies outside the database results.

    USER QUESTION:
    {question}

    DATABASE RECORDS:
    {movie_context}

    Answer the user's question directly using only the supplied
    database records.
    """

    # Generate the response using Ollama
    return generate_response(prompt)
