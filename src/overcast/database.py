"""SQLite database manager for Overcast data."""

import sqlite3
from typing import Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path

from ..config import Config


class OvercastDatabase:
    """Manages SQLite database for Overcast data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        self.db_path = db_path or str(Config.OVERCAST_DATABASE_PATH)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def exists(self) -> bool:
        """Check if the database file exists."""
        return Path(self.db_path).exists()
    
    def get_stats(self) -> Dict[str, int]:
        """Get counts from the database."""
        stats = {"feeds": 0, "episodes": 0, "playlists": 0}
        
        if not self.exists():
            return stats
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for table in ["feeds", "episodes", "playlists"]:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[table] = cursor.fetchone()[0]
                    except sqlite3.OperationalError:
                        pass
        except Exception:
            pass
        
        return stats
