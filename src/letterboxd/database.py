"""SQLite database manager for Letterboxd data."""

import sqlite3
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path

from ..config import Config
from .models import ALL_TABLES, CREATE_INDEXES


class LetterboxdDatabase:
    """Manages SQLite database for Letterboxd data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        self.db_path = db_path or str(Config.LETTERBOXD_DATABASE_PATH)
        Config.ensure_data_dir()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_tables(self) -> None:
        """Create all tables if they don't exist."""
        is_new = not Path(self.db_path).exists()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table_sql in ALL_TABLES:
                cursor.execute(table_sql)
            for index_sql in CREATE_INDEXES:
                cursor.execute(index_sql)
        
        if is_new:
            print(f"Letterboxd database initialized at: {self.db_path}")
    
    def upsert_user(self, user_data: Dict[str, Any]) -> bool:
        """Insert or update a user."""
        username = user_data.get("Username")
        if not username:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (
                    username, date_joined, given_name, family_name, email,
                    location, website, bio, pronoun, favorite_films, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    date_joined = excluded.date_joined,
                    given_name = excluded.given_name,
                    family_name = excluded.family_name,
                    email = excluded.email,
                    location = excluded.location,
                    website = excluded.website,
                    bio = excluded.bio,
                    pronoun = excluded.pronoun,
                    favorite_films = excluded.favorite_films,
                    updated_at = excluded.updated_at
            """, (
                username,
                user_data.get("Date Joined"),
                user_data.get("Given Name"),
                user_data.get("Family Name"),
                user_data.get("Email Address"),
                user_data.get("Location"),
                user_data.get("Website"),
                user_data.get("Bio"),
                user_data.get("Pronoun"),
                user_data.get("Favorite Films"),
                int(time.time())
            ))
            return True
    
    def upsert_watched(self, watched_data: Dict[str, Any], username: str) -> bool:
        """Insert or update a watched movie."""
        uri = watched_data.get("Letterboxd URI")
        if not uri:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO watched (
                    letterboxd_uri, movie_name, year, watched_at, username
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(letterboxd_uri) DO UPDATE SET
                    movie_name = excluded.movie_name,
                    year = excluded.year,
                    watched_at = excluded.watched_at
            """, (
                uri,
                watched_data.get("Name"),
                int(watched_data.get("Year")) if watched_data.get("Year") else None,
                watched_data.get("Date"),
                username
            ))
            return True
    
    def upsert_rating(self, rating_data: Dict[str, Any], username: str) -> bool:
        """Insert or update a movie rating."""
        uri = rating_data.get("Letterboxd URI")
        if not uri:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ratings (
                    letterboxd_uri, movie_name, year, rating, rated_at, username
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(letterboxd_uri) DO UPDATE SET
                    movie_name = excluded.movie_name,
                    year = excluded.year,
                    rating = excluded.rating,
                    rated_at = excluded.rated_at
            """, (
                uri,
                rating_data.get("Name"),
                int(rating_data.get("Year")) if rating_data.get("Year") else None,
                float(rating_data.get("Rating")),
                rating_data.get("Date"),
                username
            ))
            return True
    
    def get_stats(self) -> Dict[str, int]:
        """Get counts of all entities."""
        stats = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table in ["users", "watched", "ratings"]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
        return stats
