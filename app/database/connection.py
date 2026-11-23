
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Find the project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Store our database inside data/tmdb/
DATABASE_DIR = BASE_DIR / "data" / "tmdb"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_DIR / 'movies.db'}"

# Create the database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all our database models
class Base(DeclarativeBase):
    pass


# Provides a database session to the application
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
