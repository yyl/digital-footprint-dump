"""Base database class for SQLite connections."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import Config


class BaseDatabase:
    """Base class for SQLite database managers."""

    def __init__(self, db_path: str):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database.
        """
        self.db_path = db_path
        self.use_foreign_keys = False
        Config.ensure_data_dir()

    @contextmanager
    def get_connection(self):
        """Get a database connection as a context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if self.use_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON")
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
