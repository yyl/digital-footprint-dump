"""SQL schema definitions for GitHub activity tracking."""

CREATE_COMMITS_TABLE = """
CREATE TABLE IF NOT EXISTS commits (
    sha TEXT PRIMARY KEY,
    repo TEXT NOT NULL,
    message TEXT,
    author_date TEXT NOT NULL,
    date_month TEXT NOT NULL,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
)
"""

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis (
    year_month TEXT PRIMARY KEY,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    commits INTEGER DEFAULT 0,
    repos_touched INTEGER DEFAULT 0,
    updated_at TEXT
)
"""
