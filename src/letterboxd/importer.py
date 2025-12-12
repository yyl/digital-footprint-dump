"""Letterboxd CSV importer with auto-discovery."""

import csv
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..config import Config
from .database import LetterboxdDatabase


class LetterboxdImporter:
    """Imports Letterboxd data from CSV export files."""
    
    def __init__(self, db: Optional[LetterboxdDatabase] = None):
        """Initialize importer."""
        self.db = db or LetterboxdDatabase()
    
    @staticmethod
    def find_latest_export() -> Optional[Path]:
        """Find the latest Letterboxd export folder in files/.
        
        Scans for folders starting with 'letterboxd' and returns
        the one with the latest name (alphabetically/by date).
        """
        files_dir = Config.FILES_DIR
        if not files_dir.exists():
            return None
        
        letterboxd_folders = sorted([
            f for f in files_dir.iterdir()
            if f.is_dir() and f.name.startswith("letterboxd")
        ], reverse=True)  # Latest first (by name)
        
        return letterboxd_folders[0] if letterboxd_folders else None
    
    def import_from_directory(self, export_dir: Path) -> Dict[str, int]:
        """Import all CSV files from an export directory.
        
        Args:
            export_dir: Path to Letterboxd export folder
            
        Returns:
            Dictionary with import counts
        """
        stats = {"users": 0, "watched": 0, "ratings": 0}
        
        # Initialize database
        self.db.init_tables()
        
        # Import profile first (needed for FK)
        profile_path = export_dir / "profile.csv"
        username = None
        if profile_path.exists():
            username = self._import_profile(profile_path)
            if username:
                stats["users"] = 1
                print(f"Imported user: {username}")
        
        if not username:
            print("Error: Could not find username in profile.csv")
            return stats
        
        # Import watched
        watched_path = export_dir / "watched.csv"
        if watched_path.exists():
            stats["watched"] = self._import_watched(watched_path, username)
            print(f"Imported {stats['watched']} watched movies")
        
        # Import ratings
        ratings_path = export_dir / "ratings.csv"
        if ratings_path.exists():
            stats["ratings"] = self._import_ratings(ratings_path, username)
            print(f"Imported {stats['ratings']} ratings")
        
        return stats
    
    def _import_profile(self, csv_path: Path) -> Optional[str]:
        """Import profile.csv and return username."""
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if self.db.upsert_user(row):
                    return row.get("Username")
        return None
    
    def _import_watched(self, csv_path: Path, username: str) -> int:
        """Import watched.csv."""
        count = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if self.db.upsert_watched(row, username):
                    count += 1
        return count
    
    def _import_ratings(self, csv_path: Path, username: str) -> int:
        """Import ratings.csv."""
        count = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if self.db.upsert_rating(row, username):
                    count += 1
        return count
    
    def sync(self) -> Dict[str, int]:
        """Auto-discover latest export and import it.
        
        Returns:
            Dictionary with import counts
        """
        export_dir = self.find_latest_export()
        if not export_dir:
            print("Error: No Letterboxd export folder found in files/")
            print("  Expected: files/letterboxd-*")
            return {"users": 0, "watched": 0, "ratings": 0}
        
        print(f"Found export: {export_dir.name}")
        return self.import_from_directory(export_dir)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        try:
            self.db.init_tables()
            return {
                "database_stats": self.db.get_stats(),
                "latest_export": self.find_latest_export()
            }
        except Exception as e:
            return {"error": str(e)}
