# Movie Recommender

A conversational AI movie assistant that answers movie-related questions using structured database retrieval and LLM-powered response generation.

**Primary data source:** TMDB 5000 Movies dataset (see [decisions.md](decisions.md) for dataset selection rationale).

## Features

- Movie data ingestion from TMDB CSV files into SQLite.
- Structured relational database using SQLAlchemy.
- Movie search by title, year and genre.
- Movie details retrieval by ID.
- Rule-based natural language query parsing.
- Movie information summaries generated using Ollama and Qwen 2.5 7B.
- FastAPI REST API with interactive Swagger documentation.
- Error handling when the local LLM is unavailable.
- Automated tests using pytest.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| API | FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| Data processing | Pandas |
| Validation | Pydantic |
| LLM runtime | Ollama |
| LLM model | Qwen 2.5 7B |
| Testing | Pytest, FastAPI TestClient |

## Project Structure

```text
MovieRecommender/
├── app/
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   ├── repositories/
│   │   └── movie_repository.py
│   ├── schemas/
│   │   ├── chat.py
│   │   └── movie.py
│   ├── services/
│   │   ├── query_parser.py
│   │   ├── movie_service.py
│   │   └── llm_service.py
│   └── main.py
├── data/
│   └── tmdb/
│       ├── movies.csv
│       ├── credits.csv
│       └── movies.db
├── scripts/
│   ├── inspect_data.py
│   ├── init_db.py
│   ├── ingest_movies.py
│   ├── test_movie_repository.py
│   ├── test_query_parser.py
│   ├── test_movie_service.py
│   └── test_llm_service.py
├── tests/
│   ├── test_api.py
│   ├── test_movie_repository.py
│   ├── test_query_parser.py
│   └── test_movie_service.py
├── .env.example
├── .gitignore
├── decisions.md
├── pytest.ini
├── requirements.txt
└── README.md
```

## Setup

Run the following commands from the project root.

**Prerequisites:**
- Python 3.11 or newer
- Git
- Ollama (required for AI-powered responses)

### 1. Clone the repository

