import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


def generate_response(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )

    response.raise_for_status()

    result = response.json()

    return result["response"]

def generate_movie_response(question: str, movies: list) -> str:

    # Build movie context from database results
    movie_context = ""

    for movie in movies:
        movie_context += f"""
        Title: {movie.title}
        Year: {movie.year}
        Overview: {movie.overview}
        ---
        """

    # Build a stricter prompt for the LLM
    prompt = f"""
        You are a movie information assistant.

        Your task is to summarise the movie information provided
        by the database.

        IMPORTANT:
        The database is your ONLY source of information.
        Do not use your pretrained knowledge.

        RULES:

        1. Only use information explicitly stated in the movie overview.
        2. Do not add facts, characters, events, scenes or descriptions
        that are not present in the overview.
        3. Do not add promotional language or subjective claims.
        4. Do not invent genres, ratings, actors, awards or soundtrack details.
        5. Preserve the exact order of the database records.
        6. Write a maximum of TWO sentences per movie.
        7. If the overview is empty, say that no description is available.
        8. Do not recommend movies outside the database results.

        USER QUESTION:
        {question}

        DATABASE RECORDS:
        {movie_context}

        Summarise each movie using only its database overview.
        """


    # Generate the response using Ollama
    return generate_response(prompt)