# Decisions Log

A running record of architectural and product choices, with context and rationale.

---

## 1. Choice of dataset

### Dataset Selection

**Decision:** Use the TMDB 5000 Movies dataset instead of MovieLens Small as the primary data source.

**Status:** Accepted

### 1. Context

The coding challenge requires building a conversational AI movie assistant that can answer movie-related questions using structured database retrieval and LLM-powered response generation.

The requirements specifically mention the following movie attributes:

- Movie title
- Release year
- Genres
- Overview / plot
- Ratings
- Cast
- Director

Two datasets were considered:

- TMDB 5000 Movies Dataset
- MovieLens Small Dataset

Although MovieLens contains approximately 9,700 movie records compared with approximately 4,800 in TMDB 5000, dataset size was not the primary selection criterion.

### 2. Options evaluated

#### Option A: MovieLens Small

**Advantages:**

- Larger number of movie records.
- Contains individual user ratings.
- Supports rating-based and collaborative-filtering recommendation approaches.
- Includes movie genres and external movie ID mappings.

**Limitations:**

- Does not provide movie plot descriptions.
- Does not provide cast and director information in its standard small dataset.
- Would require another source to fulfil the challenge's metadata requirements.

#### Option B: TMDB 5000

**Advantages:**

- Provides movie titles and release information.
- Includes genres and plot overviews.
- Includes cast and crew information.
- Provides average ratings (`vote_average`) and vote counts (`vote_count`).
- Supports richer conversational responses without requiring an additional metadata source.

**Limitations:**

- Contains fewer movie records than MovieLens Small.
- Does not provide individual user rating histories.
- Cannot directly support user-level collaborative filtering.

### 3. Decision rationale

TMDB 5000 was selected because it offers better alignment with the core functional requirements of the challenge.

The primary objective is to build a conversational movie assistant, not exclusively a recommendation engine.

For example, questions such as:

- "Tell me about Inception."
- "Which movies feature Leonardo DiCaprio?"
- "Recommend action movies from 2020."

require metadata such as plot descriptions, cast, directors and genres.

TMDB provides these attributes directly, allowing the application to retrieve factual information from a single dataset and pass it to the LLM for conversational response generation.

MovieLens has more movie records and richer individual rating information, but using it alone would leave important challenge requirements unmet.

### 4. Consequences of the decision

**Positive:**

- Simpler ingestion pipeline.
- Fewer external data dependencies.
- Less data reconciliation and ID mapping.
- Richer context for LLM-powered responses.
- Better alignment with the challenge's specified fields.

**Trade-off:**

- Fewer movies available.
- No individual user rating histories.
- Limited support for personalised collaborative-filtering recommendations.

### 5. Future enhancement

MovieLens could be integrated in a future iteration to introduce individual user ratings and personalised recommendations.

However, this is outside the initial implementation scope and is not necessary to satisfy the current challenge.

### 6. Final decision

TMDB 5000 was selected based on data relevance and completeness rather than raw record count.

The decision prioritises fulfilling the application's core requirements while keeping the initial architecture simple, maintainable and extensible.

### 7. FAQ

**Q: Couldn't we have used both datasets?**

Yes. We could join them using the MovieLens `links.csv` mapping between MovieLens IDs and TMDB IDs. However, that introduces additional ingestion, reconciliation and data-quality considerations. Since the challenge doesn't require individual user ratings, the extra complexity isn't justified in the first iteration.

**Q: Does TMDB support movie recommendations?**

Yes. We can recommend movies using genre, release year, TMDB ratings, vote counts and popularity. More sophisticated personalised recommendations would require additional user preference data.

**Q: Does having fewer movies affect scalability?**

No, not in any meaningful architectural sense for this challenge. Dataset size is a data coverage decision, not a reason to introduce microservices or distributed infrastructure.

---

## 2. Database design and schema

### 1. Context

The application needs to store movie information in a structured format so that it can efficiently retrieve movies based on attributes such as title, genre, release year, ratings, cast and director.

The challenge specifically requires a local SQLite database with separate tables for movies, genres and ratings.

Rather than storing all information in one large table, I chose a normalized relational database design.

### 2. Decision

**Decision:** Use a normalized relational schema consisting of seven tables.

**Status:** Accepted

The tables are:

| Table | Purpose |
|---|---|
| `movies` | Stores core movie information such as title, release date, year, overview and popularity. |
| `genres` | Stores unique movie genres. |
| `movie_genres` | Connects movies with their genres. |
| `ratings` | Stores TMDB's aggregate movie rating and vote count. |
| `people` | Stores actors and directors. |
| `movie_cast` | Connects actors to movies, including their character and cast order. |
| `movie_directors` | Connects directors to movies. |

### 3. Why separate tables?

A movie can belong to multiple genres, and a genre can belong to multiple movies.

For example, Avatar belongs to Action, Adventure, Fantasy and Science Fiction.

Instead of storing all four genres as a comma-separated string in the movies table, I created a separate `genres` table and a `movie_genres` mapping table.

This represents a many-to-many relationship.

The same principle applies to people:

- One movie can have many actors.
- One actor can appear in many movies.
- One movie can have one or more directors.

The `people` table avoids storing the same person's details repeatedly.

### 4. Primary keys and relationships

I use TMDB IDs as primary keys wherever possible.

For example:
- `movies.id` uses the TMDB movie ID.
- `genres.id` uses the TMDB genre ID.
- `people.id` uses the TMDB person ID.

This allows records to be connected using stable identifiers instead of names.

Names are not reliable identifiers because different people can have the same name.

The mapping tables use composite primary keys to prevent duplicate movie-to-genre and movie-to-person associations.

### 5. Ratings decision

TMDB provides two relevant fields:

- `vote_average`
- `vote_count`

These represent TMDB's aggregate rating and the number of votes contributing to it.

I store them in a separate `ratings` table, with one rating record per movie.

These are not individual user rating records. Therefore, I will not treat them as personalised user ratings.

### 6. Consequences

**Positive:**
- Less duplicated information.
- Easier filtering and querying.
- Clear relationships between movies, genres and people.
- Easier to extend the schema later.
- Better alignment with relational database principles.

**Trade-off:**
- Queries involving multiple attributes may require SQL joins.
- Ingestion requires processing and inserting related records into multiple tables.

### 7. Final decision

Use seven normalized tables with TMDB identifiers and explicit mapping tables for many-to-many relationships.

---

## 3. Data ingestion approach

### 1. Context

The TMDB dataset is provided as two CSV files:

- `movies.csv`: Contains movie information, genres, overview, release date and aggregate ratings.
- `credits.csv`: Contains cast and crew information.

Both files contain 4,803 records.

Some columns, including `genres`, `cast` and `crew`, contain JSON-formatted strings rather than ordinary CSV values.

The data needs to be parsed, matched and transformed before it can be stored in the relational database.

### 2. Initial validation

**Decision:** Use Python and pandas to read and inspect the CSV files.

**Status:** Initial validation completed.

The first ingestion script successfully:

- Loaded both CSV files.
- Confirmed that both contain 4,803 records.
- Matched movie records using the TMDB movie ID.
- Parsed the JSON-formatted genre, cast and crew fields.
- Identified directors by filtering crew records where `job == "Director"`.

Initial validation using Avatar confirmed:

