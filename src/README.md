# Source Modules

This directory contains the core logic for the digital-footprint-dump pipeline.

## Project Structure

Note: The file structure below is shown from the root directory.

```
├── main.py                 # CLI entry point (25 subcommands)
├── src/
│   ├── config.py           # Environment configuration & validation
│   ├── database.py         # Base SQLite connection manager
│   ├── comparison.py       # Generic MoM/YoY comparison utilities
│   ├── readwise/           # Readwise Reader integration (API)
│   ├── foursquare/         # Foursquare/Swarm integration (API)
│   ├── letterboxd/         # Letterboxd CSV import (file)
│   ├── overcast/           # Overcast OPML import (file)
│   ├── strong/             # Strong workout CSV import (file)
│   ├── hardcover/          # Hardcover book API integration (API)
│   ├── github/             # GitHub commit activity tracking (API)
│   └── publish/            # Markdown + data file generation & GitHub publishing
├── data/                   # SQLite databases (generated)
├── files/                  # Import files (user-provided)
├── tests/                  # Test suite (13 test files)
└── .github/workflows/      # CI/CD (tests.yml, monthly-pipeline.yml)
```

## Module Pattern

Each data source follows a consistent structure:

| File | Purpose |
|------|---------| 
| `models.py` | SQL schema definitions (CREATE TABLE statements) |
| `database.py` | Database manager (inherits from `BaseDatabase`) with CRUD |
| `api_client.py` | API wrapper (API sources only) |
| `sync.py` | Sync orchestration (API sources only) |
| `importer.py` | File parser (file-based sources only) |
| `analytics.py` | Monthly analysis logic → writes to `analysis` table |

### Source Types

| Type | Sources | Data Ingestion |
|------|---------|----------------|
| **API** | Readwise, Foursquare, Hardcover, GitHub | `api_client.py` + `sync.py` |
| **File** | Letterboxd, Overcast, Strong | `importer.py` (reads from `files/`) |

### Publish Module

| File | Description |
|------|-------------|
| `publisher.py` | Orchestrates analysis fetching, comparison computation, and publishing |
| `markdown_generator.py` | Hugo-compatible markdown generation (sections: Reading, Travel, Movies, Podcasts) |
| `data_generator.py` | Generates Hugo data files (`data/activity/*.yaml`) from analysis tables |
| `github_client.py` | GitHub API wrapper for multi-file atomic commits via Git tree API |

## Database Schemas

Each source stores data in a separate SQLite database under `data/`.

### Analysis Tables

Every source has an `analysis` table with this common structure:
- `year_month` (TEXT, PRIMARY KEY) — Format: `YYYY-MM`
- `year` (TEXT), `month` (TEXT)
- Source-specific metrics (see below)
- `updated_at` (TEXT) — ISO timestamp

### Per-Source Schemas

#### Readwise (`readwise.db`)

**Data tables:** `books`, `highlights`, `highlight_tags`, `book_tags`, `documents`, `document_tags`, `sync_state`

| Analysis Column | Type |
|-----------------|------|
| `articles` | INTEGER |
| `words` | INTEGER |
| `reading_time_mins` | INTEGER |
| `max_words_per_article` | INTEGER |
| `median_words_per_article` | INTEGER |
| `min_words_per_article` | INTEGER |

#### Foursquare (`foursquare.db`)

**Data tables:** `users`, `places`, `checkins`, `sync_state`
**Views:** `checkins_with_places`, `user_stats`

| Analysis Column | Type |
|-----------------|------|
| `checkins` | INTEGER |
| `unique_places` | INTEGER |

#### Letterboxd (`letterboxd.db`)

**Data tables:** `users`, `watched`, `ratings`

| Analysis Column | Type |
|-----------------|------|
| `movies_watched` | REAL |
| `avg_rating` | REAL |
| `min_rating` | REAL |
| `max_rating` | REAL |
| `avg_years_since_release` | REAL |

#### Overcast (`overcast.db`)

**Data tables:** Created externally by `overcast-to-sqlite` (`feeds`, `episodes`, `playlists`)

| Analysis Column | Type |
|-----------------|------|
| `feeds_added` | INTEGER |
| `feeds_removed` | INTEGER |
| `episodes_played` | INTEGER |

#### Strong (`strong.db`)

**Data tables:** `workouts`, `exercises`

| Analysis Column | Type |
|-----------------|------|
| `workouts` | INTEGER |
| `total_minutes` | INTEGER |
| `unique_exercises` | INTEGER |
| `total_sets` | INTEGER |

