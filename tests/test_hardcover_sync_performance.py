import pytest
import os
from unittest.mock import MagicMock, patch
from src.hardcover.sync import HardcoverSyncManager
from src.hardcover.database import HardcoverDatabase

def test_hardcover_sync_uses_bulk_upsert():
    # Mock DB
    mock_db = MagicMock(spec=HardcoverDatabase)
    mock_db.exists.return_value = True

    # Mock API
    mock_api = MagicMock()
    mock_api.get_finished_books.return_value = [
        {
            "book": {
                "slug": "book-1",
                "title": "Book 1",
                "cached_contributors": [{"name": "Author 1"}]
            },
            "rating": 5,
            "date_added": "2023-01-01",
            "reviewed_at": "2023-01-02",
        },
        {
            "book": {
                "slug": "book-2",
                "title": "Book 2",
            },
            # Missing rating/dates
        }
    ]

    sync_manager = HardcoverSyncManager(db=mock_db, api=mock_api)

    sync_manager.sync()

    # Verify upsert_books was called once with 2 books
    assert mock_db.upsert_books.call_count == 1
    args = mock_db.upsert_books.call_args[0][0]
    assert len(args) == 2
    assert args[0]["slug"] == "book-1"
    assert args[1]["slug"] == "book-2"

    # Verify init_tables was called
    mock_db.init_tables.assert_called_once()

def test_upsert_books_real_db(tmp_path):
    # Test with a real temporary database
    db_path = tmp_path / "test_hardcover.db"
    db = HardcoverDatabase(str(db_path))
    db.init_tables()

    books = [
        {
            "slug": "book-1",
            "title": "Book One",
            "author": "Author A",
            "rating": 4.5,
            "date_added": "2023-01-01",
            "reviewed_at": "2023-01-02",
            "date_read": "2023-01-02"
        },
        {
            "slug": "book-2",
            "title": "Book Two",
            "author": "Author B",
            "rating": None,
            "date_added": "2023-02-01",
            "reviewed_at": None,
            "date_read": "2023-02-01"
        }
    ]

    db.upsert_books(books)

    stats = db.get_stats()
    assert stats["books"] == 2

    # Verify data integrity
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books ORDER BY slug")
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert rows[0]["slug"] == "book-1"
        assert rows[0]["title"] == "Book One"
        assert rows[1]["slug"] == "book-2"
        assert rows[1]["title"] == "Book Two"

    # Test update via upsert
    books[0]["rating"] = 5.0
    db.upsert_books([books[0]])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM books WHERE slug = 'book-1'")
        rating = cursor.fetchone()[0]
        assert rating == 5.0
