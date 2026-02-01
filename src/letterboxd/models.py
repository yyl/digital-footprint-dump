"""SQL schema definitions for Letterboxd data tables."""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY NOT NULL,
    date_joined TEXT,
    given_name TEXT,
    family_name TEXT,
    email TEXT,
    location TEXT,
    website TEXT,
    bio TEXT,
    pronoun TEXT,
    favorite_films TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""

CREATE_WATCHED_TABLE = """
CREATE TABLE IF NOT EXISTS watched (
    letterboxd_uri TEXT PRIMARY KEY NOT NULL,
    movie_name TEXT NOT NULL,
    year INTEGER,
    watched_at TEXT NOT NULL,
    username TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
"""

CREATE_RATINGS_TABLE = """
CREATE TABLE IF NOT EXISTS ratings (
    letterboxd_uri TEXT PRIMARY KEY NOT NULL,
    movie_name TEXT NOT NULL,
    year INTEGER,
    rating REAL NOT NULL,
    rated_at TEXT NOT NULL,
    username TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
    CONSTRAINT ratings_range CHECK (rating >= 0.5 AND rating <= 5.0)
);
"""

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis (
    year_month TEXT PRIMARY KEY,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    movies_watched REAL DEFAULT 0,
    avg_rating REAL DEFAULT 0,
    min_rating REAL DEFAULT 0,
    max_rating REAL DEFAULT 0,
    avg_years_since_release REAL DEFAULT 0,
    updated_at TEXT
);
"""

ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_WATCHED_TABLE,
    CREATE_RATINGS_TABLE,
    CREATE_ANALYSIS_TABLE,
]

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_watched_username ON watched(username);",
    "CREATE INDEX IF NOT EXISTS idx_watched_date ON watched(watched_at);",
    "CREATE INDEX IF NOT EXISTS idx_ratings_username ON ratings(username);",
    "CREATE INDEX IF NOT EXISTS idx_ratings_date ON ratings(rated_at);",
    "CREATE INDEX IF NOT EXISTS idx_ratings_rating ON ratings(rating);",
    "CREATE INDEX IF NOT EXISTS idx_analysis_year_month ON analysis(year, month);",
]
