"""Overcast OPML importer with auto-discovery."""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from ..config import Config
from .database import OvercastDatabase


class OvercastImporter:
    """Imports Overcast data from OPML export files."""
    
    def __init__(self):
        """Initialize importer."""
        self.db_path = Config.OVERCAST_DATABASE_PATH
        Config.ensure_data_dir()
    
    @staticmethod
    def find_latest_export() -> Optional[Path]:
        """Find the latest Overcast OPML export in files/.
        
        Scans for files matching 'overcast*.opml' pattern and returns
        the one with the latest modification time.
        """
        files_dir = Config.FILES_DIR
        if not files_dir.exists():
            return None
        
        opml_files = sorted(
            files_dir.glob("overcast*.opml"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        return opml_files[0] if opml_files else None
    
    def sync(self) -> Dict[str, int]:
        """Auto-discover latest export and import it.
        
        Returns:
            Dictionary with import counts
        """
        stats = {"feeds": 0, "episodes": 0, "playlists": 0}
        
        opml_file = self.find_latest_export()
        if not opml_file:
            print("Error: No Overcast OPML file found in files/")
            print("  Expected: files/overcast*.opml")
            return stats
        
        print(f"Found export: {opml_file.name}")
        
        # Run overcast-to-sqlite command
        try:
            result = subprocess.run(
                [
                    "overcast-to-sqlite", "save",
                    str(self.db_path),
                    "--load", str(opml_file),
                    "--no-archive"
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            print("Import complete!")
            
            # Get stats from database
            stats = self.get_db_stats()
            print(f"  feeds: {stats['feeds']}")
            print(f"  episodes: {stats['episodes']}")
            print(f"  playlists: {stats['playlists']}")
            
        except subprocess.TimeoutExpired:
            print("Error: overcast-to-sqlite timed out after 60 seconds")
        except subprocess.CalledProcessError as e:
            print(f"Error running overcast-to-sqlite: {e}")
            if e.stderr:
                print(f"  {e.stderr}")
        except FileNotFoundError:
            print("Error: overcast-to-sqlite not installed")
            print("  Run: uv sync")
        
        return stats
    
    def get_db_stats(self) -> Dict[str, int]:
        """Get counts from the database."""
        db = OvercastDatabase(str(self.db_path))
        return db.get_stats()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "database_stats": self.get_db_stats(),
            "latest_export": self.find_latest_export()
        }
