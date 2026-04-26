# Source Modules

This document is the developer-oriented guide to how the codebase works.

It covers architecture, storage layout, per-source implementation patterns, analysis tables, publishing, backfill behavior, and deployment details that are useful when modifying the repo.

## Project Structure

Note: the tree below is shown from the repository root.

```text
├── main.py                 # CLI entry point
├── src/
│   ├── config.py           # Environment configuration and storage resolution
│   ├── database.py         # Base SQLite connection manager
│   ├── comparison.py       # Shared MoM/YoY comparison helpers
│   ├── time_utils.py       # UTC timestamp helpers
│   ├── readwise/
│   ├── foursquare/
│   ├── letterboxd/
│   ├── overcast/
│   ├── strong/
│   ├── apple_health/
│   ├── blog/
│   ├── hardcover/
│   ├── github/
│   └── publish/
├── docs/
├── tests/
└── .github/workflows/
```

## Storage Resolution

The app does not always read and write data from this repo directly.

It resolves a storage root, then uses:

- `<storage-root>/data/` for SQLite databases
- `<storage-root>/files/` for file imports

Resolution order:

1. `DATA_REPO_LOCAL_PATH` if set
2. sibling repo `../digital-footprint-data` if it exists
3. this repo itself

That means local development often uses:

- `/.../digital-footprint-data/data/*.db`
- `/.../digital-footprint-data/files/*`

GitHub Actions checks out the private data repo separately and links its `data/` and `files/` into the workspace.

## Local and CI Consistency

The repo pins Python in `.python-version`.

Recommended validation:

```bash
make test-ci
```

That command installs the pinned Python version with `uv`, syncs dependencies, and runs `pytest` with the same interpreter used by CI.

For markdown generation changes, also run:

```bash
uv run main.py publish --dry-run
```

## Module Pattern

Each source generally follows the same structure:

| File | Purpose |
|------|---------|
| `models.py` | SQL schema definitions |
| `database.py` | Source-specific database manager |
| `api_client.py` | External API wrapper for API-backed sources |
| `sync.py` | Sync orchestration for API-backed sources |
| `importer.py` | File import path for file-backed sources |
| `analytics.py` | Monthly rollups written into `analysis` |

Raw data tables are created during sync/import setup. Derived monthly `analysis` tables are owned by each source's `analytics.py`.

## Source Types

| Type | Sources | Ingestion Path |
|------|---------|----------------|
| API-backed | Readwise, Foursquare, Blog, Hardcover, GitHub | `api_client.py` + `sync.py` |
| File-backed | Letterboxd, Overcast, Strong, Apple Health | `importer.py` |

Letterboxd is hybrid in practice: it uses RSS for incremental sync, plus CSV export seeding when the DB is empty.

## Publish Module

The `src/publish/` package contains the publishing layer.

| File | Purpose |
|------|---------|
| `publisher.py` | Orchestrates data fetch, comparisons, report assembly, and publish flow |
| `markdown_generator.py` | Renders the monthly markdown report |
| `data_generator.py` | Generates `data/activity/*.yaml` files from analysis tables |
| `github_client.py` | Writes report/data files to GitHub using PyGithub |

## Publish and Backfill Flows

### Publish

Supported paths:

- `publish`: sync all sources, analyze all sources, generate the report, commit the draft post
- `publish --skip-sync-analysis`: generate the report from existing analysis data
- `publish --dry-run`: render the report locally only
- `publish --last-month`: publish the previous month instead of the latest available month

The publish flow scans the available analysis DBs and chooses the latest available `YYYY-MM`, while tolerating optional sources that may be missing.

### Backfill

`backfill` regenerates activity data files twice: the full-history set goes to the data repo, and a second set limited to the rolling one-year lookback window goes to the blog repo under `data/activity/`.

It does that by running each source's analyze command, and those analyze commands in turn refresh raw source data first through their paired sync path.

Current activity files:

| File | Source | Fields |
|------|--------|--------|
| `reading.yaml` | Readwise | `articles_archived`, `total_words`, `time_spent_minutes`, `avg_reading_speed`, `max_words_per_article`, `median_words_per_article`, `min_words_per_article` |
| `travel.yaml` | Foursquare | `checkins`, `unique_places` |
| `movies.yaml` | Letterboxd | `movies_watched`, `minutes_watched`, `avg_rating` |
| `podcasts.yaml` | Overcast | `feeds_added`, `feeds_removed`, `episodes_played`, `minutes_listened` |
| `workouts.yaml` | Apple Health | `workouts`, `total_minutes`, `total_calories` |
| `writing.yaml` | Blog | `posts`, `total_words`, `unique_tags` |
| `books.yaml` | Hardcover | `books_finished`, `avg_rating` |
| `code.yaml` | GitHub | `commits`, `repos_touched` |

