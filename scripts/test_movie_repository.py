
from app.database.connection import SessionLocal
from app.repositories.movie_repository import get_movies


db = SessionLocal()

try:
    # Test 1: Search by title
    print("\n--- Search by title: Inception ---")
    movies = get_movies(db, titles=["Inception"])

    for movie in movies:
        print(movie.title, movie.year)

    # Test 2: Filter by year
    print("\n--- Search by year: 2010 ---")
    movies = get_movies(db, year=2010)

    for movie in movies[:5]:
        print(movie.title, movie.year)

    # Test 3: Filter by genre
    print("\n--- Search by genre: Action ---")
    movies = get_movies(db, genre="Action")

    for movie in movies[:5]:
        print(movie.title, movie.year)
 
    # Test 4: Filter by genre and sort by popularity
    print("\n--- Search by genre: Action (sorted by popularity) ---")
    movies = get_movies(db, genre="Action")

    for movie in movies[:5]:
        print(movie.title, movie.popularity)

finally:
    db.close()