```bash
git clone https://github.com/VanshikaWadhwa17/MovieRecommender
cd MovieRecommender
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add the TMDB dataset

Expected files:

- `data/tmdb/movies.csv`
- `data/tmdb/credits.csv`

Download the TMDB 5000 Movie Dataset from [Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) and place the CSV files in `data/tmdb/`.

### 5. Initialize and populate the database

Initialize the database:

```bash
python -m scripts.init_db
```

Ingest the movie dataset:

```bash
python -m scripts.ingest_movies
```

> **Note:** `init_db` creates any missing database tables. It does not reset or delete existing data. The ingestion script populates the database using the supplied CSV files.

The application uses SQLite and stores the generated database at:

```text
data/tmdb/movies.db
```

### 6. Configure environment variables

Create your local environment file using the example:

```bash
cp .env.example .env
```

The default configuration is:

```env
OLLAMA_URL=http://localhost:11434/api/generate
MODEL_NAME=qwen2.5:7b
OLLAMA_TIMEOUT=300
```

The `.env` file is excluded from Git to keep local configuration separate from the tracked project files.

### 7. Install and start Ollama

Install Ollama from [https://ollama.com/](https://ollama.com/).

Download the configured model:

```bash
ollama pull qwen2.5:7b
```

Verify the installed model:

```bash
ollama list
```

Make sure the Ollama service is running before using the AI-powered chat endpoint.

## Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### Interactive API Documentation

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API health |
| GET | `/movies` | Search movies using filters |
| GET | `/movies/{movie_id}` | Retrieve movie details |
| POST | `/chat` | Process a natural language movie query |

### Example: Search Movies

```http
GET /movies?genre=Action&year=2015
```

Optional query parameters:

- `title`: Filter by movie title.
- `year`: Filter by release year.
- `genre`: Filter by genre.
- `skip`: Number of records to skip.
- `limit`: Maximum number of records (default: 10, maximum: 100).

### Example: Movie Details

```http
GET /movies/27205
```

### Example: Conversational Movie Query

Request:

```json
{
  "question": "Tell me about Inception"
}
```

Endpoint:

```http
POST /chat
```

Successful response:

```json
{
  "question": "Tell me about Inception",
  "parsed_query": {
    "intent": "movie_details",
    "genre": null,
    "year": null,
    "titles": [
      "Inception"
    ]
  },
  "movies": [
    {
      "id": 27205,
      "title": "Inception",
      "year": 2010,
      "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets is offered a chance to regain his old life as payment for a task considered to be impossible: \"inception\", the implantation of another person's idea into a target's subconscious.",
      "rating": {
        "vote_average": 8.1,
        "vote_count": 13752
      },
      "cast_members": [
        {
          "name": "Leonardo DiCaprio",
          "character": "Dom Cobb"
        },
        {
          "name": "Joseph Gordon-Levitt",
          "character": "Arthur"
        },
        {
          "name": "Ellen Page",
          "character": "Ariadne"
        },
        {
          "name": "Tom Hardy",
          "character": "Eames"
        },
        {
          "name": "Ken Watanabe",
          "character": "Saito"
        }
      ],
      "directors": [
        {
          "name": "Christopher Nolan"
        }
      ]
    }
  ],
  "response": "Inception is a 2010 film directed by Christopher Nolan. The movie, with a rating of 8.1/10, follows Dom Cobb, played by Leonardo DiCaprio, as he attempts to implant an idea into someone's subconscious mind."
}
```

> Note: The cast list in this documentation example is abbreviated to the first five entries. The actual API response includes the full cast retrieved from the database.

The response demonstrates:
- Natural-language query parsing.
- Structured movie retrieval from SQLite.
- Movie overview, rating, cast and director information.
- LLM-generated response using database-provided context.

### Example: Movie Recommendations

Request:

```json
{
  "question": "Recommend some action movies"
}
```

Endpoint:

```http
POST /chat
```

The response includes a short LLM-generated introduction followed by a complete recommendation list built from the database records (title, year, rating, vote count and director), preserving the database ranking.

### Example: No Matching Movies

Request:

```json
{
  "question": "Recommend action movies from 2020"
}
```

Response:

```json
{
  "question": "Recommend action movies from 2020",
  "parsed_query": {
    "intent": "recommend",
    "genre": "Action",
    "year": 2020,
    "titles": []
  },
  "movies": [],
  "response": "Sorry, no matching movies were found in the database."
}
```

### Example: Ollama Unavailable

If Ollama is unavailable, the application still retrieves matching movie records from SQLite but returns a fallback response instead of an AI-generated summary.

To verify this behaviour:

1. Stop Ollama temporarily, but leave the FastAPI server running.
2. Run:

```bash
curl -X POST http://127.0.0.1:8000/chat \
-H "Content-Type: application/json" \
-d '{"question":"Tell me about Inception"}'
```

Example fallback message:

```text
The matching movies were found, but the AI response could not be generated. Please try again later.
```

## Automated Testing

The project uses pytest for automated testing.

Run the complete test suite:

```bash
python -m pytest -v
```

Pytest is configured through `pytest.ini` to discover tests only inside the `tests/` directory.

Current automated test coverage includes:

| Test module | Coverage |
|---|---|
| `test_query_parser.py` | Intent, genre, year and title extraction |
| `test_movie_repository.py` | Database retrieval, filtering, sorting, pagination and service integration |
| `test_movie_service.py` | Movie query processing and LLM failure handling |
| `test_api.py` | API endpoints, response validation and error handling |

**Current test status:** 40 automated tests passing.

## Dataset Information

The project uses the TMDB 5000 Movies dataset.

### Movies

- **Rows:** 4,803
- **Fields include:** title, overview, genres, release date, vote average, vote count and popularity.

### Credits

- **Rows:** 4,803
- **Fields:** movie ID, title, cast and crew.

### Dataset Coverage

- **Earliest movie release year:** 1916
- **Latest movie release year:** 2017
- **Total movies:** 4,803

The dataset does not contain movies released after 2017. Queries for later years will therefore return no matching records.

### Database Design

The relational database contains seven tables:

1. `movies`
2. `genres`
3. `movie_genres`
4. `ratings`
5. `people`
6. `movie_cast`
7. `movie_directors`

The dataset contains nested JSON fields, including genres, cast and crew, which are parsed during ingestion.

## Architecture and Design Decisions

The application follows a modular monolith architecture:

- **API layer:** Handles HTTP requests and responses.
- **Repository layer:** Handles database queries.
- **Service layer:** Processes natural language queries and coordinates LLM responses.
- **Database layer:** Stores structured movie information.
- **LLM integration:** Uses retrieved database information to generate natural-language summaries.

The database is the source of truth. The LLM is used to summarise retrieved information rather than independently retrieve or invent movie facts.

Architectural choices, implementation trade-offs and known limitations are documented in [decisions.md](decisions.md).

## Known Limitations

- **Dataset coverage:** The TMDB dataset contains movies released between 1916 and 2017. More recent releases are not available.
- **Query understanding:** Natural language parsing is rule-based and may not correctly interpret complex or ambiguous questions.
- **Movie title matching:** Partial title matching is supported, but typo handling and ambiguous title resolution are limited.
- **Personalisation:** Recommendations are based on movie metadata and ratings, not individual user preferences or viewing history.
- **LLM consistency:** The LLM may occasionally produce imperfect introductory text. Recommendation titles and details are generated from database records to preserve completeness and ordering.
- **Local LLM dependency:** AI-powered responses require Ollama and the configured model to be available. The application has fallback handling when Ollama is unavailable.
- **Database updates:** The database reflects the supplied CSV files and does not automatically update when new movie data becomes available.

## Future Improvements

Potential areas for further development include:

- More robust natural language query understanding.
- Improved movie title matching and typo handling.
- Improve factual consistency of LLM-generated introductory text.
- Expanded automated testing.
- Additional API validation and integration tests.
- Deployment and production configuration.

---

**Note:** This project is being developed incrementally. The README will evolve as additional functionality is implemented.
