
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Movie(Base):
    __tablename__ = "movies"

    # TMDB's original movie ID
    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False, index=True)

    release_date = Column(String(20), nullable=True)

    year = Column(Integer, nullable=True, index=True)

    overview = Column(Text, nullable=True)

    popularity = Column(Float, nullable=True)

    rating = relationship(
        "Rating",
        backref="movie",
        uselist=False
    )

    cast_members = relationship(
        "MovieCast",
        backref="movie",
        order_by="MovieCast.cast_order"
    )

    directors = relationship(
        "MovieDirector",
        backref="movie"
    )


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, unique=True)

class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id = Column(
        Integer,
        ForeignKey("movies.id"),
        primary_key=True
    )

    genre_id = Column(
        Integer,
        ForeignKey("genres.id"),
        primary_key=True
    )

class Rating(Base):
    __tablename__ = "ratings"

    movie_id = Column(
        Integer,
        ForeignKey("movies.id"),
        primary_key=True
    )

    vote_average = Column(Float, nullable=True)

    vote_count = Column(Integer, nullable=True)


class Person(Base):
    __tablename__ = "people"

    # Use TMDB's original person ID
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False, index=True)



class MovieCast(Base):
    __tablename__ = "movie_cast"

    id = Column(Integer, primary_key=True, autoincrement=True)

    movie_id = Column(
        Integer,
        ForeignKey("movies.id"),
        nullable=False
    )

    person_id = Column(
        Integer,
        ForeignKey("people.id"),
        nullable=False
    )

    character = Column(String(255), nullable=True)

    cast_order = Column(Integer, nullable=True)

    person = relationship("Person")

class MovieDirector(Base):
    __tablename__ = "movie_directors"

    movie_id = Column(
        Integer,
        ForeignKey("movies.id"),
        primary_key=True
    )

    person_id = Column(
        Integer,
        ForeignKey("people.id"),
        primary_key=True
    )

    person = relationship("Person")
