
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


def generate_movie_response(
    question: str,
    movies: list,
    intent: str
) -> str:

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

    # Identify recommendation requests using the parsed intent.
    # The movie service passes the intent returned by query_parser.
    is_recommendation = intent == "recommend"

    # Recommendation response:
    # Let the LLM generate only a short introduction.
    # Python will generate the actual movie list.
    if is_recommendation:

        prompt = f"""
        You are a movie information assistant.

        The user has asked for movie recommendations.

        Write ONE short introductory sentence.
        Do not list movie titles.
        Do not describe individual movies.
        Do not invent facts.
        Do not add promotional language.

        USER QUESTION:
        {question}

        DATABASE RECORDS:
        {movie_context}
        """

        introduction = generate_response(prompt).strip()

        # Generate the complete recommendation list directly
        # from database records, preserving their original order.
        recommendation_list = []

        for movie in movies:

            if movie.rating:
                rating = (
                    f"{movie.rating.vote_average}/10 "
                    f"({movie.rating.vote_count} votes)"
                )
            else:
                rating = "Not available"

            directors = ", ".join(
                director.person.name
                for director in movie.directors
            )

            if not directors:
                directors = "Not available"

            recommendation_list.append(
                f"- **{movie.title} ({movie.year or 'Year unavailable'})**\n"
                f"  - Rating: {rating}\n"
                f"  - Director: {directors}"
            )

        return (
            f"{introduction}\n\n"
            + "\n\n".join(recommendation_list)
        )

    # For non-recommendation questions, retain the existing
    # database-grounded LLM response behaviour.
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
    10. Do not recommend movies outside the database results.
    11. Write a maximum of TWO sentences per movie.
    12. Keep each movie's title, year and rating clear and readable.

    USER QUESTION:
    {question}

    DATABASE RECORDS:
    {movie_context}

    Answer the user's question directly using only the supplied
    database records.
    """

    # Generate the response using Ollama
    return generate_response(prompt)
