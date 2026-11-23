
import json
import logging
from pathlib import Path

import pandas as pd

from app.database.connection import SessionLocal
from app.database.models import Movie, Genre, MovieGenre, Rating, Person, MovieCast, MovieDirector


# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]

MOVIES_CSV = BASE_DIR / "data" / "tmdb" / "movies.csv"
CREDITS_CSV = BASE_DIR / "data" / "tmdb" / "credits.csv"


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def load_datasets():
    """Read the movie and credits CSV files."""

    logger.info("Loading TMDB datasets...")

    movies_df = pd.read_csv(MOVIES_CSV)
    credits_df = pd.read_csv(CREDITS_CSV)

    logger.info("Movies loaded: %d", len(movies_df))
    logger.info("Credits loaded: %d", len(credits_df))

    return movies_df, credits_df


def parse_json_field(value):
    """Safely convert a JSON string into a Python list."""

    if not isinstance(value, str) or not value.strip():
        return []

    try:
        result = json.loads(value)

        if isinstance(result, list):
            return result

        return []

    except json.JSONDecodeError:
        logger.warning("Could not parse a JSON field")
        return []


def main():
    movies_df, credits_df = load_datasets()
    # Create a lookup using TMDB movie IDs
    credits_lookup = credits_df.set_index("movie_id").to_dict("index")

    # Temporarily inspect Avatar's cast
    # avatar_credits = credits_lookup.get(19995)

    # avatar_cast = parse_json_field(avatar_credits["cast"])

    # for actor in avatar_cast[:5]:
    #     print(actor["id"], actor["name"], actor["character"])
    #till here

    logger.info("Starting movie and genre insertion...")

    db = SessionLocal()

    # Remember genre IDs already processed during this run
    processed_genre_ids = set()

    processed_person_ids = set()

    try:
        # Rebuild cast relationships from the source dataset
        db.query(MovieCast).delete(synchronize_session=False)

        
        for _, row in movies_df.iterrows():

            movie_id = int(row["id"])
            credits = credits_lookup.get(movie_id)
            # if credits:
            #     print(credits.keys())
            #     print(credits["cast"][:200])

            # --------------------------------
            # 1. Insert movie information
            # --------------------------------

            # Extract release date
            release_date = (
                str(row["release_date"])
                if pd.notna(row["release_date"])
                else None
            )

            # Extract year from release date
            year = None

            if release_date and len(release_date) >= 4:
                year = int(release_date[:4])

            # Create a Movie object
            movie = Movie(
                id=movie_id,
                title=row["title"],
                release_date=release_date,
                year=year,
                overview=(
                    row["overview"]
                    if pd.notna(row["overview"])
                    else None
                ),
                popularity=(
                    float(row["popularity"])
                    if pd.notna(row["popularity"])
                    else None
                )
            )

            db.merge(movie)
            # --------------------------------
            # 2. Insert movie ratings
            # --------------------------------

            rating = Rating(
                movie_id=movie_id,
                vote_average=(
                    float(row["vote_average"])
                    if pd.notna(row["vote_average"])
                    else None
                ),
                vote_count=(
                    int(row["vote_count"])
                    if pd.notna(row["vote_count"])
                    else None
                )
            )

            db.merge(rating)

            # --------------------------------
            # 3. Insert genres and relationships
            # --------------------------------

            genres = parse_json_field(row["genres"])

            for genre_data in genres:

                genre_id = int(genre_data["id"])
                genre_name = genre_data["name"]

                # Insert each unique genre only once
                if genre_id not in processed_genre_ids:

                    genre = Genre(
                        id=genre_id,
                        name=genre_name
                    )

                    db.merge(genre)

                    # Remember that we processed this genre
                    processed_genre_ids.add(genre_id)

                # Connect this movie to its genre
                movie_genre = MovieGenre(
                    movie_id=movie_id,
                    genre_id=genre_id
                )

                db.merge(movie_genre)
            
            # --------------------------------
            # 4. Insert actors and cast relationships
            # --------------------------------


            if credits:
                cast_members = parse_json_field(credits["cast"])

                for actor_data in cast_members:

                    person_id = int(actor_data["id"])
                    person_name = actor_data["name"]

                    # Insert each person only once
                    if person_id not in processed_person_ids:

                        person = Person(
                            id=person_id,
                            name=person_name
                        )

                        db.merge(person)
                        processed_person_ids.add(person_id)

                    # Connect actor to the movie
                    movie_cast = MovieCast(
                        movie_id=movie_id,
                        person_id=person_id,
                        character=actor_data["character"],
                        cast_order=actor_data["order"]
                    )

                    db.merge(movie_cast)
            
            # --------------------------------
            # 5. Insert directors and relationships
            # --------------------------------

            crew_members = parse_json_field(credits["crew"])

            for crew_member in crew_members:

                # We only want directors, not the entire crew
                if crew_member.get("job") != "Director":
                    continue

                person_id = int(crew_member["id"])
                person_name = crew_member["name"]

                # Insert director into people if not already processed
                if person_id not in processed_person_ids:

                    person = Person(
                        id=person_id,
                        name=person_name
                    )

                    db.merge(person)
                    processed_person_ids.add(person_id)

                # Connect director to the movie
                movie_director = MovieDirector(
                    movie_id=movie_id,
                    person_id=person_id
                )

                db.merge(movie_director)

        # Save all database changes
        db.commit()

        logger.info(
            "Successfully processed %d movies",
            len(movies_df)
        )

        logger.info(
            "Successfully processed %d unique genres",
            len(processed_genre_ids)
        )

        logger.info("Movie-genre relationships processed successfully")

    except Exception:
        db.rollback()
        logger.exception("Movie insertion failed")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
