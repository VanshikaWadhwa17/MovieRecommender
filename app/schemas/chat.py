
from pydantic import BaseModel

from app.schemas.movie import MovieResponse


class ParsedQueryResponse(BaseModel):
    intent: str
    genre: str | None = None
    year: int | None = None
    titles: list[str] = []


class ChatResponse(BaseModel):
    question: str
    parsed_query: ParsedQueryResponse
    movies: list[MovieResponse]
    response: str
