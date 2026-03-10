"""SQLite database manager for Overcast data."""

import sqlite3
from typing import Optional, Dict, Any

from ..config import Config
from ..database import BaseDatabase


class OvercastDatabase(BaseDatabase):
    """Manages SQLite database for Overcast data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        super().__init__(db_path or str(Config.OVERCAST_DATABASE_PATH))
    
    def get_stats(self) -> Dict[str, int]:
        """Get counts from the database."""
        stats = {"feeds": 0, "episodes": 0, "playlists": 0}
        
        if not self.exists():
            return stats
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # We use explicit queries for each table to avoid f-string SQL injection,
                # even though the table names are hardcoded here.
                try:
                    cursor.execute("SELECT COUNT(*) FROM feeds")
                    stats["feeds"] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass

                try:
                    cursor.execute("SELECT COUNT(*) FROM episodes")
                    stats["episodes"] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass

                try:
                    cursor.execute("SELECT COUNT(*) FROM playlists")
                    stats["playlists"] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass
        except Exception:
            pass
        
        return stats