- Movie ID: `19995`
- Genres: 4
- Cast members: 83
- Directors: 1

### 3. Data transformation

The ingestion pipeline will transform the CSV records into the seven-table relational schema.

For example:

- Movie details will be inserted into `movies`.
- Genre information will be inserted into `genres` and linked through `movie_genres`.
- Aggregate ratings will be inserted into `ratings`.
- Actor and director details will be stored in `people`.
- Cast and director associations will be stored in their respective mapping tables.

### 4. Data integrity and repeatability

The ingestion process should be safe to execute more than once.

It should avoid creating duplicate records when the same dataset is processed again.

The pipeline will also use database transactions so that a failed ingestion does not leave the database in a partially updated state.

### 5. Current status

The CSV loading, JSON parsing and insertion of records into SQLite have been completed and validated.

All seven database tables have been populated. Verified record counts and relationship checks are documented in Section 3.5 Data Ingestion Completion.

### 6. Final decision

Use a Python-based ingestion script with pandas for CSV processing and SQLAlchemy for database interaction.

### 3.1 Movie Ratings Ingestion

**What we implemented**

After inserting movie records, we also populated the `ratings` table using the `vote_average` and `vote_count` columns from TMDB's `movies.csv`.

For every movie:
- `movie_id` stores the corresponding TMDB movie ID.
- `vote_average` stores TMDB's aggregated average rating.
- `vote_count` stores the number of votes contributing to that rating.

**Why we chose this approach**

The challenge requires movie ratings. TMDB already provides aggregated ratings, so we can use these directly instead of introducing another dataset.

We maintain a separate `ratings` table to keep rating information separate from the core movie details.

**Implementation details**

- Used SQLAlchemy's `Rating` model to create rating records.
- Used `db.merge()` to insert or update records based on their primary key.
- Used `pd.notna()` to handle missing rating values safely.
- Stored one rating record per movie, linked through `movie_id`.

**Validation and results**

Verified the ingestion using SQLite:

| Table | Record count |
|---|---:|
| `ratings` | 4,803 |

Also checked Avatar (TMDB ID: 19995):

- Average rating: 7.2
- Vote count: 11,800

The results confirmed that all 4,803 movies have corresponding rating records and that the relationship between `movies` and `ratings` works correctly.

**Current status:** Completed and verified.

### 3.2 Cast Data Ingestion

**Source:** `credits.csv`

**Fields extracted:**
- `id`: TMDB person ID
- `name`: Actor's name
- `character`: Character portrayed
- `order`: Cast billing order

**Implementation:**
1. Matched each movie to its credits using the TMDB movie ID.
2. Parsed the JSON-formatted cast column.
3. Inserted each person into the `people` table.
4. Used a Python set (`processed_person_ids`) to avoid repeatedly inserting the same person.
5. Inserted each cast credit into `movie_cast`, linking the movie and person.

**Database design decision:**

Initially, `movie_id` and `person_id` formed a composite primary key. Ingestion failed because the source contained multiple cast entries for the same movie-person combination.

We changed the design to use an independent auto-incrementing `id` as the primary key. This allows multiple cast credits for the same person in the same movie, while preserving each character entry.

**Validation:**
- 54,588 people records inserted.
- 106,257 cast records inserted.
- Verified Avatar's first five cast members using a SQL join across `movies`, `people`, and `movie_cast`.

**Outcome:** Cast data successfully ingested and relationships verified.

### 3.3 Director Data Ingestion

**Source:** `credits.csv`, specifically the `crew` column.

**Implementation:**
1. Parsed the JSON-formatted crew data.
2. Filtered crew members where `job == "Director"`.
3. Reused the existing `people` table to store director information.
4. Used the shared `processed_person_ids` Python set to avoid processing the same person repeatedly.
5. Inserted movie-director relationships into `movie_directors`.

**Database design decision:**

Kept `movie_directors` as a junction table with a composite primary key (`movie_id`, `person_id`).

This allows:
- One movie to have multiple directors.
- One director to be associated with multiple movies.
- No duplicate relationship between the same movie and director.

**Validation:**
- 5,166 director relationships.
- 56,603 unique people across cast and crew.
- Christopher Nolan's eight movie relationships successfully verified.
- 30 movies had no director relationship in the source data.

**Outcome:** Director data successfully ingested and relationships verified.

### 3.4 Making Cast Ingestion Repeatable (Idempotency)

**Problem:**

After changing `MovieCast` to use an auto-incrementing primary key, repeated ingestion runs created duplicate cast records.

The original `db.merge()` approach could identify existing records using their primary keys. However, each new cast object received a new generated ID, so SQLAlchemy treated it as a new record.

**Solution:**

Before processing the dataset, delete existing records from `movie_cast`:

```python
db.query(MovieCast).delete(synchronize_session=False)
```

Then rebuild the cast relationships from the source CSV.

**Why this approach?**
- Prevents duplicate cast records on repeated executions.
- Keeps the implementation simple for a relatively small dataset.
- Uses a single database transaction.
- If ingestion fails, the rollback also restores the previously deleted cast records.

**Validation:**
- First ingestion: 106,257 cast records.
- Repeated ingestion: 106,257 cast records.
- Confirmed that subsequent executions do not increase the record count.

**Future improvement:**

For larger datasets, consider database-level upserts or incremental ingestion rather than deleting and rebuilding all relationships.

### 3.5 Data Ingestion Completion

**Status:** Completed and verified.

The TMDB dataset has now been ingested into the local SQLite database.

| Table | Verified record count |
|---|---:|
| `movies` | 4,803 |
| `genres` | 20 |
| `movie_genres` | 12,160 |
| `ratings` | 4,803 |
| `people` | 56,603 |
| `movie_cast` | 106,257 |
| `movie_directors` | 5,166 |

**Validation performed:**

- Verified movie, genre and rating records.
- Verified Avatar's genres and first five cast members.
- Verified Christopher Nolan's movie-director relationships.
- Identified 30 movies without a director relationship in the source data.
- Repeated ingestion and confirmed that cast records do not accumulate duplicates.

**Outcome:**

All seven tables have been populated and validated. The database is ready to support movie retrieval through the API layer.

---

## 4. Handling duplicate genres during ingestion

### 1. Problem encountered

During the initial genre ingestion implementation, the script failed with:

`UNIQUE constraint failed: genres.id`

The issue occurred because genres are shared across multiple movies.

For example, the Action genre (TMDB genre ID 28) appears in many movies.

The initial implementation attempted to insert the same genre repeatedly while processing different movies.

### 2. Root cause

The `genres` table uses the TMDB genre ID as its primary key.

This means each genre ID can only exist once in the table.

Although SQLAlchemy's `merge()` can reconcile an object with an existing database record, it does not automatically deduplicate multiple pending objects with the same primary key within the same transaction.

### 3. Solution

I introduced a Python `set` called `processed_genre_ids`.

Before inserting a genre, the script checks whether its ID has already been processed during the current ingestion run.

- If the genre ID is new, the genre is inserted and its ID is added to the set.
- If the genre ID has already been processed, the genre insertion is skipped.

However, the movie-to-genre relationship is still created for every movie.

### 4. Why this approach?

This separates two responsibilities:

