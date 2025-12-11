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
uv run main.py init            # Initialize all databases
uv run main.py sync            # Sync all services
uv run main.py readwise-sync   # Sync Readwise only
uv run main.py foursquare-sync # Sync Foursquare only
uv run main.py status          # Show sync status
```

---

## Readwise

Exports books, highlights, and Reader documents to `data/readwise.db`.

**Required in .env:**
- `READWISE_ACCESS_TOKEN` - Get from [readwise.io/access_token](https://readwise.io/access_token)

---

## Foursquare

Exports checkins and places to `data/foursquare.db`.

**Required in .env:**
- `FOURSQUARE_CLIENT_ID` - From your [Foursquare app](https://foursquare.com/developers/apps)
- `FOURSQUARE_CLIENT_SECRET`
- `FOURSQUARE_API_KEY` - Service key for Places API

On first sync, you'll be prompted to authorize via browser. The access token is saved automatically.

---

## Project Structure

```
├── main.py
├── src/
│   ├── config.py
│   ├── database.py, models.py, api_client.py, sync.py  # Readwise
│   └── foursquare/
│       ├── database.py, models.py, api_client.py, sync.py
└── data/
    ├── readwise.db
    └── foursquare.db
```
