
from app.database.connection import Base, engine
from app.database import models


def initialize_database():
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database created successfully!")
    print("Tables:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    initialize_database()