- `genres`: Stores each unique genre only once.
- `movie_genres`: Stores the relationship between each movie and its genres.

For example, Action is stored once in `genres`, but can have thousands of associations in `movie_genres`.

The Python set prevents duplicate genre insertion without losing any movie-to-genre relationships.

### 5. Final decision

Use an in-memory Python set to deduplicate genre IDs during ingestion.

This is simple and efficient for the current dataset size of approximately 4,800 movies.

The database primary key remains the final safeguard against duplicate genre records.

---

## 5. API architecture and implementation

### 1. Context

After completing database creation and data ingestion, the next requirement is to expose movie information through an API.

The application needs to support structured movie searches initially, followed by conversational queries handled by an LLM.

I chose FastAPI because it provides request handling, input validation, automatic API documentation and integration with Python-based services.

### 2. Architectural decision

**Decision:** Use a layered architecture within a single FastAPI application (modular monolith).

**Status:** Accepted

The application will separate responsibilities into the following layers:

| Layer | Responsibility |
|---|---|
| API | Receives HTTP requests and returns responses. |
| Repository | Retrieves and filters records from the database. |
| Database | Defines SQLAlchemy models and manages database connections. |
| Service | Contains business logic; coordinates query parsing, repository retrieval and LLM response generation. |
| Schema | Defines and validates API request and response structures using Pydantic. |

This separation avoids putting database queries, business logic and HTTP handling into one file.

### 3. Initial project structure

```text
MovieRecommender/
├── app/
│   ├── main.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── models.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── movie_repository.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── movie.py
│   └── services/
│       ├── __init__.py
│       └── query_parser.py
├── scripts/
├── data/
│   └── tmdb/
├── decisions.md
└── requirements.txt
```

### 4. Health-check endpoint

**Implementation:** Created `GET /health` in `app/main.py`.

The endpoint returns the application's health status.

Example response:

```json
{
    "status": "healthy",
    "message": "Movie Recommendation API is running"
}
```

**Validation:** Successfully started the FastAPI application using Uvicorn and verified the endpoint locally.

FastAPI's interactive API documentation is available through `/docs`.

**Outcome:** The application starts successfully and responds to HTTP requests.

### 5. Movie repository

**Implementation:** Created `app/repositories/movie_repository.py`.

The repository contains a `get_movies()` function that retrieves movies using SQLAlchemy.

Supported filters:

- Title: partial, case-insensitive title matching.
- Year: exact release-year matching.
- Genre: genre-based filtering through joins.
- Pagination: `skip` and `limit` parameters.

The repository uses joins across `movies`, `movie_genres` and `genres` when filtering by genre.

`distinct()` prevents duplicate movie results when joins produce repeated rows.

**Why a repository layer?**

Database retrieval should be independent of HTTP request handling.

This makes the code easier to test and allows the underlying database implementation to change without requiring the API layer to be rewritten.

### 6. Repository validation

Created a temporary test script, `scripts/test_movie_repository.py`, to test the repository directly against SQLite.

**Tests performed:**

| Test | Result |
|---|---|
| Search by title: Inception | Passed |
| Filter by year: 2010 | Passed |
| Filter by genre: Action | Passed |

The repository successfully returned the expected movie records.

#### Popularity-Based Sorting

**Decision:** Sort movie search results by popularity in descending order before applying pagination.

**Implementation:**
```python
query = query.order_by(Movie.popularity.desc())
query = query.offset(skip).limit(limit)
```

**Reasoning:**
- When multiple movies match a user's filters, more popular movies appear first.
- Provides a useful default ordering for movie discovery.
- Sorting before pagination ensures that each page follows the same popularity ranking.

**Validation:** Tested using the Action genre. The first five results were returned in descending popularity order, confirming the implementation works as expected.

#### GET /movies/{movie_id} — Movie Details Endpoint

**Decision:** Provide an endpoint to retrieve an individual movie using its TMDB ID.

**Implementation:**
- Added `get_movie_by_id()` to the movie repository.
- Added `GET /movies/{movie_id}` to FastAPI.
- Used the existing `MovieResponse` Pydantic schema to structure the response.
- Return HTTP 200 when the movie exists.
- Return HTTP 404 with `"Movie not found"` when the movie does not exist.

**Validation:**
- TMDB ID `27205` successfully returned Inception (2010).
- TMDB ID `999999999` correctly returned HTTP 404.

**Reasoning:** Separating database retrieval from API handling keeps responsibilities clear. The repository retrieves the record, while the API decides how to communicate success or failure to the caller.

### 7. Current API implementation status

| Component | Status |
|---|---|
| FastAPI application | Completed |
| `GET /health` | Completed and tested |
| Movie repository | Implemented and tested |
| Title filtering | Tested |
| Year filtering | Tested |
| Genre filtering | Tested |
| Pagination | Completed and tested |
| Popularity sorting | Completed and tested |
| `GET /movies` | Completed and tested through Swagger |
| `GET /movies/{movie_id}` | Completed and tested |
| Query parser: intent detection | Implemented and tested |
| Query parser: genre extraction | Implemented and tested; all 20 genres supported |
| Query parser: year extraction | Implemented and tested |
| Query parser: movie-title extraction | Implemented and tested; LOTR partial matching is still dataset-specific |
| Query parser: combined `parse_query()` | Implemented and tested |
| Movie query execution service | Implemented and tested independently |
| `POST /chat` | Completed and tested end-to-end through Swagger |
| LLM integration | Completed end-to-end through `POST /chat` (see Sections 21–22) |

### 8. Final decision

Use FastAPI with separate API, repository, database, schema and service responsibilities.

Start with structured SQL-based movie retrieval before introducing LLM-powered conversational functionality.

This keeps the initial implementation simple, testable and extensible.

---

## 6. Natural Language Query Parsing

### 1. Context

The application needs to understand natural-language questions before retrieving relevant movie information from the database.

For example:

"Recommend action movies from 2020."

The application needs to identify:
- Intent: recommend
- Genre: Action
- Year: 2020
- Title: None

The extracted information will be passed to the repository layer to retrieve matching movies.

### 2. Initial architectural decision

**Decision:** Start with rule-based query parsing instead of introducing an LLM for query understanding immediately.

**Reasoning:**
- Rule-based parsing is predictable and easy to test.
- Genre extraction can use the known list of database genres.
- Year extraction can use a predictable numerical pattern.
- Database queries remain controlled by application code rather than generated directly by an LLM.
- This keeps the initial implementation simple while allowing more intelligent parsing to be introduced later.

### 3. Initial implementation

Created `app/services/query_parser.py`.

The parser currently contains the following functions:

**`detect_intent(question)`**

Identifies the user's intention using keywords.

Supported intents:
- recommend
- movie_details
- search (default)

**`extract_genre(question)`**

Identifies a genre mentioned in the question.

The supported genre list contains all 20 genres present in the SQLite database, including Foreign.

**`extract_year(question)`**

Uses Python's regular expressions to extract a four-digit year between 1900 and 2099.

**`extract_title(question, db)`**

Retrieves movie titles from the database and checks whether a title appears in the user's question.

The current implementation checks longer titles first to reduce incorrect matches between titles that share similar wording.

### 4. Initial testing and validation

Created `scripts/test_query_parser.py` to test the parsing functions independently.

**Intent detection:**

