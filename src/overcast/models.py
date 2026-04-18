"""SQL schema definitions for Overcast analysis tables."""

# Note: The main Overcast tables (feeds, episodes, playlists) are created
# by the external overcast-to-sqlite tool. This file only defines tables
# managed by our analytics module.

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis (
    year_month TEXT PRIMARY KEY,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    feeds_added INTEGER DEFAULT 0,
    feeds_removed INTEGER DEFAULT 0,
    episodes_played INTEGER DEFAULT 0,
    minutes_listened INTEGER DEFAULT 0,
    updated_at TEXT
);
"""

# Migration: add duration_seconds to the episodes table created by overcast-to-sqlite.
# Idempotent — safe to run multiple times.
ADD_DURATION_COLUMN = """
ALTER TABLE episodes ADD COLUMN duration_seconds INTEGER;
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_analysis_year_month ON analysis(year, month);",
]
