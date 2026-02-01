# digital-footprint-dump

A dump of all the digital footprints.

## Setup

```bash
uv sync
cp .env.example .env
# Edit .env with your credentials
```

## Commands

```bash
uv run main.py init              # Initialize all databases
uv run main.py sync              # Sync all services
uv run main.py analyze           # Analyze all sources
uv run main.py readwise-sync     # Sync Readwise only
uv run main.py readwise-analyze  # Analyze Readwise archive
uv run main.py foursquare-sync   # Sync Foursquare only
uv run main.py letterboxd-sync   # Import Letterboxd data
uv run main.py letterboxd-analyze # Analyze Letterboxd movies
uv run main.py overcast-sync     # Import Overcast data
uv run main.py overcast-analyze  # Analyze Overcast podcasts
uv run main.py publish           # Publish monthly summary to blog
uv run main.py status            # Show sync status
```

---

## Readwise

Exports books, highlights, and Reader documents to `data/readwise.db`.

**Commands:**
- `readwise-sync`: Syncs data from Readwise API to the local database.
- `readwise-analyze`: Generates monthly reading stats (archived articles, total words, reading time) and writes to the `analysis` table in `data/readwise.db`.

**Required in .env:**
- `READWISE_ACCESS_TOKEN` - Get from [readwise.io/access_token](https://readwise.io/access_token)

---

## Foursquare

Exports checkins and places to `data/foursquare.db`.

**Required in .env:**
- `FOURSQUARE_CLIENT_ID` - From your [Foursquare app](https://foursquare.com/developers/apps)
- `FOURSQUARE_CLIENT_SECRET`
- `FOURSQUARE_API_KEY` - Service key for Places API

---

## Letterboxd

Imports watched movies and ratings from CSV export to `data/letterboxd.db`.

**Commands:**
- `letterboxd-sync`: Imports data from Letterboxd CSV export.
- `letterboxd-analyze`: Generates monthly movie stats (count, avg/min/max rating, avg years since release) and writes to the `analysis` table.

**Setup:**
1. Export your data from [letterboxd.com/settings/data](https://letterboxd.com/settings/data/)
2. Unzip and place folder in `files/` (e.g., `files/letterboxd-username-2025-...`)
3. Run `uv run main.py letterboxd-sync`

---

## Overcast

Imports podcast feeds and episodes from OPML export to `data/overcast.db`.

**Commands:**
- `overcast-sync`: Imports data from Overcast OPML export.
- `overcast-analyze`: Generates monthly podcast stats (feeds added, feeds removed, episodes played) and writes to the `analysis` table.

**Setup:**
1. Export from [overcast.fm/account](https://overcast.fm/account) → "All data" OPML
2. Place file in `files/` (e.g., `files/overcast.opml`)
3. Run `uv run main.py overcast-sync`

---

## Publishing

Generates a monthly activity summary as a Hugo blog article (draft) and commits it to a GitHub repository.

**Commands:**
- `publish`: Syncs latest data, runs analysis, generates markdown, and commits to GitHub.

**Required in .env:**
- `GITHUB_TOKEN` - Personal access token with repo write access
- `GITHUB_REPO_OWNER` - Repository owner username
- `GITHUB_REPO_NAME` - Repository name
- `GITHUB_TARGET_BRANCH` - (optional) Branch to commit to, defaults to `main`

---

## Project Structure

```
├── main.py                 # CLI entry point
├── src/
│   ├── config.py           # Configuration and environment variables
│   ├── readwise/
│   ├── foursquare/
│   ├── letterboxd/
│   ├── overcast/
│   └── publish/
├── data/                   # SQLite databases (generated)
└── files/                  # Import files (user-provided)
```

### Module Files

Each source module (`readwise/`, `foursquare/`, `letterboxd/`, `overcast/`) follows a consistent pattern:

| File | Description |
|------|-------------|
| `models.py` | SQL schema definitions (table creation statements) |
| `database.py` | Database manager with connection handling and CRUD operations |
| `api_client.py` | API wrapper for external service calls (API sources only) |
| `sync.py` | Sync orchestration between API and database (API sources only) |
| `importer.py` | File parser for CSV/OPML imports (file-based sources only) |
| `analytics.py` | Monthly analysis logic, writes to `analysis` table |

The `publish/` module contains:
| File | Description |
|------|-------------|
| `github_client.py` | GitHub API wrapper for committing files |
| `markdown_generator.py` | Hugo-compatible markdown generation |
| `publisher.py` | Orchestrates analysis fetching and publishing |