#### Hardcover (`hardcover.db`)

**Data tables:** `books`

| Analysis Column | Type |
|-----------------|------|
| `books_finished` | INTEGER |
| `avg_rating` | REAL |

#### GitHub (`github.db`)

**Data tables:** `commits`

| Analysis Column | Type |
|-----------------|------|
| `commits` | INTEGER |
| `repos_touched` | INTEGER |

## Key Concepts

### MoM/YoY Comparisons

All sources display month-over-month and year-over-year percentage changes in their output.

| Source | Metrics with MoM/YoY |
|--------|---------------------|
| Readwise | articles, words, reading_time_mins, avg_speed (derived) |
| Foursquare | checkins, unique_places |
| Letterboxd | movies_watched, avg_rating |
| Overcast | episodes_played |
| Strong | workouts, total_minutes |
| Hardcover | books_finished, avg_rating |
| GitHub | commits, repos_touched |

The `comparison.py` module provides shared utilities:

```python
from src.comparison import compute_comparisons, format_comparison_suffix

# In publisher.py — compute comparisons
comparisons = compute_comparisons(
    current_stats=data,
    historical_getter=self._get_source_analysis,
    year_month="2026-02",
    metrics=['checkins', 'unique_places']
)

# In markdown_generator.py — format suffix
suffix = format_comparison_suffix(comparisons.get('checkins'))  # " (-46% MoM, +367% YoY)"
```

**Key functions:**
- `compute_percentage_change(current, previous)` → percentage or None
- `get_comparison_periods(year_month)` → `{'mom': '2026-01', 'yoy': '2025-02'}`
- `format_change(value)` → `"+15%"`, `"-10%"`, or `"N/A"`
- `format_comparison_suffix(changes)` → `" (+15% MoM, -5% YoY)"` or `""`
- `format_value_with_changes(value, changes, value_format)` → `"42 (+15% MoM, -5% YoY)"`
- `compute_comparisons(...)` → dict of metrics with MoM/YoY values

**Derived metrics:** Readwise average reading speed is derived from words/time in `_compute_speed_comparison()`.

### Hugo Data Files

The `publish/data_generator.py` module generates Hugo-compatible YAML data files from all analysis tables. These are committed to `data/activity/` in the blog repo via the `backfill` command:

| File | Source | Fields |
|------|--------|--------|
| `reading.yaml` | Readwise | `articles_archived`, `total_words`, `time_spent_minutes`, `avg_reading_speed`, `max_words_per_article`, `median_words_per_article`, `min_words_per_article` |
| `travel.yaml` | Foursquare | `checkins`, `unique_places` |
| `movies.yaml` | Letterboxd | `movies_watched`, `avg_rating` |
| `podcasts.yaml` | Overcast | `feeds_added`, `feeds_removed`, `episodes_played` |
| `workouts.yaml` | Strong | `workouts`, `total_minutes`, `unique_exercises`, `total_sets` |
| `books.yaml` | Hardcover | `books_finished`, `avg_rating` |
| `code.yaml` | GitHub | `commits`, `repos_touched` |

### Database Connections

All database managers inherit from `src/database.py:BaseDatabase` and use a context manager pattern:

```python
with self.db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    rows = cursor.fetchall()
    # rows are sqlite3.Row objects — access like dicts: row['column']
```

### Configuration

`src/config.py` loads environment variables from `.env` and provides validation methods:

| Config Section | Key Variables | Validation |
|----------------|---------------|------------|
| Readwise | `READWISE_ACCESS_TOKEN` | `validate_readwise()` |
| Foursquare | `FOURSQUARE_ACCESS_TOKEN` | `validate_foursquare()` |
| Hardcover | `HARDCOVER_ACCESS_TOKEN` | `validate_hardcover()` |
| GitHub Activity | `CODEBASE_USERNAME`, `BLOG_GITHUB_TOKEN` | `validate_github_activity()` |
| GitHub Publishing | `BLOG_GITHUB_TOKEN`, `BLOG_REPO_OWNER`, `BLOG_REPO_NAME` | `validate_github()` |

File-based sources (Letterboxd, Overcast, Strong) require no API tokens — they read from `files/`.

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_comparison.py -v
```

Test files cover: comparison utilities, data generator, cloud config, Foursquare client + security, GitHub client + sync, Hardcover sync/timeout, main refactor, Overcast importer security, Readwise client security + database.
