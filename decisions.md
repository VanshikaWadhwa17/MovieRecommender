# Technical Decisions

## 1. Dataset Selection

I chose the **TMDB 5000 Movies dataset** rather than MovieLens.

The dataset contains 4,803 movies and a corresponding credits file. It provides the information needed for a conversational movie assistant, including titles, release dates, genres, overviews, ratings, cast members and directors.

MovieLens offers a larger collection of ratings, but requires additional data mapping to obtain movie descriptions and credits. TMDB was a better fit for the scope of this proof of concept because it provides richer movie metadata in a relatively straightforward format.

**Trade-off:** The dataset is static and does not include current releases beyond its coverage period. A production application would need an up-to-date data source.

## 2. Database Design

I chose **SQLite with SQLAlchemy** for data storage and database access.

SQLite keeps the project lightweight and easy to run locally without requiring a separate database server. SQLAlchemy provides an ORM layer, making database operations easier to maintain and allowing the application logic to remain less dependent on raw SQL.

The database uses seven tables:

| Table | Purpose |
|---|---|
| `movies` | Core movie information |
| `genres` | Unique genre records |
| `movie_genres` | Many-to-many relationship between movies and genres |
| `ratings` | Movie ratings and vote counts |
| `people` | Shared cast and director records |
| `movie_cast` | Cast members and their characters |
| `movie_directors` | Movie-to-director relationships |

I separated genres, ratings and people from the main movie records to reduce duplication and represent relationships more clearly.

**Trade-off:** SQLite is sufficient for this local proof of concept, but a production system with concurrent users and higher write workloads would benefit from a database such as PostgreSQL.

## 3. Technology Choices

| Technology | Purpose |
|---|---|
| Python | Main application language |
| FastAPI | REST API framework |
| SQLAlchemy | Database ORM |
| SQLite | Relational data storage |
| pandas | Loading and processing CSV datasets |
| Ollama | Running a local language model |
| Qwen2.5:7b | Generating conversational responses |
| pytest | Automated testing |

I selected FastAPI because it provides a straightforward way to build REST endpoints, request validation and automatically generated API documentation.

I used Ollama with Qwen2.5:7b to run the language model locally rather than relying on a paid external LLM API.

**Trade-off:** Local inference avoids an external API dependency, but requires the model to be installed and sufficient local computing resources to run it.

## 4. Application Architecture

I used a modular, layered structure to separate responsibilities:

- **API layer:** Defines FastAPI endpoints and handles HTTP requests.
- **Schema layer:** Defines request and response structures using Pydantic.
- **Service layer:** Coordinates query parsing, database retrieval and response generation.
- **Repository layer:** Handles database queries.
- **Database layer:** Defines SQLAlchemy models, database configuration and session management.

The main `/chat` workflow is:

1. Receive the user's natural-language question.
2. Parse the question to identify the intent and relevant filters.
3. Retrieve matching movie records from SQLite.
4. Pass the retrieved records to the LLM for conversational response generation.
5. Return the parsed query, matching database records and generated response.

Keeping retrieval separate from response generation helps ensure that movie information comes from the structured dataset rather than being invented by the language model.

## 5. Query Processing

I implemented a lightweight, rule-based query parser rather than introducing a separate NLP framework.

It identifies three main intents:

- `search`: Find movies matching criteria such as genre or year.
- `movie_details`: Retrieve information about a particular movie.
- `recommend`: Return movie recommendations.

The parser also extracts relevant information such as genres, years and movie titles.

I chose this approach because the project is a proof of concept with a defined dataset and a limited set of supported query types. It is easier to understand, test and explain than introducing a more complex semantic parsing pipeline.

An in-memory cache stores movie titles after the first database lookup, reducing repeated title-list retrieval during the application's runtime.

**Trade-off:** Rule-based parsing is predictable and lightweight, but it has limitations with spelling mistakes, ambiguous titles and more complex natural-language questions. A future version could use an NLP model or LLM-based intent extraction.

## 6. LLM Integration and Grounding

I use the LLM for conversational response generation, not as the source of movie facts.

The application first retrieves relevant records from SQLite and then supplies those records as context to Qwen2.5:7b. The prompt instructs the model to base its response on the supplied data.

This separation is important because language models can generate plausible but inaccurate information.

For recommendations, the application performs the selection and ranking in Python. It filters out movies with fewer than 100 votes and sorts the remaining results by:

1. Rating, descending
2. Vote count, descending
3. Popularity, descending

Python constructs the recommendation list, while the LLM generates the conversational introduction. This keeps the recommendation results deterministic rather than relying on the model to select or reorder records.

If no matching movies are found, the application returns an appropriate response without making an unnecessary LLM request. If Ollama is unavailable or a request fails, the application can fall back to a non-LLM response while retaining the retrieved database results.

**Trade-off:** This approach improves factual grounding and reliability, but the quality of the generated explanation still depends on the model and the context supplied to it.

## 7. Key Design Trade-offs

| Decision | Reason | Limitation |
|---|---|---|
| TMDB 5000 | Rich movie metadata and credits | Static dataset |
| SQLite | Simple local setup | Limited scalability |
| Rule-based parser | Lightweight and testable | Limited language flexibility |
| Local Ollama model | No paid external LLM API required | Requires local resources |
| Structured retrieval before LLM generation | Keeps responses grounded in database records | Depends on retrieval quality |
| Deterministic recommendation ranking | Consistent and explainable results | Uses a fixed ranking strategy |

## 8. Future Improvements

If I were to extend the project beyond the proof of concept, I would consider:

- Improving title matching to handle spelling mistakes and ambiguous queries.
- Introducing semantic search or embeddings for more flexible natural-language retrieval.
- Adding user preferences and personalised recommendations.
- Replacing the static dataset with an up-to-date movie data source.
- Adding pagination, more advanced filtering and database optimisation.
- Evaluating LLM response quality and factual consistency across a larger set of queries.
- Moving to PostgreSQL and deploying the application for multi-user access.

The current implementation focuses on demonstrating the complete flow: structured data ingestion, relational storage, natural-language query processing, database retrieval and LLM-powered response generation.