Published workout metrics come from Apple Health monthly analysis. Strong is still importable and analyzable, but it is not the published workout source.

## Source-Specific Technical Notes

### Readwise

- Syncs Reader documents plus associated metadata into `readwise.db`
- Analysis computes article counts, total words, reading time, and article-length stats
- Reading speed comparison in the published report is derived rather than stored directly in the analysis table

### Foursquare

- Uses the Foursquare v2 API for core checkin/user data
- Can optionally enrich venue details through the Places API when `FOURSQUARE_API_KEY` is configured

### Letterboxd

Letterboxd uses a hybrid ingestion model:

- historical seed from CSV export in `files/letterboxd-*`
- incremental updates from public RSS via `LETTERBOXD_RSS_URL`

Important implementation details:

- CSV and RSS data are deduplicated by checking whether the same movie name already exists within a `+/- 2 day` watch-date window
- RSS entries are normalized from user-specific film links to canonical film URLs when possible
- `watched` stores enriched metadata fields:
  - `tmdb_id`
  - `runtime_minutes`
  - `metadata_updated_at`
- If `TMDB_ACCESS_TOKEN` or `TMDB_API_KEY` is configured, `letterboxd-sync` performs a TMDB enrichment pass after import/sync
- The TMDB enrichment path prefers exact title plus exact year, then falls back to exact title with a `+/- 1` year window
- If runtime enrichment still fails, sync prints the unmatched movie titles

Letterboxd analysis writes:

- `movies_watched`
- `minutes_watched`
- `avg_rating`
- `min_rating`
- `max_rating`
- `avg_years_since_release`

`minutes_watched` is computed from the summed `watched.runtime_minutes` values available for that month.

### Overcast

- Supports direct OPML export fetch when `OVERCAST_COOKIE` or `OVERCAST_EMAIL` plus `OVERCAST_PASSWORD` are configured
- Falls back to `files/overcast*.opml` import otherwise
- `overcast-sync` also fetches missing episode durations from live RSS feeds using title matching
- Those duration lookups populate `episodes.duration_seconds`, which enables monthly `minutes_listened`

### Strong

- Imports Strong CSV workout exports into `strong.db`
- Still has its own analysis path for workout/exercise/set metrics
- No longer drives the published workout section

### Apple Health

- Imports workouts from `export.xml`
- Monthly analysis is the source of truth for the published workout section and `workouts.yaml`

### Blog

- Syncs from a public Hugo JSON index rather than writing to the blog repo directly
- The `Writing` report section and `writing.yaml` come from blog analysis

### Hardcover

- Uses the Hardcover GraphQL API
- Tracks finished books and monthly average rating

### GitHub

- Syncs commit history from owned public repositories
- Uses an inclusive timestamp cursor plus SHA deduplication so same-second commits are not skipped
- Publishing uses PyGithub and retries branch update races when necessary

## Database Schemas

Each source has a separate SQLite database under `<storage-root>/data/`.

### Common Analysis Table Shape

Every source's `analysis` table has:

- `year_month` as a `YYYY-MM` primary key
- `year`
- `month`
- source-specific metrics
- `updated_at`

### Per-Source Databases

#### Readwise (`readwise.db`)

Data tables:

- `books`
- `highlights`
- `highlight_tags`
- `book_tags`
- `documents`
- `document_tags`
- `sync_state`

Analysis fields:

- `articles`
- `words`
- `reading_time_mins`
- `max_words_per_article`
- `median_words_per_article`
- `min_words_per_article`

#### Foursquare (`foursquare.db`)

Data tables:

- `users`
- `places`
- `checkins`
- `sync_state`

Views:

- `checkins_with_places`
- `user_stats`

Analysis fields:

- `checkins`
- `unique_places`

#### Letterboxd (`letterboxd.db`)

Data tables:

- `users`
- `watched`
- `ratings`

`watched` also stores:

- `tmdb_id`
- `runtime_minutes`
- `metadata_updated_at`

Analysis fields:

- `movies_watched`
- `minutes_watched`
- `avg_rating`
- `min_rating`
- `max_rating`
- `avg_years_since_release`

#### Overcast (`overcast.db`)

Primary tables are created by `overcast-to-sqlite`:

- `feeds`
- `episodes`
- `playlists`

Analysis fields:

- `feeds_added`
- `feeds_removed`
- `episodes_played`
- `minutes_listened`