| Question | Expected result |
|---|---|
| Recommend action movies from 2020 | recommend |
| Tell me about Inception | movie_details |
| Show me movies from 2015 | search |

All tested cases passed.

**Genre extraction:**

| Question | Expected result |
|---|---|
| Recommend action movies | Action |
| Show me comedy movies | Comedy |
| Find science fiction movies | Science Fiction |
| I want to watch horror films | Horror |
| Tell me about Inception | None |

All tested cases passed.

**Year extraction:**

| Question | Expected result |
|---|---|
| Recommend action movies from 2020 | 2020 |
| Show comedy movies released in 2015 | 2015 |
| Find movies from 1999 | 1999 |
| Tell me about Inception | None |
| Recommend movies from 2024 | 2024 |

All tested cases passed.

### 5. Problem discovered: Movie title matching

During testing of `extract_title()`, two edge cases were identified.

**Problem A: Partial title matching**

Input:

"I want to watch The Lord of the Rings"

The parser returned `None`.

Investigation of the database showed that it contains three movies matching this phrase:
- The Lord of the Rings: The Fellowship of the Ring
- The Lord of the Rings: The Return of the King
- The Lord of the Rings: The Two Towers

The current implementation searches for complete movie titles. Therefore, it cannot recognise a shorter phrase that is shared by multiple longer movie titles.

**Problem B: False positive title matching**

Input:

"Recommend some good movies"

The parser returned:

`Good`

Investigation confirmed that the database contains a movie with the exact title Good.

The parser matched the word even though the user was using "good" as an adjective rather than referring to that movie.

This is a false positive: a technically valid text match that does not represent the user's actual intention.

### 6. Architectural learning

These cases revealed that checking whether a movie title appears in a question is not sufficient to determine whether the user intended to refer to that movie.

The parser needs to consider:
- Partial title matches.
- Multiple movies sharing a common phrase.
- Context in which a word is used.
- Ambiguous references that should not be resolved through arbitrary selection.

A parser should avoid confidently returning a movie when the user's intention is unclear.

### 7. Proposed improvement

**Decision proposed:** Improve title extraction to support multiple candidate matches instead of returning only the first matching title.

The proposed approach is:
1. Change `extract_title()` to `extract_titles()` and return a list of candidate titles.
2. Support matching shorter phrases against longer movie titles.
3. Improve contextual matching to reduce false positives caused by ordinary descriptive words.
4. Preserve multiple candidates when a phrase matches several movies.
5. Allow a later service/API layer to request clarification rather than silently selecting one movie.

**Status:** Items 1–4 implemented and tested (see Sections 10–12). Multiple matching titles are now passed through to the repository (see Section 15). Item 5 remains open: no clarification flow exists yet in the API for ambiguous references.

### 8. Performance consideration

The current implementation retrieves movie titles from SQLite whenever title extraction runs.

For the current dataset of approximately 4,803 movies, this is acceptable during initial development.

If title matching becomes a performance bottleneck, possible improvements include:
- Caching the movie title list.
- Using more targeted database queries.
- Introducing a dedicated search mechanism if the dataset grows significantly.

### 9. Current status

| Component | Status |
|---|---|
| Intent detection | Implemented and tested |
| Genre extraction | Implemented and tested |
| Year extraction | Implemented and tested |
| Basic title extraction | Implemented and tested |
| Partial title matching | Implemented for The Lord of the Rings; general-purpose solution still required |
| False-positive prevention | Implemented and tested |
| Combined query parsing | Implemented and tested |

Title-extraction improvements and the combined `parse_query()` entry point are complete. The movie service is connected to FastAPI via `POST /chat`, passes all extracted titles to the repository, and returns LLM-generated responses. Remaining work includes general partial-title matching and ambiguous-title clarification in the API.

### 10. Movie Title Extraction Improvements

**Problem identified:** The initial title extraction implementation only supported complete database titles and could incorrectly identify ordinary words as movie titles.

The following improvements were implemented:

**A. Multiple title candidates**

Changed `extract_title()` to `extract_titles()`.

- The function now returns a list of matching movie titles.
- This allows the application to preserve multiple candidates rather than returning only the first match.

**B. Multi-word title matching**

- Multi-word titles are checked before single-word titles.
- Longer matching titles take priority over shorter overlapping titles.
- This prevents `The Dark Knight` from being returned alongside `The Dark Knight Rises`.

**C. Single-word title matching**

- Single-word titles require nearby movie-related context.
- This prevents the word `Good` from being identified as a movie in "Recommend some good movies".
- Word tokenisation uses regular expressions to remove punctuation before matching.
- This allows `Avatar` to be recognised in "Who is in Avatar?".

**D. Instruction phrase handling**

- Common instruction phrases such as `Show Me` are excluded when they appear as command prefixes.
- This prevents the parser from treating the instruction "Show me" as a movie title.

**E. Partial title matching**

A targeted rule was added for `The Lord of the Rings`.

When the user mentions this shared phrase, the parser returns all three matching database titles:

- The Lord of the Rings: The Fellowship of the Ring
- The Lord of the Rings: The Return of the King
- The Lord of the Rings: The Two Towers

This is currently a dataset-specific rule, not a general partial-title matching solution.

### 11. Validation Results

The following test cases were executed using `scripts/test_query_parser.py`:

| User question | Extracted titles | Result |
|---|---|---|
| Tell me about Inception | Inception | Passed |
| Who is in Avatar? | Avatar | Passed |
| Show me The Dark Knight Rises | The Dark Knight Rises | Passed |
| I want to watch The Lord of the Rings | Three matching films | Passed |
| Recommend some good movies | Empty list | Passed |

The database was also queried independently to verify that the extracted Lord of the Rings titles exist exactly as stored.

**Current status:** All five tested title-extraction scenarios pass.

**Known limitation:** Partial title matching currently uses a hardcoded phrase for The Lord of the Rings. A general-purpose solution is still required for other movie franchises and ambiguous partial references.

### 12. Combined Query Parser

**Decision:** Introduce a single `parse_query()` function to combine the outputs of the individual query-parsing functions.

**Implementation:** Added `parse_query()` to `app/services/query_parser.py`.

The function calls:

- `detect_intent()` to identify the user's intention.
- `extract_genre()` to identify the requested genre.
- `extract_year()` to identify the requested release year.
- `extract_titles()` to identify movie-title references.

It returns a structured Python dictionary containing all four values.

**Example:**

Input:

`Recommend action movies from 2020`

Output:

```python
{
    "intent": "recommend",
    "genre": "Action",
    "year": 2020,
    "titles": []
}
```

**Reasoning:**

- Provides one entry point for query parsing.
- Keeps individual parsing responsibilities separate.
- Makes the output easier for the service layer to consume.
- Allows individual parsing functions to be tested independently.

**Validation:**

Created combined test cases in `scripts/test_query_parser.py`.

Five scenarios were tested, covering recommendations, movie details, genre filtering, year filtering and title extraction.

All five combined parsing test cases passed.

**Current status:** Implemented and tested.

**Known limitation:** The parser currently uses rule-based keyword matching. It does not yet understand every possible natural-language variation or resolve ambiguous movie references.

---

## 13. Movie Query Execution Service

### 1. Decision

Introduce `movie_service.py` to connect the query parser with the movie repository.

