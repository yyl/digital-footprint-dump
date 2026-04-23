# Source Modules

This directory contains the core logic for the digital-footprint-dump pipeline.

## Project Structure

Note: The file structure below is shown from the root directory.

```
├── main.py                 # CLI entry point
├── src/
│   ├── config.py           # Environment configuration & validation
│   ├── database.py         # Base SQLite connection manager
│   ├── comparison.py       # Generic MoM/YoY comparison utilities
│   ├── readwise/           # Readwise Reader integration (API)
│   ├── foursquare/         # Foursquare/Swarm integration (API)
│   ├── letterboxd/         # RSS feed sync + CSV import fallback
│   ├── overcast/           # Overcast OPML import (file)
│   ├── strong/             # Strong workout CSV import (file)
│   ├── apple_health/       # Apple Health XML import (file)
│   ├── blog/               # Public Hugo posts JSON tracking (API)
│   ├── hardcover/          # Hardcover book API integration (API)
│   ├── github/             # GitHub commit activity tracking (API)
│   └── publish/            # Markdown + data file generation & GitHub publishing
├── data/                   # SQLite databases (generated)
├── files/                  # Import files (user-provided)
├── tests/                  # Test suite (13 test files)
└── .github/workflows/      # CI/CD (tests.yml, monthly-pipeline.yml)
```

## Data Source / Storage Resolution

This project reads and writes source databases and import files from a storage root. The app resolves `data/` and `files/` from a storage root rather than always using this repo directly.

- Local runs default to the sibling repo `../digital-footprint-data` when it exists.
- Otherwise, local runs fall back to this repo's own `data/` and `files/` directories.
- GitHub Actions checks out the private data repo separately and links its `data/` and `files/` into the workspace.
- You can explicitly override the local storage root with `DATA_REPO_LOCAL_PATH`.

In practice this means:

- SQLite databases live under `<storage-root>/data/`.
- File imports live under `<storage-root>/files/`.
- API-backed sources write their SQLite databases under `<storage-root>/data/`.
- File-backed sources read imports from `<storage-root>/files/` and write their databases under `<storage-root>/data/`.

## Local/CI Consistency

The repo pins Python in `.python-version`, and both GitHub Actions workflows use that exact version.

For container-based local development, this repo's `.devcontainer/devcontainer.json` points at the shared `yyl/dev-tools:latest` image from the sibling `../dev-tools` folder, while keeping repo-specific VS Code settings, extensions, and the `uv sync` post-create step local to this repo.

For a CI-like local test run, use:

```bash
make test-ci
```

That command:

- installs the pinned Python version with `uv`
- syncs dependencies against that version
- runs `pytest` with the same pinned interpreter

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

Sync/import initialization creates raw source tables only. Each source's `analytics.py` is responsible for creating its own derived `analysis` table.

### Source Types

| Type | Sources | Data Ingestion |
|------|---------|----------------|
| **API** | Readwise, Foursquare, Blog, Hardcover, GitHub | `api_client.py` + `sync.py` |
| **File** | Letterboxd, Overcast, Strong, Apple Health | `importer.py` (reads from `files/`) |

### Publish Module

| File | Description |
|------|-------------|
| `publisher.py` | Orchestrates analysis fetching, comparison computation, report assembly, and publishing |
| `markdown_generator.py` | Hugo-compatible markdown generation for the monthly draft report (sections: Reading, Travel, Movies, Podcasts, Workout, Writing, Books, Code) |
| `data_generator.py` | Generates Hugo data files (`data/activity/*.yaml`) from analysis tables |
| `github_client.py` | PyGithub-based wrapper for multi-file atomic commits via the Git tree API, with retry handling for non-fast-forward ref updates |

### Publish Flow

The `publish` command supports several flags to customize its execution path:

- `publish`: syncs all sources, reruns analysis, generates the latest monthly report, and commits a draft blog post.
- `publish --skip-sync-analysis`: skips both sync and analysis, and publishes directly from the current analysis data in the local databases.
- `publish --dry-run`: skips sync and publish, and only renders markdown from the current analysis data already present in the local databases.
- `publish --last-month`: generates and publishes the report for the previous month instead of the latest available month.
- `backfill`: runs the analyze commands for Readwise, Letterboxd, Foursquare, Overcast, Strong, Apple Health, Blog, Hardcover, and GitHub, then commits regenerated Hugo data files under `data/activity/`. Each analyze command refreshes its raw source data first via its paired sync step.

