
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories.movie_repository import get_movies, get_movie_by_id
from app.services.movie_service import search_movies as process_movie_query
from app.schemas.movie import MovieResponse
from pydantic import BaseModel

app = FastAPI(
    title="Movie Recommendation Assistant",
    description="An AI-powered assistant for movie discovery",
    version="1.0.0"
)
class ChatRequest(BaseModel):
    question: str

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Movie Recommendation API is running"
    }


@app.get("/movies", response_model=list[MovieResponse])
def search_movies(
    title: str | None = None,
    year: int | None = None,
    genre: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_movies(
        db=db,
        titles=[title] if title else None,
        year=year,
        genre=genre,
        skip=skip,
        limit=limit
    )


@app.get("/movies/{movie_id}", response_model=MovieResponse)
def get_movie_details(
    movie_id: int,
    db: Session = Depends(get_db)
):
    movie = get_movie_by_id(db, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie not found"
        )

    return movie

@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):

    # Process the user's question
    result = process_movie_query(request.question, db)

    # Return database results and the LLM-generated response
    return {
        "question": request.question,

        "parsed_query": result["parsed_query"],

        "movies": [
            {
                "id": movie.id,
                "title": movie.title,
                "year": movie.year,
                "overview": movie.overview
            }
            for movie in result["movies"]
        ],

        "response": result["response"]
    }