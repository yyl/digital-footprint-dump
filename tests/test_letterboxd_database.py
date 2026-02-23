"""Tests for LetterboxdDatabase."""

import pytest
import sqlite3
import os
from src.letterboxd.database import LetterboxdDatabase


@pytest.fixture
def mock_db_path(tmp_path):
    """Fixture to provide a temporary database path."""
    db_file = tmp_path / "test_letterboxd.db"
    return str(db_file)


def test_letterboxd_database_connection_and_foreign_keys(mock_db_path):
    """Test that LetterboxdDatabase initializes correctly and enables foreign keys."""
    # We pass the path explicitly, so no need to patch Config
    db = LetterboxdDatabase(db_path=mock_db_path)

    # Verify foreign keys are enabled
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        # result[0] should be 1 if foreign_keys are ON
        assert result[0] == 1, "Foreign keys should be enabled"

    # Verify row factory is set
    with db.get_connection() as conn:
        assert conn.row_factory == sqlite3.Row, "Row factory should be sqlite3.Row"


def test_letterboxd_database_init_tables(mock_db_path):
    """Test that tables are initialized correctly."""
    db = LetterboxdDatabase(db_path=mock_db_path)
    db.init_tables()

    # Verify tables exist
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert "users" in tables
        assert "watched" in tables
        assert "ratings" in tables