Published workout metrics now come from Apple Health monthly analysis. Strong remains importable and analyzable directly, but its exercise/set metrics are no longer used in the report or `workouts.yaml`.

Published writing metrics now come from the public Hugo posts JSON export. The report renders a `Writing` section, and backfill writes `writing.yaml`.

When selecting the reporting month, `publisher.py` now scans all available analysis databases and picks the latest (or second-latest if `--last-month` is provided) `YYYY-MM` it can find, while tolerating optional sources that are absent or not initialized yet.

See [docs/SUMMARY.md](../docs/SUMMARY.md) for full details on the generated report format and content.

### Publish Implementation Details

- GitHub publishing uses PyGithub for authenticated write operations.
- If the target branch moves during publish, the GitHub client automatically retries non-fast-forward ref update failures.
- GitHub activity sync uses an inclusive timestamp cursor plus SHA de-duplication so same-second commits are not skipped during incremental sync.

## Database Schemas

Each source stores data in a separate SQLite database under `<storage-root>/data/`.

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

*Technical Note (Letterboxd Hybrid Syncing): Letterboxd uses a hybrid integration architecture. It fetches incremental updates via the public RSS feed (`LETTERBOXD_RSS_URL`), but automatically falls back to manual CSV directory parsing (`files/letterboxd-*`) if the database is entirely empty (for historical backfill seeding) or if the RSS config is absent. Because the CSV export and RSS feed use varying canonical ID formats (short URLs vs canonical slugs) and boundary timezone definitions for dates, the importer automatically deduplicates overlapping movie watches across these two ingestion methods by checking if the movie name matches any existing watch record within a +/- 2 day window.*

#### Overcast (`overcast.db`)

**Data tables:** Created externally by `overcast-to-sqlite` (`feeds`, `episodes`, `playlists`)

| Analysis Column | Type |
|-----------------|------|
| `feeds_added` | INTEGER |
| `feeds_removed` | INTEGER |
| `episodes_played` | INTEGER |
| `minutes_listened` | INTEGER |

*Note: The `overcast-sync` command automatically fetches missing episode durations from live RSS feeds using title-matching, which populates the `duration_seconds` column in `episodes` and enables the `minutes_listened` analysis.*

#### Strong (`strong.db`)

**Data tables:** `workouts`, `exercises`

| Analysis Column | Type |
|-----------------|------|
| `workouts` | INTEGER |
| `total_duration_seconds` | INTEGER |
| `unique_exercises` | INTEGER |
| `total_sets` | INTEGER |

#### Apple Health (`apple_health.db`)

**Data tables:** `workouts`

| Analysis Column | Type |
|-----------------|------|
| `workouts` | INTEGER |
| `total_duration_seconds` | INTEGER |
| `total_calories` | REAL |

#### Blog (`blog.db`)

**Data tables:** `posts`, `post_tags`

| Analysis Column | Type |
|-----------------|------|
| `posts` | INTEGER |
| `total_words` | INTEGER |
| `unique_tags` | INTEGER |

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
| Apple Health | workouts, total_duration_seconds, total_calories |
| Blog | posts, total_words, unique_tags |
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

The `publish/data_generator.py` module generates Hugo-compatible YAML data files from all analysis tables. `backfill` first refreshes source analysis tables by running the per-source analyze commands (which themselves invoke sync first), then commits the resulting files to `data/activity/` in the blog repo.

| File | Source | Fields |
|------|--------|--------|
| `reading.yaml` | Readwise | `articles_archived`, `total_words`, `time_spent_minutes`, `avg_reading_speed`, `max_words_per_article`, `median_words_per_article`, `min_words_per_article` |
| `travel.yaml` | Foursquare | `checkins`, `unique_places` |
| `movies.yaml` | Letterboxd | `movies_watched`, `avg_rating` |
| `podcasts.yaml` | Overcast | `feeds_added`, `feeds_removed`, `episodes_played`, `minutes_listened` |
| `workouts.yaml` | Apple Health | `workouts`, `total_minutes` (derived from analysis seconds), `total_calories` |
| `writing.yaml` | Blog | `posts`, `total_words`, `unique_tags` |
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

### Timestamp Helpers

Timezone-aware UTC timestamps are generated via `src/time_utils.py:utc_now_iso()`, which returns ISO 8601 strings ending in `Z`. This avoids the Python 3.12 `datetime.utcnow()` deprecation warnings while keeping the stored format unchanged.

### Configuration

`src/config.py` loads environment variables from `.env` and provides validation methods:

| Config Section | Key Variables | Validation |
|----------------|---------------|------------|
| Readwise | `READWISE_ACCESS_TOKEN` | `validate_readwise()` |
| Foursquare | `FOURSQUARE_ACCESS_TOKEN` | `validate_foursquare()` |
| Hardcover | `HARDCOVER_ACCESS_TOKEN` | `validate_hardcover()` |
| GitHub Activity | `CODEBASE_USERNAME`, `BLOG_GITHUB_TOKEN` | `validate_github_activity()` |
| GitHub Publishing | `BLOG_GITHUB_TOKEN`, `BLOG_REPO_OWNER`, `BLOG_REPO_NAME` | `validate_github()` |

File-based sources (Letterboxd, Overcast, Strong, Apple Health) require no API tokens — they read from `<storage-root>/files/`. Blog tracking also requires no token by default and reads from the public `BLOG_POSTS_INDEX_URL`.

## Testing

```bash
# Run all tests
uv run pytest

# Run the CI-like local test flow
make test-ci

# Run specific test file
uv run pytest tests/test_comparison.py -v
```

Test files cover: comparison utilities, data generator, cloud config, Foursquare client + security, GitHub client + sync, Hardcover sync/timeout, main refactor, Overcast importer security, Readwise client security + database.

## Cloud Deployment (GitHub Actions)

Automate the pipeline to run monthly using GitHub Actions with a private data repository.

### Setup

1. **Create a private data repository** (e.g., `digital-footprint-data`):
   ```
   digital-footprint-data/
   ├── data/           # Empty initially, DBs auto-created
   └── files/          # Manual exports (Letterboxd, Strong, Apple Health, optional Overcast fallback)
       ├── letterboxd-export/
       ├── strong_workouts.csv
       └── export.xml
   ```

   If you configure direct Overcast export auth in Actions secrets, the workflow does not need a checked-in `overcast.opml`. You can still keep `files/overcast*.opml` as a fallback.

2. **Create two fine-grained Personal Access Tokens** at [github.com/settings/tokens](https://github.com/settings/tokens):

   | Token | Repo scope | Permissions needed |
   |-------|-----------|--------------------|
   | `DATA_REPO_PAT` | Private data repo | **Contents: Read and write** |
   | `BLOG_GITHUB_TOKEN` | Blog repo | **Contents: Read and write** |

   > These can be the same token if it has access to both repos.

3. **Add secrets** to your public repo (Settings → Secrets → Actions):

   | Secret | Description |
   |--------|-------------|
   | `DATA_REPO_OWNER` | Your GitHub username |
   | `DATA_REPO_NAME` | Private data repo name |
   | `DATA_REPO_PAT` | PAT with Contents read/write on data repo |
   | `READWISE_ACCESS_TOKEN` | Readwise API token |
   | `FOURSQUARE_ACCESS_TOKEN` | Foursquare OAuth token — required for all API calls |
   | `FOURSQUARE_API_KEY` | *(optional)* Foursquare Places API for venue details |
   | `OVERCAST_COOKIE` | *(optional)* Overcast authenticated `o` cookie for direct OPML export |
   | `OVERCAST_EMAIL` | *(optional)* Overcast login email for direct OPML export |
   | `OVERCAST_PASSWORD` | *(optional)* Overcast login password for direct OPML export |
   | `HARDCOVER_ACCESS_TOKEN` | Hardcover API token |
   | `CODEBASE_USERNAME` | Your GitHub username (for activity tracking) |
   | `BLOG_GITHUB_TOKEN` | PAT with Contents read/write on blog repo |
   | `BLOG_REPO_OWNER` | Blog repo owner |
   | `BLOG_REPO_NAME` | Blog repo name |
   | `BLOG_GITHUB_TARGET_BRANCH` | *(optional)* Branch to commit to, defaults to `main` |

   Prefer `OVERCAST_COOKIE` if you already have a working authenticated cookie. Otherwise set both `OVERCAST_EMAIL` and `OVERCAST_PASSWORD`. If none of those are present, the workflow falls back to `files/overcast*.opml`.

### Schedule

The workflow runs automatically on the **last day of each month at 11:00 AM UTC**.

### Manual Trigger

1. Go to **Actions** tab in your repository
2. Select **"Monthly Pipeline"** workflow
3. Click **"Run workflow"**
4. Optionally check **"Publish for the last month"** to run the report for the previous month
5. Optionally select **dry-run mode** from the command dropdown to validate without publishing