**File:** `app/services/movie_service.py`

### 2. Responsibility

The service acts as the coordination layer between query understanding and database retrieval.

It performs the following steps:

1. Receives the user's natural-language question.
2. Calls `parse_query()` to extract intent, genre, year and movie titles.
3. Converts the parsed information into repository parameters.
4. Calls `get_movies()` to retrieve matching records from SQLite.
5. Returns the parsed query and matching movies.

### 3. Implementation

Created `search_movies(question, db)`.

The service passes the complete extracted title list to the repository. If no title is found, it passes `None`.

**Update:** Multiple-title matching is documented in Section 15. Clarification for ambiguous references in the API remains open.

### 4. Validation

Created `scripts/test_movie_service.py` to test the complete flow.

Three scenarios were tested:

| User question | Expected behaviour | Result |
|---|---|---|
| Recommend action movies | Retrieve Action movies | Passed |
| Tell me about Inception | Retrieve Inception | Passed |
| Show me comedy movies from 2015 | Apply both genre and year filters | Passed |

The results confirmed that the service successfully connects the query parser, repository and SQLite database.

### 5. Current status

**Implemented, tested independently, and connected to FastAPI via `POST /chat`.**

See Section 14 for the chat endpoint integration details.

---

## 14. FastAPI Chat Endpoint Integration

### Decision

Connect the existing movie query service to FastAPI through a new `POST /chat` endpoint.

### Implementation

- Added a `ChatRequest` Pydantic model to validate incoming questions.
- Added `POST /chat` to `app/main.py`.
- Used the existing `get_db` dependency to provide a database session.
- Connected the endpoint to `search_movies()` from `movie_service.py`, imported as `process_movie_query` to avoid a naming conflict with the existing `/movies` endpoint function.
- Returned the original question, parsed query, and matching movie details as JSON.

### Validation

Successfully tested through Swagger UI (`/docs`):

1. **Genre-based recommendation:** `"Recommend action movies"` returned 10 Action movies, ordered by popularity.
2. **Specific movie lookup:** `"Tell me about Inception"` correctly identified the movie and returned its 2010 record and overview.

### Current Status

The `/chat` endpoint is implemented and successfully tested end-to-end.

**Update:** LLM response generation is integrated in `movie_service.py` and exposed through `POST /chat` (see Sections 21–22).

---

## 15. Multiple Movie Title Matching

### Problem Identified

During testing, the query parser correctly identified multiple movie titles for a question such as:

"Tell me about The Lord of the Rings"

However, the movie service originally selected only the first extracted title using `titles[0]`. This meant the remaining matching movies were ignored.

### Decision

Update the repository and movie service to support multiple movie titles in a single query.

### Implementation

1. Changed the repository parameter from `title: str | None` to `titles: list[str] | None`.
2. Used SQLAlchemy's `or_()` to construct title conditions, allowing any supplied title to match.
3. Updated `movie_service.py` to pass the complete extracted title list instead of selecting only the first title.
4. Preserved existing year filtering, genre filtering, popularity sorting and pagination.

### Validation

Successfully tested:

- Existing action movie recommendation.
- Specific movie lookup for Inception.
- Combined Comedy genre and 2015 year filtering.
- Multiple-title matching for The Lord of the Rings.

The standalone service test and the FastAPI `POST /chat` endpoint both returned all three Lord of the Rings movies.

### Current Status

Multiple-title matching is implemented and tested end-to-end.

---

## 16. Handling Unknown and Partial Movie Titles

### Problem Identified

During testing, the question:

"Tell me about Interstellar 2"

incorrectly returned the existing movie "Interstellar" (2014).

The title extraction logic matched known movie titles even when the user included additional numeric text after the title.

### Decision

Improve title extraction to avoid treating a known movie title as a valid match when it is immediately followed by a number.

### Implementation

- Added a validation check after a title match.
- Inspected the remaining question text after the matched title.
- If the next non-whitespace character is a digit, skipped that title match.
- Updated the movie service to return an empty movie list when the intent is `movie_details` but no title is identified.

### Validation

Tested the following scenarios:

| Question | Result |
|---|---|
| Tell me about Inception | Correct movie returned |
| Tell me about The Lord of the Rings | All three movies returned |
| Tell me about Interstellar 2 | No movies returned |
| Recommend action movies | Recommendations returned |
| Show me comedy movies from 2015 | Matching movies returned |

All existing regression tests passed after the change.

### Limitation

This is a rule-based validation improvement, not a complete solution for ambiguous or misspelled movie titles. More sophisticated title matching may be required in the future.

---

## 17. In-Memory Caching of Movie Titles

### Problem Identified

The `extract_titles()` function originally queried the database for all movie titles every time a user submitted a question.

```python
movie_titles = db.query(Movie.title).all()
titles = [movie[0] for movie in movie_titles]
```

Although this worked correctly, it caused an unnecessary database query on every request. The database contains 4,803 movie records, and the list of movie titles does not normally change between requests.

### Decision

**Decision:** Introduce an in-memory cache for movie titles.

Instead of querying SQLite repeatedly, load all movie titles the first time they are needed and store them in a module-level variable.

Subsequent calls reuse the cached list.

### Implementation

Added the following to `app/services/query_parser.py`:

- `_MOVIE_TITLES_CACHE`: stores the movie titles in memory.
- `get_movie_titles()`: checks whether the cache is empty.
- If the cache is empty, it retrieves all movie titles from SQLite and stores them.
- If the cache already contains titles, it returns the existing list without querying the database again.

The original database-query implementation has been retained as commented-out code for reference.

### Validation

Verified using `scripts/test_query_parser.py`.

| Test | Result |
|---|---|
| First cache call | 4,803 titles loaded |
| Second cache call | 4,803 titles returned |
| Object identity check | `True` |
| Existing parser regression tests | Passed |

The object identity check confirms that both calls return the same cached list rather than creating a new list.

### Benefits

- Avoids repeatedly querying SQLite for the same movie titles.
- Reduces unnecessary database access during title extraction.
- Keeps the existing title-matching logic unchanged.
- Simple to implement without introducing additional infrastructure.

### Trade-offs and Limitations

- The cache uses application memory.
- If movie titles are added, removed or updated in the database while the application is running, the cache will not automatically reflect those changes.
- Restarting the application clears the cache, allowing it to load the latest titles on the next request.
- In a multi-worker deployment, each worker maintains its own separate cache.

### Why This Approach?

For the current project, the movie dataset is relatively static and contains 4,803 records. An in-memory cache is a simple solution that avoids unnecessary database queries without introducing Redis or another external caching system.

If the application later requires frequent database updates or multiple instances sharing a consistent cache, a more advanced caching strategy can be considered.

---

## 18. Future Work and Deferred Improvements

This section records improvements that were considered during development but intentionally deferred to keep the initial implementation focused, manageable and aligned with the coding challenge requirements.

These are not forgotten features. They are potential improvements that can be revisited if time permits or if the application's requirements change.

### 18.1 Enhanced Natural Language Query Understanding

**Current status:** Deferred

The current query parser uses rule-based matching to identify:
- User intent (recommend, movie details, search).
- Movie genres.
- Release years.
- Movie titles.

