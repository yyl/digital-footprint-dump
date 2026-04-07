"""SQL schema definitions for blog post tracking."""

CREATE_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS posts (
    permalink TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    published_at TEXT NOT NULL,
    last_modified_at TEXT,
    slug TEXT,
    word_count INTEGER DEFAULT 0,
    reading_time INTEGER DEFAULT 0,
    summary TEXT,
    section TEXT,
    draft INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""

CREATE_POST_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS post_tags (
    permalink TEXT NOT NULL,
    tag TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    PRIMARY KEY (permalink, tag),
    FOREIGN KEY (permalink) REFERENCES posts(permalink) ON DELETE CASCADE
);
"""

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis (
    year_month TEXT PRIMARY KEY,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    posts INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    unique_tags INTEGER DEFAULT 0,
    updated_at TEXT
);
"""

RAW_TABLES = [
    CREATE_POSTS_TABLE,
    CREATE_POST_TAGS_TABLE,
]

RAW_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at ON posts(published_at);",
    "CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON posts(slug);",
    "CREATE INDEX IF NOT EXISTS idx_blog_post_tags_tag ON post_tags(tag);",
]

ANALYSIS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_blog_analysis_year_month ON analysis(year, month);",
]
