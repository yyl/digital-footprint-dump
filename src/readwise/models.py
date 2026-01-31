"""SQL schema definitions for Readwise data tables."""

# SQL statements for creating tables

CREATE_BOOKS_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_book_id INTEGER UNIQUE NOT NULL,
    title TEXT,
    author TEXT,
    readable_title TEXT,
    source TEXT,
    cover_image_url TEXT,
    unique_url TEXT,
    category TEXT,
    document_note TEXT,
    summary TEXT,
    readwise_url TEXT,
    source_url TEXT,
    external_id TEXT,
    asin TEXT,
    is_deleted INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
"""

CREATE_HIGHLIGHTS_TABLE = """
CREATE TABLE IF NOT EXISTS highlights (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    text TEXT,
    note TEXT,
    location INTEGER,
    location_type TEXT,
    color TEXT,
    url TEXT,
    external_id TEXT,
    end_location INTEGER,
    highlighted_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    is_favorite INTEGER DEFAULT 0,
    is_discard INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    readwise_url TEXT,
    FOREIGN KEY (book_id) REFERENCES books(user_book_id)
);
"""

CREATE_HIGHLIGHT_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS highlight_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    highlight_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    FOREIGN KEY (highlight_id) REFERENCES highlights(id),
    UNIQUE(highlight_id, tag_name)
);
"""

CREATE_BOOK_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS book_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(user_book_id),
    UNIQUE(book_id, tag_name)
);
"""

CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    url TEXT,
    source_url TEXT,
    title TEXT,
    author TEXT,
    source TEXT,
    category TEXT,
    location TEXT,
    site_name TEXT,
    word_count INTEGER,
    reading_time TEXT,
    notes TEXT,
    summary TEXT,
    image_url TEXT,
    parent_id TEXT,
    reading_progress REAL,
    published_date TEXT,
    first_opened_at TEXT,
    last_opened_at TEXT,
    saved_at TEXT,
    last_moved_at TEXT,
    created_at TEXT,
    updated_at TEXT
);
"""

CREATE_DOCUMENT_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS document_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    tag_key TEXT NOT NULL,
    tag_name TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    UNIQUE(document_id, tag_key)
);
"""

CREATE_SYNC_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS sync_state (
    entity_type TEXT PRIMARY KEY,
    last_sync_at TEXT,
    last_cursor TEXT
);
"""

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis (
    year_month TEXT PRIMARY KEY,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    articles INTEGER DEFAULT 0,
    words INTEGER DEFAULT 0,
    reading_time_mins INTEGER DEFAULT 0,
    updated_at TEXT
);
"""

# List of all table creation statements
ALL_TABLES = [
    CREATE_BOOKS_TABLE,
    CREATE_HIGHLIGHTS_TABLE,
    CREATE_HIGHLIGHT_TAGS_TABLE,
    CREATE_BOOK_TAGS_TABLE,
    CREATE_DOCUMENTS_TABLE,
    CREATE_DOCUMENT_TAGS_TABLE,
    CREATE_SYNC_STATE_TABLE,
    CREATE_ANALYSIS_TABLE,
]

# Index creation for better query performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_highlights_book_id ON highlights(book_id);",
    "CREATE INDEX IF NOT EXISTS idx_highlight_tags_highlight_id ON highlight_tags(highlight_id);",
    "CREATE INDEX IF NOT EXISTS idx_book_tags_book_id ON book_tags(book_id);",
    "CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_documents_parent_id ON documents(parent_id);",
    "CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);",
    "CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);",
    "CREATE INDEX IF NOT EXISTS idx_analysis_year_month ON analysis(year, month);",
]