**Potential improvements:**
- Movie comparison (e.g. "Compare Inception and Interstellar").
- Similar movie discovery (e.g. "Find movies similar to Avatar").
- Actor-based searches.
- Director-based searches.
- Better handling of ambiguous, misspelled and differently phrased movie titles.

**Reason for deferring:**

The existing parser supports the basic search and recommendation flows needed for the initial version. LLM integration is the next priority, and additional query capabilities can be added later.

### 18.2 Semantic Search and Vector Database

**Current status:** Deferred

**Potential improvement:**

Introduce embeddings and a vector database to support meaning-based movie searches.

For example, a user could ask:

"Suggest movies about people travelling through time."

The system could retrieve relevant movies based on plot meaning rather than relying only on exact keywords and structured filters.

**Reason for deferring:**

The current dataset and relational database support structured filtering and title-based searches. Introducing embeddings and a vector database would add infrastructure and complexity that are not necessary for the initial version.

### 18.3 Redis and Advanced Caching

**Current status:** Deferred

**Potential improvement:**

Introduce Redis for shared caching across multiple application instances, with configurable expiration and cache invalidation.

**Reason for deferring:**

An in-memory cache is sufficient for the current dataset and single-instance development setup. Redis would become more useful if the application needed distributed caching, multiple workers or more complex cache management.

### 18.4 Background Processing and Message Queues

**Current status:** Deferred

**Potential improvement:**

Introduce Kafka or another message queue for asynchronous tasks such as:
- Large dataset ingestion.
- Background recommendation processing.
- Updating embeddings and search indexes.
- Processing long-running AI requests.

**Reason for deferring:**

The current application handles requests synchronously, and the initial workload does not justify the operational complexity of a message queue.

### 18.5 Microservices Architecture

**Current status:** Deferred

**Potential improvement:**

Split the application into independently deployable services, such as:
- Movie catalogue service.
- Recommendation service.
- LLM service.
- User and ratings service.

**Reason for deferring:**

The current modular monolith provides clear separation of responsibilities while keeping development and deployment simple. Microservices would introduce additional complexity around service communication, deployment, monitoring and data consistency.

The LLM integration will initially remain a separate module within the existing application rather than becoming an independently deployed microservice.

### 18.6 Personalised Recommendations

**Current status:** Deferred

**Potential improvement:**

Use individual user preferences, watch history and ratings to generate personalised movie recommendations.

**Reason for deferring:**

The current implementation focuses on general movie discovery using the TMDB dataset. Personalisation would require additional user-related data, preference management and recommendation logic.

### 18.7 Cache Invalidation and Multi-Instance Support

**Current status:** Deferred

**Potential improvement:**

Improve the current in-memory movie title cache to support automatic refresh when the underlying database changes and consistent behaviour across multiple application workers.

**Reason for deferring:**

The current dataset is relatively static. Restarting the application refreshes the cache, which is sufficient for the initial implementation.

### 18.8 Performance Benchmarking

**Current status:** Deferred

**Potential improvement:**

Introduce performance measurements for:
- Database query execution.
- Movie title extraction.
- API response times.
- LLM response latency.
- Cache effectiveness.

**Reason for deferring:**

The current focus is functional correctness and completing the main application flow. Performance benchmarking can be added once the complete application is working.

### 18.9 Review and Revisit Strategy

These deferred improvements will be reviewed during final project evaluation.

If additional time is available, improvements will be prioritised based on their impact on functionality, maintainability and user experience.

The status of an item will be updated from **Deferred** to **In Progress** or **Completed** only when implementation actually begins or is verified.

The goal is to deliver a working, well-documented initial application before introducing additional infrastructure or advanced features.

---

## 19. LLM Technology Selection

### Requirement

The application needs a Large Language Model (LLM) to convert structured movie information retrieved from the database into natural, conversational responses.

The LLM should:
- Understand the context of retrieved movie information.
- Generate readable recommendations and explanations.
- Follow instructions about which information it can use.
- Avoid inventing movie details that are not present in the retrieved data.

### Decision 1: Use Ollama for Local LLM Execution

**Decision:** Use Ollama to run an open-source language model locally.

**Reasoning:**
- Avoids dependency on paid external LLM APIs.
- Allows local development without requiring an API key.
- Provides a straightforward interface for integration with Python.
- Keeps movie data and prompts within the local development environment.

### Decision 2: Select Qwen 2.5 7B

**Decision:** Use `qwen2.5:7b` as the initial language model.

**Reasoning:**
- Suitable for conversational responses and instruction following.
- Provides a reasonable balance between response quality and local resource requirements.
- Can run on the development machine, which has an Apple M2 chip and 16 GB unified memory.

### Validation

Successfully downloaded the model using:

```bash
ollama pull qwen2.5:7b
```

Tested it independently using:

```bash
ollama run qwen2.5:7b
```

Provided a prompt requesting three science-fiction movie recommendations with explanations.

**Result:** The model successfully generated a structured conversational response containing three recommendations and explanations.

### Architectural Decision: Ground LLM Responses in Database Results

The LLM will not be responsible for retrieving movie records directly.

The existing application will remain responsible for:
1. Parsing the user's question.
2. Retrieving matching movie records from SQLite.
3. Passing the retrieved information and user question to the LLM.
4. Returning the generated conversational response.

The database remains the source of truth for movie information. The LLM is responsible for generating natural-language responses using the supplied data.

#### Request flow before and after LLM integration

**Earlier flow:**

```text
Question → Parser → Repository → Database → JSON
```

**Flow after LLM integration:**

```text
Question → Parser → Repository → Database
                                  ↓
                            Retrieved movies
                                  ↓
                              Ollama
                                  ↓
                         Natural-language answer
```

### Implementation Plan

Create a dedicated `app/services/llm_service.py` module to handle communication with Ollama.

The existing `movie_service.py` will coordinate movie retrieval and LLM response generation.

This keeps database operations, query understanding and language generation separated into distinct responsibilities.

---

## 20. LLM Prompt Engineering and Factual Grounding

### 20.1 Objective

**Objective:** Ensure that the LLM generates useful, conversational movie responses using information retrieved from the SQLite database, without introducing unsupported movie details.

The application follows this principle:

- SQLite is the source of truth for movie information.
- The LLM is responsible for communicating and summarising the retrieved information.
- The LLM should not independently invent or assume movie details.

### 20.2 Initial Prompting Approach

**Initial decision:** Provide the LLM with movie records retrieved from SQLite and ask it to generate conversational movie recommendations.

The prompt initially included:
- User's original question.
- Movie title.
- Release year.
- Movie overview.
- Instructions not to invent movies or movie details.
- Instructions to explain when no matching movies are available.

**Initial observation:**

The LLM generated natural-language recommendations successfully. However, it added descriptions such as action sequences, space battles and other movie characteristics.

Although some of these details were factually correct, we needed to establish whether they were actually supported by the database records.

### 20.3 Prompt Refinement Experiments

#### Experiment 1: Basic Grounding Instructions

**Change:** Added instructions prohibiting the LLM from recommending movies or introducing details outside the supplied database records.

**Observation:**
- The LLM returned only movies retrieved from SQLite.
- However, it continued adding descriptive information based on its general knowledge.
- The generated descriptions were not necessarily supported by the supplied context.

**Conclusion:** Basic instructions were insufficient to consistently restrict the model's responses to database information.

