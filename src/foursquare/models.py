"""SQL schema definitions for Foursquare data tables."""

# SQL statements for creating tables

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    foursquare_user_id TEXT PRIMARY KEY NOT NULL,
    last_pulled_timestamp INTEGER DEFAULT 0,
    last_updated_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    CONSTRAINT users_timestamps_check CHECK (last_pulled_timestamp >= 0)
);
"""

CREATE_PLACES_TABLE = """
CREATE TABLE IF NOT EXISTS places (
    fsq_place_id TEXT PRIMARY KEY NOT NULL,
    name TEXT,
    latitude REAL,
    longitude REAL,
    address TEXT,
    locality TEXT,
    region TEXT,
    postcode TEXT,
    country TEXT,
    formatted_address TEXT,
    primary_category_fsq_id TEXT,
    primary_category_name TEXT,
    website TEXT,
    tel TEXT,
    email TEXT,
    price INTEGER,
    rating REAL,
    last_updated_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    CONSTRAINT places_coords_check CHECK (
        (latitude IS NULL AND longitude IS NULL) OR 
        (latitude IS NOT NULL AND longitude IS NOT NULL AND
         latitude BETWEEN -90 AND 90 AND 
         longitude BETWEEN -180 AND 180)
    )
);
"""

CREATE_CHECKINS_TABLE = """
CREATE TABLE IF NOT EXISTS checkins (
    checkin_id TEXT PRIMARY KEY NOT NULL,
    foursquare_user_id TEXT NOT NULL,
    place_fsq_id TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    type TEXT,
    shout TEXT,
    private BOOLEAN DEFAULT 0,
    visibility TEXT,
    is_mayor BOOLEAN DEFAULT 0,
    liked BOOLEAN DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    photos_count INTEGER DEFAULT 0,
    source_name TEXT,
    source_url TEXT,
    time_zone_offset INTEGER,
    imported_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (foursquare_user_id) REFERENCES users(foursquare_user_id) ON DELETE CASCADE,
    FOREIGN KEY (place_fsq_id) REFERENCES places(fsq_place_id) ON DELETE RESTRICT,
    CONSTRAINT checkins_counts_check CHECK (
        comments_count >= 0 AND 
        likes_count >= 0 AND 
        photos_count >= 0
    ),
    CONSTRAINT checkins_timestamps_check CHECK (created_at > 0)
);
"""

CREATE_SYNC_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS sync_state (
    entity_type TEXT PRIMARY KEY,
    last_sync_at TEXT
);
"""

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis (
    year_month TEXT PRIMARY KEY,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    checkins INTEGER DEFAULT 0,
    unique_places INTEGER DEFAULT 0,
    updated_at TEXT
);
"""

# List of all table creation statements
ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_PLACES_TABLE,
    CREATE_CHECKINS_TABLE,
    CREATE_SYNC_STATE_TABLE,
    CREATE_ANALYSIS_TABLE,
]

# Index creation for better query performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_last_pulled ON users(last_pulled_timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_places_name ON places(name);",
    "CREATE INDEX IF NOT EXISTS idx_places_locality ON places(locality);",
    "CREATE INDEX IF NOT EXISTS idx_places_location ON places(latitude, longitude);",
    "CREATE INDEX IF NOT EXISTS idx_places_category ON places(primary_category_fsq_id);",
    "CREATE INDEX IF NOT EXISTS idx_checkins_user ON checkins(foursquare_user_id);",
    "CREATE INDEX IF NOT EXISTS idx_checkins_place ON checkins(place_fsq_id);",
    "CREATE INDEX IF NOT EXISTS idx_checkins_created ON checkins(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_checkins_user_created ON checkins(foursquare_user_id, created_at);",
]

# Views for convenient queries
CREATE_VIEWS = [
    """
    CREATE VIEW IF NOT EXISTS checkins_with_places AS
    SELECT 
        c.checkin_id, c.foursquare_user_id, c.created_at, c.type, c.shout, c.private,
        c.visibility, c.is_mayor, c.liked, c.comments_count, c.likes_count, c.photos_count,
        c.source_name, c.source_url, c.time_zone_offset, c.imported_at,
        p.fsq_place_id, p.name as place_name, p.latitude, p.longitude, p.address,
        p.locality, p.region, p.postcode, p.country, p.primary_category_name, p.rating
    FROM checkins c
    LEFT JOIN places p ON c.place_fsq_id = p.fsq_place_id;
    """,
    """
    CREATE VIEW IF NOT EXISTS user_stats AS
    SELECT 
        u.foursquare_user_id,
        u.last_pulled_timestamp,
        COUNT(c.checkin_id) as total_checkins,
        COUNT(DISTINCT c.place_fsq_id) as unique_places,
        MIN(c.created_at) as first_checkin_date,
        MAX(c.created_at) as last_checkin_date
    FROM users u
    LEFT JOIN checkins c ON u.foursquare_user_id = c.foursquare_user_id
    GROUP BY u.foursquare_user_id;
    """,
]
