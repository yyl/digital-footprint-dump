# Source Modules

This directory contains the core logic for the digital-footprint-dump pipeline.

## Structure

```
src/
├── config.py           # Environment configuration
├── comparison.py       # Generic MoM/YoY comparison utilities
├── readwise/           # Readwise Reader integration
├── foursquare/         # Foursquare/Swarm integration
├── letterboxd/         # Letterboxd CSV import
├── overcast/           # Overcast OPML import
└── publish/            # Markdown generation & GitHub publishing
```

## Module Pattern

Each data source follows a consistent structure:

| File | Purpose |
|------|---------|
| `models.py` | SQL schema definitions (CREATE TABLE statements) |
| `database.py` | Database manager with connection handling and CRUD |
| `api_client.py` | API wrapper (API sources only) |
| `sync.py` | Sync orchestration (API sources only) |
| `importer.py` | File parser (file-based sources only) |
| `analytics.py` | Monthly analysis logic → writes to `analysis` table |

## Key Concepts

### Analysis Tables

Each source has an `analysis` table with this common structure:
- `year_month` (TEXT, PRIMARY KEY) - Format: `YYYY-MM`
- `year` (TEXT), `month` (TEXT)
- Source-specific metrics (e.g., `articles`, `checkins`, `movies_watched`)
- `updated_at` (TEXT) - ISO timestamp

### Adding MoM/YoY Comparisons

The `comparison.py` module provides generic utilities for computing percentage changes:

```python
from src.comparison import compute_comparisons, format_change

# In publisher.py
comparisons = compute_comparisons(
    current_stats=data,
    historical_getter=self._get_source_analysis,  # Function that takes year_month
    year_month="2026-02",
    metrics=['metric1', 'metric2']
)
# Returns: {'metric1': {'mom': 15.0, 'yoy': -5.0}, ...}

# In markdown_generator.py
formatted = format_change(comparisons['metric1']['mom'])  # "+15%"
```

**Key functions:**
- `compute_percentage_change(current, previous)` → percentage or None
- `get_comparison_periods(year_month)` → `{'mom': '2026-01', 'yoy': '2025-02'}`
- `format_change(value)` → `"+15%"`, `"-10%"`, or `"N/A"`
- `compute_comparisons(...)` → dict of metrics with MoM/YoY values

### Database Connections

All database managers use a context manager pattern:

```python
with self.db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    rows = cursor.fetchall()
    # rows are sqlite3.Row objects - access like dicts: row['column']
```

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_comparison.py -v
```
