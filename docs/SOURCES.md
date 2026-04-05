# Supported Sources

This repository syncs data from various digital platforms. Below are the details for each supported source.

## Readwise

Exports books, highlights, and Reader documents to `<storage-root>/data/readwise.db`.

**Commands:**
- `readwise-sync`: Syncs data from Readwise API to the local database.
- `readwise-analyze`: Generates monthly reading stats (archived articles, total words, reading time, max/median/min words per article) and writes to the `analysis` table in `data/readwise.db`.

**Required in .env:**
- `READWISE_ACCESS_TOKEN` - Get from [readwise.io/access_token](https://readwise.io/access_token)

---

## Foursquare

Exports checkins and places to `<storage-root>/data/foursquare.db`.

**Commands:**
- `foursquare-sync`: Syncs checkin history from Foursquare API.
- `foursquare-analyze`: Generates monthly stats (checkins, unique places) and writes to the `analysis` table.

**Required in .env:**
- `FOURSQUARE_ACCESS_TOKEN` - OAuth token used for all v2 API calls (checkins, user info)
- `FOURSQUARE_CLIENT_ID` - Only needed for initial OAuth flow / re-auth. From your [Foursquare app](https://foursquare.com/developers/apps)
- `FOURSQUARE_CLIENT_SECRET` - Only needed for initial OAuth flow / re-auth
- `FOURSQUARE_API_KEY` - *(optional)* Service key for Places API; enriches venue details but falls back to checkin data if absent

---

## Letterboxd

Imports watched movies and ratings from CSV export to `<storage-root>/data/letterboxd.db`.

**Commands:**
- `letterboxd-sync`: Imports data from Letterboxd CSV export.
- `letterboxd-analyze`: Generates monthly movie stats (count, avg/min/max rating, avg years since release) and writes to the `analysis` table.

**Required in .env:**
- None (File-based export)

**Setup:**
1. Export your data from [letterboxd.com/settings/data](https://letterboxd.com/settings/data/)
2. Unzip and place folder in `<storage-root>/files/` (e.g., `files/letterboxd-username-2025-...`)
3. Run `uv run main.py letterboxd-sync`

---

## Overcast

Imports podcast feeds and episodes from OPML export to `<storage-root>/data/overcast.db`.

**Commands:**
- `overcast-sync`: Imports data from Overcast OPML export.
- `overcast-analyze`: Generates monthly podcast stats (feeds added, feeds removed, episodes played) and writes to the `analysis` table.

**Required in .env:**
- None (File-based export)

**Setup:**
1. Export from [overcast.fm/account](https://overcast.fm/account) → "All data" OPML
2. Place file in `<storage-root>/files/` (e.g., `files/overcast.opml`)
3. Run `uv run main.py overcast-sync`

---

## Strong

Imports workout data from Strong app CSV export to `<storage-root>/data/strong.db`.

**Commands:**
- `strong-sync`: Imports workout and exercise data from CSV export.
- `strong-analyze`: Generates monthly stats (workouts, total minutes, unique exercises, total sets) and writes to the `analysis` table.

**Required in .env:**
- None (File-based export)

**Setup:**
1. Export from [Strong app](https://www.strong.app/) → Settings → Export Data
2. Place CSV in `<storage-root>/files/` (e.g., `files/strong_workouts.csv`)
3. Run `uv run main.py strong-sync`

---

## Hardcover

Syncs finished books from [Hardcover](https://hardcover.app/) via their GraphQL API to `<storage-root>/data/hardcover.db`.

**Commands:**
- `hardcover-sync`: Fetches all books marked as "read" from Hardcover API.
- `hardcover-analyze`: Generates monthly stats (books finished, average rating) and writes to the `analysis` table.

**Required in .env:**
- `HARDCOVER_ACCESS_TOKEN` - Get from [hardcover.app/account/api](https://hardcover.app/account/api)

**Setup:**
1. Get your API token and add `HARDCOVER_ACCESS_TOKEN` to your `.env`
2. Run `uv run main.py hardcover-sync`

---

## GitHub

Syncs commit history from your public repositories via the GitHub REST API to `<storage-root>/data/github.db`.

**Commands:**
- `github-sync`: Fetches commits from all owned public repos (non-fork).
- `github-analyze`: Generates monthly stats (commits, repos touched) and writes to the `analysis` table.

**Required in .env:**
- `CODEBASE_USERNAME` - Your GitHub username
- `BLOG_GITHUB_TOKEN` - Reused for authenticated API access (5000 req/hr)
