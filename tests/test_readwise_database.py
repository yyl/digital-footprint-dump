
import unittest
import sqlite3
import os
from src.readwise.database import ReadwiseDatabase

class TestReadwiseDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_readwise_db.sqlite"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = ReadwiseDatabase(db_path=self.db_path)
        self.db.init_tables()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_upsert_book_no_cursor(self):
        book = {
            "user_book_id": 1,
            "title": "Test Book",
            "author": "Test Author",
            "source": "kindle",
            "category": "books",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        self.db.upsert_book(book)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM books WHERE user_book_id = 1")
            row = cursor.fetchone()
            self.assertEqual(row[0], "Test Book")

    def test_upsert_book_with_cursor(self):
        book = {
            "user_book_id": 2,
            "title": "Test Book 2",
            "author": "Test Author 2",
            "source": "kindle",
            "category": "books",
            "updated_at": "2023-01-01T00:00:00Z"
        }

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            self.db.upsert_book(book, cursor=cursor)
            # Should be visible in same transaction
            cursor.execute("SELECT title FROM books WHERE user_book_id = 2")
            row = cursor.fetchone()
            self.assertEqual(row[0], "Test Book 2")

    def test_upsert_highlight_no_cursor(self):
        # Need a book first due to FK?
        # Check models.py: FOREIGN KEY (book_id) REFERENCES books(user_book_id)
        # So yes, need a book.
        book = {"user_book_id": 1}
        self.db.upsert_book(book)

        highlight = {
            "id": 100,
            "text": "Highlight text",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        self.db.upsert_highlight(highlight, book_id=1)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT text FROM highlights WHERE id = 100")
            row = cursor.fetchone()
            self.assertEqual(row[0], "Highlight text")

    def test_upsert_highlight_with_cursor(self):
        book = {"user_book_id": 2}

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            self.db.upsert_book(book, cursor=cursor)

            highlight = {
                "id": 200,
                "text": "Highlight text 2",
                "updated_at": "2023-01-01T00:00:00Z"
            }
            self.db.upsert_highlight(highlight, book_id=2, cursor=cursor)

            cursor.execute("SELECT text FROM highlights WHERE id = 200")
            row = cursor.fetchone()
            self.assertEqual(row[0], "Highlight text 2")

if __name__ == '__main__':
    unittest.main()
