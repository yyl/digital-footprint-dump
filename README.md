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
uv run main.py init             # Initialize all databases
uv run main.py sync             # Sync all services
uv run main.py readwise-sync    # Sync Readwise only
uv run main.py readwise-analyze # Analyze Readwise archive
uv run main.py foursquare-sync  # Sync Foursquare only
uv run main.py letterboxd-sync  # Import Letterboxd data
uv run main.py overcast-sync    # Import Overcast data
uv run main.py publish          # Publish monthly summary to blog
uv run main.py status           # Show sync status
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

**Setup:**
1. Export your data from [letterboxd.com/settings/data](https://letterboxd.com/settings/data/)
2. Unzip and place folder in `files/` (e.g., `files/letterboxd-username-2025-...`)
3. Run `uv run main.py letterboxd-sync`

---

## Overcast

Imports podcast feeds and episodes from OPML export to `data/overcast.db`.

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
├── main.py
├── src/
│   ├── config.py
│   ├── readwise/
│   ├── foursquare/
│   ├── letterboxd/
│   └── overcast/
├── data/
│   ├── readwise.db
│   ├── foursquare.db
│   ├── letterboxd.db
│   └── overcast.db
└── files/
    ├── letterboxd-*/
    └── overcast*.opml
```