#### Experiment 2: Stronger Restrictions

**Change:** Added stricter rules explicitly prohibiting:
- Use of general movie knowledge.
- Invented characters, actors, genres, scenes and awards.
- Unsupported plot details.
- Information not explicitly present in the supplied records.

Also instructed the LLM to preserve the order of the database results.

**Observation:**
- The LLM returned only the three movie titles and years.
- The database ordering was preserved.
- However, the response became too restrictive and conversational explanations disappeared.

**Conclusion:** Excessively restrictive instructions can reduce the usefulness of the LLM by making it behave like a database output formatter rather than a conversational assistant.

#### Experiment 3: Allowing Controlled Summarisation

**Change:** Allowed the LLM to rephrase and summarise movie overviews while explicitly prohibiting unsupported factual additions and interpretations.

**Observation:**
- The LLM generated more natural recommendations.
- However, it continued introducing additional descriptions, such as soundtrack details, action sequences and promotional claims.
- Some details were not explicitly present in the supplied overview.

**Conclusion:** Allowing unrestricted rephrasing and recommendation generation gave the model too much creative freedom.

#### Experiment 4: Restricting the Task to Summarisation

**Change:** Changed the task from generating promotional movie recommendations to summarising the database-provided movie overviews.

Additional instructions:
- Use the database as the only information source.
- Do not use pretrained movie knowledge.
- Do not add unsupported facts or interpretations.
- Limit each movie description to two sentences.
- Preserve database ordering.

**Observation:**
- The LLM returned descriptions closely aligned with the supplied database overviews.
- It preserved the order of the retrieved movies.
- It stopped adding obvious unsupported movie details.
- The response remained readable and useful.

**Conclusion:** Summarisation provided a better balance between natural-language generation and factual grounding than unrestricted recommendation generation.

### 20.4 Final Prompting Decision

**Decision:** Use a database-grounded summarisation prompt for the initial implementation.

The LLM receives:
1. The original user question.
2. The list of movies retrieved from SQLite.
3. Each movie's title, release year and overview.

The LLM is instructed to summarise the available information without introducing facts that are not supported by the supplied records.

The current implementation uses:
- Ollama for local LLM inference.
- Qwen 2.5 7B as the language model.
- Python `requests` to communicate with the Ollama API.
- A dedicated `generate_movie_response()` function in `app/services/llm_service.py`.

### 20.5 Testing and Validation

Tested the implementation using the question:

"Recommend three action movies."

The repository retrieved the following records:

1. Deadpool (2016)
2. Guardians of the Galaxy (2014)
3. Mad Max: Fury Road (2015)

**Final observed behaviour:**
- All three retrieved movies were included.
- The movie titles and release years were correct.
- The original database ordering was preserved.
- The generated descriptions closely followed the supplied database overviews.
- No obvious unsupported additions were observed in the final test output.

**Important limitation:**

Prompt instructions alone cannot guarantee that an LLM will never hallucinate. The final test demonstrates improved grounding for this particular test case, not a universal guarantee of factual accuracy.

### 20.6 Lessons Learned

1. A language model can introduce information from its pretrained knowledge even when database context is provided.
2. Stronger prompts do not always produce better user experiences. Excessive restrictions can eliminate useful natural-language explanations.
3. Summarisation is easier to constrain than open-ended recommendation generation.
4. The quality of the LLM response depends partly on the quality and completeness of the retrieved database information.
5. Prompt engineering should be validated through actual test cases rather than assuming that instructions will always be followed.
6. Keeping the database as the source of truth provides a clearer separation between data retrieval and natural-language generation.

### 20.7 Future Improvements

The following improvements are intentionally deferred until the initial LLM integration is complete:

**1. Automated Factual Grounding Tests**
- Create test cases containing known movie records and expected facts.
- Check whether generated descriptions contain unsupported names, events or claims.
- Test empty results, missing overviews and incomplete records.
- Evaluate responses across different question types.

**2. Structured LLM Output**
- Ask the LLM to return structured JSON instead of unrestricted text.
- Separate movie titles, release years and generated summaries.
- Validate the output using Pydantic before returning it through the API.
- Ensure the LLM cannot silently introduce movies that were not retrieved.

**3. Response Validation**
- Compare generated movie titles and years against the original database results.
- Reject or regenerate responses containing unknown movies.
- Consider validating individual factual claims against the supplied movie overviews.

**4. Improved Recommendation Logic**
- Use database information such as genres, ratings, popularity and vote counts to identify suitable movies.
- Keep movie selection within the repository/service layer rather than relying entirely on the LLM.
- Let the LLM explain why the retrieved movies match the user's request.

**5. Prompt Versioning and Evaluation**
- Maintain different prompt versions.
- Compare response quality, factual accuracy, consistency and latency.
- Build a repeatable evaluation dataset to identify regressions when prompts or models change.

**6. Model Evaluation**
- Compare Qwen 2.5 7B with other locally available models.
- Evaluate factual grounding, response quality, inference time and memory usage.
- Select a model based on measured results rather than model size alone.

**7. Token and Context Management**
- Limit the amount of overview text sent to the model.
- Introduce appropriate context limits for larger database result sets.
- Evaluate response latency and resource consumption.

These improvements will be considered as the application moves beyond its initial working implementation.

---

## 21. LLM Integration with Movie Query Service

### 21.1 Objective

**Decision:** Integrate the locally running Ollama LLM into the existing movie query service so that users receive natural-language responses instead of only structured database results.

The integration connects the previously implemented query parser, movie repository and LLM service.

### 21.2 Implementation

Updated `app/services/movie_service.py` to import:

`generate_movie_response()` from `app/services/llm_service.py`.

The `search_movies()` function now performs the following steps:

1. Receives the user's natural-language question.
2. Calls `parse_query()` to identify intent, genre, year and movie titles.
3. Calls the movie repository to retrieve matching database records.
4. Passes the original question and retrieved movie records to the LLM.
5. Returns the parsed query, matching movie objects and generated response.

### 21.3 Updated Service Response

The service now returns three fields:

- `parsed_query`: The structured output from the query parser.
- `movies`: The SQLAlchemy movie records retrieved from SQLite.
- `response`: The natural-language response generated by Ollama.

The original query parsing and database retrieval logic was retained.

### 21.4 Timeout Handling During Integration

**Issue encountered:** The first integrated service test failed with a `requests.exceptions.ReadTimeout` exception.

The Ollama API request exceeded the existing 120-second timeout.

**Resolution:** Increased the HTTP request timeout in `app/services/llm_service.py` from 120 seconds to 300 seconds.

**Result:** The integrated test completed successfully after increasing the timeout.

This allows longer-running local inference requests but does not guarantee that every request will complete within five minutes.

### 21.5 Integration Testing

Tested the integrated service using five different questions.

| Test question | Expected behaviour | Result |
|---|---|---|
| Recommend action movies | Retrieve and describe action movies | Passed |
| Tell me about Inception | Retrieve and describe Inception | Passed |
| Show me comedy movies from 2015 | Apply genre and year filters | Passed |
| Tell me about The Lord of the Rings | Retrieve all three matching films | Passed |
| Tell me about Interstellar 2 | Return no matching movies | Passed |

**Test observations:**