#### Strong (`strong.db`)

Data tables:

- `workouts`
- `exercises`

Analysis fields:

- `workouts`
- `total_duration_seconds`
- `unique_exercises`
- `total_sets`

#### Apple Health (`apple_health.db`)

Data tables:

- `workouts`

Analysis fields:

- `workouts`
- `total_duration_seconds`
- `total_calories`

#### Blog (`blog.db`)

Data tables:

- `posts`
- `post_tags`

Analysis fields:

- `posts`
- `total_words`
- `unique_tags`

#### Hardcover (`hardcover.db`)

Data tables:

- `books`

Analysis fields:

- `books_finished`
- `avg_rating`

#### GitHub (`github.db`)

Data tables:

- `commits`

Analysis fields:

- `commits`
- `repos_touched`

## Comparisons

`src/comparison.py` contains the shared MoM and YoY comparison helpers used by publish.

Sources currently surfaced in the published report use comparisons for these metrics:

| Source | Metrics |
|--------|---------|
| Readwise | articles, words, reading time, derived reading speed |
| Foursquare | checkins, unique places |
| Letterboxd | movies watched, average rating |
| Overcast | episodes played, minutes listened |
| Apple Health | workouts, total duration, total calories |
| Blog | posts, total words, unique tags |
| Hardcover | books finished, average rating |
| GitHub | commits, repos touched |

## Database Access Pattern

All DB managers inherit from `BaseDatabase` in [`src/database.py`](/Users/yulong/Documents%20(local)/coding/digital-footprint-dump/src/database.py).

Typical usage:

```python
with self.db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    rows = cursor.fetchall()
```

Connections use `sqlite3.Row`, so rows are accessed by column name.

## Time and Timestamps

`src/time_utils.py` provides UTC timestamp helpers, including `utc_now_iso()`, which is used for `updated_at` values in analysis tables.

## Configuration

`src/config.py` loads `.env`, resolves the storage root, and exposes validation methods.

Key config areas:

| Area | Variables |
|------|-----------|
| Readwise | `READWISE_ACCESS_TOKEN` |
| Foursquare | `FOURSQUARE_ACCESS_TOKEN`, `FOURSQUARE_CLIENT_ID`, `FOURSQUARE_CLIENT_SECRET`, `FOURSQUARE_API_KEY` |
| Letterboxd | `LETTERBOXD_RSS_URL`, `TMDB_ACCESS_TOKEN`, `TMDB_API_KEY` |
| Overcast | `OVERCAST_COOKIE`, `OVERCAST_EMAIL`, `OVERCAST_PASSWORD` |
| Blog tracking | `BLOG_POSTS_INDEX_URL` |
| Hardcover | `HARDCOVER_ACCESS_TOKEN` |
| GitHub activity | `CODEBASE_USERNAME`, `BLOG_GITHUB_TOKEN` |
| GitHub publishing | `BLOG_GITHUB_TOKEN`, `BLOG_REPO_OWNER`, `BLOG_REPO_NAME`, `BLOG_GITHUB_TARGET_BRANCH`, `DATA_REPO_OWNER`, `DATA_REPO_NAME`, `DATA_GITHUB_TARGET_BRANCH` |
| Storage override | `DATA_REPO_LOCAL_PATH` |

## Testing

Useful commands:

```bash
uv run pytest
make test-ci
uv run main.py publish --dry-run
```

When docs or behavior change around the monthly report or activity files, `publish --dry-run` is the most useful end-to-end validation step.

## Cloud Deployment

This repo includes GitHub Actions for tests and monthly pipeline automation.

For the monthly pipeline, the common deployment model is:

1. public repo for this code
2. private repo for `data/` and `files/`
3. PAT/secrets for the source APIs and the target blog repo

Common Actions secrets include:

- `DATA_REPO_OWNER`
- `DATA_REPO_NAME`
- `DATA_REPO_PAT`
- `READWISE_ACCESS_TOKEN`
- `FOURSQUARE_ACCESS_TOKEN`
- `FOURSQUARE_API_KEY`
- `OVERCAST_COOKIE`
- `OVERCAST_EMAIL`
- `OVERCAST_PASSWORD`
- `HARDCOVER_ACCESS_TOKEN`
- `CODEBASE_USERNAME`
- `BLOG_GITHUB_TOKEN`
- `BLOG_REPO_OWNER`
- `BLOG_REPO_NAME`
- `BLOG_GITHUB_TARGET_BRANCH`
- `TMDB_ACCESS_TOKEN` or `TMDB_API_KEY` if you want Letterboxd runtime enrichment in Actions too
