
from pydantic import BaseModel, ConfigDict, Field, AliasPath


class RatingResponse(BaseModel):
    vote_average: float | None = None
    vote_count: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CastResponse(BaseModel):
    name: str = Field(
        validation_alias=AliasPath("person", "name")
    )
    character: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DirectorResponse(BaseModel):
    name: str = Field(
        validation_alias=AliasPath("person", "name")
    )

    model_config = ConfigDict(from_attributes=True)


class MovieResponse(BaseModel):
    id: int
    title: str
    year: int | None = None
    overview: str | None = None
    popularity: float | None = None
    rating: RatingResponse | None = None
    cast_members: list[CastResponse] = Field(default_factory=list)
    directors: list[DirectorResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
