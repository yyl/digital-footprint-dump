import os
import sqlite3
import unittest
import sys
from unittest.mock import MagicMock

# Mock missing dependencies before importing src
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['github'] = MagicMock()

from src.overcast.database import OvercastDatabase

class TestOvercastDatabaseStats(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_overcast.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        # Mocking Config.OVERCAST_DATABASE_PATH to avoid it failing if not set
        with unittest.mock.patch('src.overcast.database.Config') as mock_config:
            mock_config.OVERCAST_DATABASE_PATH = self.db_path
            self.db = OvercastDatabase(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_stats_empty_db(self):
        # Even if the file exists, if tables aren't there, it should return 0s
        with sqlite3.connect(self.db_path) as conn:
            pass

        stats = self.db.get_stats()
        self.assertEqual(stats, {"feeds": 0, "episodes": 0, "playlists": 0})

    def test_get_stats_with_some_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE feeds (id TEXT)")
            cursor.execute("INSERT INTO feeds VALUES ('1'), ('2')")
            cursor.execute("CREATE TABLE episodes (id TEXT)")
            cursor.execute("INSERT INTO episodes VALUES ('a'), ('b'), ('c')")
            # playlists table is missing

        stats = self.db.get_stats()
        self.assertEqual(stats, {"feeds": 2, "episodes": 3, "playlists": 0})

    def test_get_stats_all_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE feeds (id TEXT)")
            cursor.execute("INSERT INTO feeds VALUES ('1')")
            cursor.execute("CREATE TABLE episodes (id TEXT)")
            cursor.execute("INSERT INTO episodes VALUES ('a'), ('b')")
            cursor.execute("CREATE TABLE playlists (id TEXT)")
            cursor.execute("INSERT INTO playlists VALUES ('p1'), ('p2'), ('p3')")

        stats = self.db.get_stats()
        self.assertEqual(stats, {"feeds": 1, "episodes": 2, "playlists": 3})

if __name__ == "__main__":
    unittest.main()