- The service successfully retrieved matching movies from SQLite.
- Ollama generated descriptions based on the supplied movie overviews.
- Multiple movie results were handled successfully.
- Unknown movie requests produced an empty database result and a response indicating that no description was available.

### 21.6 Known Limitations and Future Improvements

1. **Response ordering:** The LLM does not consistently preserve the exact database result order. Proposed improvement documented in Section 24: generate per-movie summaries in Python iteration order.

2. **Empty-result messaging:** Completed in Section 23 — empty database results are now handled in Python with a consistent message, without calling the LLM.

3. **Response length:** Some movie descriptions reproduce most of the original overview. Future improvement: encourage concise summaries with configurable length limits.

4. **Timeout and error handling:** The current timeout is 300 seconds. Controlled logging and fallback messaging for Ollama failures are implemented in Section 25.

5. **Factual validation:** Prompt instructions cannot guarantee factual accuracy. Future improvement: validate generated content against retrieved database records.

6. **Performance:** Each question currently triggers a separate local LLM inference request. Future improvement: evaluate response latency, model loading and opportunities to reduce unnecessary inference.

These improvements remain deferred after the initial API integration (see Section 22).

---

## 22. LLM Response Integration with FastAPI Chat Endpoint

### Objective

Expose the natural-language response generated by the local Ollama LLM through the existing FastAPI `/chat` endpoint.

### Implementation

Updated `app/main.py` to include the LLM-generated response in the JSON returned by the `POST /chat` endpoint.

Added:

```python
"response": result["response"]
```

The endpoint now returns four key elements:

1. `question` – the original user question.
2. `parsed_query` – the intent, genre, year and movie titles identified by the query parser.
3. `movies` – matching movie records retrieved from the SQLite database.
4. `response` – the natural-language response generated by Ollama.

### Validation

Tested the updated endpoint through FastAPI Swagger UI (`/docs`).

**Test question:**

`Tell me about Inception`

**Verified results:**

- Intent correctly identified as `movie_details`.
- Movie title correctly identified as `Inception`.
- Correct database record retrieved (TMDB ID: 27205).
- Movie year correctly returned as 2010.
- Natural-language response successfully generated by Ollama using the database overview.

**Outcome:** Successful. The `/chat` endpoint now integrates query parsing, database retrieval and LLM-generated responses.

### Decision

Keep the database results and LLM-generated response together in the `/chat` API response. This provides both the structured information needed by applications and a readable answer for users.

### Future Improvement

Handle empty database results directly in Python instead of calling the LLM. This will provide a consistent message when no matching movies are found and avoid unnecessary LLM processing.

**Update:** Implemented in Section 23.

---

## 23. Handling Empty Movie Search Results

### Problem

During testing, the query `Tell me about Interstellar 2` returned no matching movie records from the database.

Previously, the application still called the Ollama LLM with an empty movie list. This resulted in inconsistent and unhelpful responses.

### Decision

Handle empty database results directly in Python instead of sending an empty result set to the LLM.

### Implementation

Updated `app/services/movie_service.py` to check whether the database returned any movies before calling the LLM.

```python
if not movies:
    response = "Sorry, no matching movies were found in the database."
else:
    response = generate_movie_response(question, movies)
```

### Validation

Tested using:

`Tell me about Interstellar 2`

**Observed results:**
- Query parser identified the `movie_details` intent.
- No movie titles were identified.
- Database returned zero matching movies.
- Python returned the predefined message.
- Ollama was not called.

**Outcome:** Successful. Empty search results are now handled consistently without unnecessary LLM processing.

### Benefits

- Faster responses when no movies match.
- Avoids unnecessary LLM calls.
- Consistent user-facing error messages.
- Keeps simple application logic in Python rather than relying on the LLM.

---

## 24. Preserving Movie Order in LLM Responses

### Problem

During testing with the query:

`Tell me about The Lord of the Rings`

The database returned three movies in a particular order, but the Ollama LLM rearranged their order in its generated response.

The existing prompt explicitly instructs the LLM to preserve the database record order. However, prompt instructions alone cannot guarantee this behaviour.

### Current Implementation

All matching movie records are currently combined into a single prompt and sent to Ollama through `generate_movie_response()`.

The LLM generates summaries for all movies in one response.

### Proposed Improvement

Move control of movie ordering from the LLM to Python.

Python would:
1. Iterate through the movies in the order returned by the database.
2. Send each movie's information to Ollama individually.
3. Generate a summary for each movie.
4. Append each summary to the final response in the original database order.

### Advantages

- Python guarantees that the original database order is preserved.
- Each LLM request contains information about only one movie.
- Easier to associate each generated summary with its corresponding movie.
- Reduces the possibility of the LLM mixing information between multiple movie records.

### Trade-offs

- Requires multiple Ollama API calls instead of one.
- Increases total response time.

---

## 25. Error Handling for Ollama Failures

### Problem

The application depends on the locally hosted Ollama service to generate natural-language movie responses.

If Ollama is unavailable, the request fails, or the model encounters an error, the `/chat` endpoint could fail instead of returning a useful response.

### Decision

Implement error handling in `app/services/movie_service.py` so that Ollama failures do not prevent the application from returning database results.

### Implementation

Added Python logging and a `try/except` block around the LLM response generation.

```python
try:
    response = generate_movie_response(question, movies)

except Exception:
    logger.exception("Failed to generate movie response using Ollama.")
    response = (
        "The matching movies were found, but the AI response "
        "could not be generated. Please try again later."
    )
```

The exception is logged for debugging, while the user receives a predefined fallback message.

### Validation

Tested three scenarios:

**1. Ollama available**
- Movie details retrieved successfully.
- LLM generated a natural-language response.

**2. Ollama unavailable**
- Stopped the local Ollama service.
- Matching movies were still retrieved from SQLite.
- The exception was logged.
- The API returned HTTP 200 with the predefined fallback message instead of failing.

**3. Empty movie results**
- No matching movies found.
- The predefined empty-result message was returned.
- Ollama was not called.

**Outcome:** Successful. Database retrieval continues to work even when Ollama fails, and users receive a clear fallback message.

### Benefits

- Prevents `/chat` from failing when Ollama is unavailable.
- Preserves structured movie results for the caller.
- Logs the underlying exception for debugging.
- Separates AI generation failures from database query failures.

**Update:** The broad `except Exception` handler was later narrowed to `requests.exceptions.RequestException` in Section 26.

---

## 26. Narrowing Ollama Exception Handling

### Decision

Replace the broad `except Exception` handler with `except requests.exceptions.RequestException` in `movie_service.py`.

### Reason

The broad exception handler could hide unrelated programming errors. The narrower handler catches errors related to HTTP requests to Ollama, including:

- Connection errors when Ollama is unavailable.
- Request timeouts.
- HTTP errors returned by the Ollama API.

This makes error handling more specific while allowing unrelated programming errors to surface.

### Validation

Tested the updated implementation in two scenarios:

1. **Ollama running:** All five movie-service test cases completed successfully.
2. **Ollama stopped:** The application logged the connection error and returned a fallback response while preserving the database movie results.

The no-results scenario also continued to work without calling Ollama.

### Outcome

The application can continue serving database results even when the local LLM service is unavailable. Technical errors are logged for debugging, while users receive a clear fallback message.
