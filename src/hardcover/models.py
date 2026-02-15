"""SQL schema definitions for Hardcover book tracking."""

CREATE_BOOKS_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    rating REAL,
    date_added TEXT,
    reviewed_at TEXT,
    date_read TEXT,
    slug TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
)
"""

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis (
    year_month TEXT PRIMARY KEY,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    books_finished INTEGER DEFAULT 0,
    avg_rating REAL,
    updated_at TEXT
)
"""
