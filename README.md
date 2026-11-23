# Movie Recommender

Conversational AI movie assistant that answers movie-related questions using structured database retrieval and LLM-powered response generation.

Primary data source: **TMDB 5000 Movies** (see [decisions.md](decisions.md) for why).

---

## Project layout

```
MovieRecommender/
├── data/tmdb/
│   ├── movies.csv      # TMDB movie metadata
│   └── credits.csv     # Cast and crew
├── scripts/
│   └── inspect_data.py # Quick dataset inspection
├── decisions.md        # Architectural / product decisions log
├── requirements.txt
└── README.md
```

---

## Setup

Run these from the **project root**.

### 1. Create / activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

**Used for:** installing Python packages needed to load and inspect the TMDB CSVs (currently `pandas`).

### 3. Confirm data is present

Expected paths:

- `data/tmdb/movies.csv`
- `data/tmdb/credits.csv`

If these files are missing, place the TMDB 5000 `movies.csv` and `credits.csv` under `data/tmdb/` before running any scripts.

---

## How to run (current flow)

At this stage the project only has data inspection. End-to-end app run steps will be added here as features land.

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `pip install -r requirements.txt` | Install project dependencies |
| 2 | `python scripts/inspect_data.py` | Load both TMDB CSVs and print record counts, column names, and the first 2 rows of each |

### Inspect the datasets

```bash
python scripts/inspect_data.py
```

**Used for:** verifying that the TMDB files load correctly from the project root and understanding schema / sample content before building ingestion or query layers.

**When to run:** after placing the CSVs, after changing data paths, or whenever you want a quick sanity check of the raw data.

---

## Dataset snapshot (from `inspect_data.py`)

### Movies

- **Rows:** 4,803
- **Columns include:** `title`, `overview`, `genres`, `release_date`, `vote_average`, `vote_count`, `popularity`, and others (`budget`, `homepage`, `id`, `keywords`, `original_language`, `original_title`, `production_companies`, `production_countries`, `revenue`, `runtime`, `spoken_languages`, `status`, `tagline`)

### Credits

- **Rows:** 4,803
- **Columns:** `movie_id`, `title`, `cast`, `crew`

### Notes

- First rows look like Avatar and similar TMDB entries.
- `genres`, `cast`, and `crew` (and several other fields) store **nested JSON** as strings in the CSV — these need parsing before structured querying.

---

## Decision log

Architectural choices (dataset selection, trade-offs, FAQs) are tracked in [decisions.md](decisions.md).
