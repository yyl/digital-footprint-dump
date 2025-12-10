# digital-footprint-dump

A dump of all the digital footprints.

## Readwise Data Exporter

Exports all your Readwise data (books, highlights, Reader documents) to SQLite with incremental sync support.

### Setup

```bash
# Install dependencies (uv will handle this automatically on first run)
uv sync

# Configure your Readwise token
cp .env.example .env
# Edit .env and add your token from https://readwise.io/access_token
```

### Commands

```bash
uv run main.py init     # Initialize database tables
uv run main.py sync     # Sync data from Readwise (incremental)
uv run main.py status   # Show sync status and counts
```

### Database

Data is stored in `data/readwise.db` with these tables:

| Table | Description |
|-------|-------------|
| `books` | Books, articles, podcasts from Readwise |
| `highlights` | User highlights with notes |
| `documents` | Reader documents |
| `*_tags` | Tags for each entity |
| `sync_state` | Tracks last sync time |

### Project Structure

```
├── main.py              # CLI entry point
├── src/
│   ├── config.py        # Environment configuration
│   ├── models.py        # SQL schema definitions
│   ├── database.py      # SQLite operations
│   ├── api_client.py    # Readwise API client
│   └── sync.py          # Sync orchestration
└── data/readwise.db     # SQLite database
```
