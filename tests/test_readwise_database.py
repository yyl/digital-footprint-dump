
import os
import sys
import unittest
import tempfile
import sqlite3
from pathlib import Path

# Add repo root to sys.path so we can import src.readwise.database
sys.path.append(os.getcwd())

from src.database import BaseDatabase
from src.readwise.database import ReadwiseDatabase
from src.readwise.models import ALL_TABLES

class TestReadwiseDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_readwise.db")
        self.db = ReadwiseDatabase(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_connection_inheritance(self):
        """Test that ReadwiseDatabase inherits get_connection from BaseDatabase."""
        # Check if get_connection is defined in ReadwiseDatabase class
        # It should NOT be in ReadwiseDatabase.__dict__
        self.assertNotIn('get_connection', ReadwiseDatabase.__dict__,
                         "ReadwiseDatabase should not define get_connection, it should inherit it.")

        # Verify it resolves to BaseDatabase.get_connection
        self.assertEqual(ReadwiseDatabase.get_connection, BaseDatabase.get_connection)

    def test_connection_and_initialization(self):
        """Test that we can connect and initialize tables."""
        # This calls get_connection internally
        self.db.init_tables()

        # Verify tables exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            self.assertIn('books', tables)
            self.assertIn('highlights', tables)
            self.assertIn('documents', tables)

    def test_insert_and_retrieve(self):
        """Test basic operations to verify connection context manager works."""
        self.db.init_tables()

        # Test inserting a book using upsert_book which uses get_connection
        book = {
            "user_book_id": 12345,
            "title": "Test Book",
            "author": "Test Author",
            "source": "readwise",
            "category": "books",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        self.db.upsert_book(book)

        # Verify it was inserted
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM books WHERE user_book_id = ?", (12345,))
            row = cursor.fetchone()
            self.assertEqual(row['title'], "Test Book")

if __name__ == '__main__':
    unittest.main()
