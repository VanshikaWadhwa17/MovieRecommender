
from pydantic import BaseModel, ConfigDict


class MovieResponse(BaseModel):
    id: int
    title: str
    year: int | None = None
    overview: str | None = None
    popularity: float | None = None

    model_config = ConfigDict(from_attributes=True)
