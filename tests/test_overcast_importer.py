
import os
import sys
import unittest
import tempfile
import sqlite3
from unittest.mock import patch
from pathlib import Path

# Add repo root to sys.path
sys.path.append(os.getcwd())

from src.overcast.importer import OvercastImporter

class TestOvercastImporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_overcast.db")

        # Patch Config.OVERCAST_DATABASE_PATH to use our temp DB
        self.config_patcher = patch('src.config.Config.OVERCAST_DATABASE_PATH', self.db_path)
        self.config_patcher.start()

        # Patch Config.FILES_DIR to use our temp dir
        self.files_patcher = patch('src.config.Config.FILES_DIR', Path(self.temp_dir.name))
        self.files_patcher.start()

        # Initialize DB with some data
        self.init_db()

        # Create importer instance
        self.importer = OvercastImporter()
        # Override db_path on importer instance too, just in case
        self.importer.db_path = Path(self.db_path)

    def tearDown(self):
        self.config_patcher.stop()
        self.files_patcher.stop()
        self.temp_dir.cleanup()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables as expected by OvercastImporter
        cursor.execute("CREATE TABLE IF NOT EXISTS feeds (id INTEGER PRIMARY KEY)")
        cursor.execute("CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY)")
        cursor.execute("CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY)")

        # Insert dummy data
        cursor.execute("INSERT INTO feeds (id) VALUES (1)")
        cursor.execute("INSERT INTO feeds (id) VALUES (2)")

        cursor.execute("INSERT INTO episodes (id) VALUES (1)")
        cursor.execute("INSERT INTO episodes (id) VALUES (2)")
        cursor.execute("INSERT INTO episodes (id) VALUES (3)")

        cursor.execute("INSERT INTO playlists (id) VALUES (1)")

        conn.commit()
        conn.close()

    def test_get_db_stats(self):
        """Test that get_db_stats returns correct counts using OvercastDatabase."""
        stats = self.importer.get_db_stats()

        self.assertEqual(stats['feeds'], 2)
        self.assertEqual(stats['episodes'], 3)
        self.assertEqual(stats['playlists'], 1)

if __name__ == '__main__':
    unittest.main()
