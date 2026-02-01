"""Analytics module for Overcast podcast data."""

from collections import defaultdict
from datetime import datetime
from typing import Optional, Dict, Any

from .database import OvercastDatabase
from .models import CREATE_ANALYSIS_TABLE, CREATE_INDEXES


class OvercastAnalytics:
    """Analyzes Overcast podcast data."""

    def __init__(self, db: Optional[OvercastDatabase] = None):
        """Initialize analytics.

        Args:
            db: Database manager instance.
        """
        self.db = db or OvercastDatabase()

    def _ensure_analysis_table(self) -> None:
        """Create analysis table if it doesn't exist."""
        with self.db.get_connection() as conn:
            conn.execute(CREATE_ANALYSIS_TABLE)
            for index_sql in CREATE_INDEXES:
                conn.execute(index_sql)

    def analyze_podcasts(self) -> int:
        """Analyze podcast activity by month.

        Computes new feeds subscribed, feeds removed, and episodes played
        for each month. Writes results to the analysis table.

        Returns:
            Number of monthly records written to the database.
        """
        # Ensure analysis table exists
        self._ensure_analysis_table()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get feeds added by month (using overcastAddedDate)
            feeds_added: Dict[tuple, int] = defaultdict(int)
            cursor.execute("""
                SELECT 
                    strftime('%Y', overcastAddedDate) as year,
                    strftime('%m', overcastAddedDate) as month
                FROM feeds
                WHERE overcastAddedDate IS NOT NULL
            """)
            for row in cursor.fetchall():
                if row['year'] and row['month']:
                    feeds_added[(row['year'], row['month'])] += 1
            
            # Get feeds removed by month (using dateRemoveDetected)
            feeds_removed: Dict[tuple, int] = defaultdict(int)
            cursor.execute("""
                SELECT 
                    strftime('%Y', dateRemoveDetected) as year,
                    strftime('%m', dateRemoveDetected) as month
                FROM feeds
                WHERE dateRemoveDetected IS NOT NULL
            """)
            for row in cursor.fetchall():
                if row['year'] and row['month']:
                    feeds_removed[(row['year'], row['month'])] += 1
            
            # Get episodes played by month (using userUpdatedDate for played episodes)
            episodes_played: Dict[tuple, int] = defaultdict(int)
            cursor.execute("""
                SELECT 
                    strftime('%Y', userUpdatedDate) as year,
                    strftime('%m', userUpdatedDate) as month
                FROM episodes
                WHERE played = 1 AND userUpdatedDate IS NOT NULL
            """)
            for row in cursor.fetchall():
                if row['year'] and row['month']:
                    episodes_played[(row['year'], row['month'])] += 1
            
            # Merge all months
            all_months = set(feeds_added.keys()) | set(feeds_removed.keys()) | set(episodes_played.keys())
            
            # Write to database
            updated_at = datetime.utcnow().isoformat() + "Z"
            
            for year, month in all_months:
                year_month = f"{year}-{month}"
                
                cursor.execute("""
                    INSERT INTO analysis (year_month, year, month, feeds_added, feeds_removed, episodes_played, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year_month) DO UPDATE SET
                        feeds_added = excluded.feeds_added,
                        feeds_removed = excluded.feeds_removed,
                        episodes_played = excluded.episodes_played,
                        updated_at = excluded.updated_at
                """, (
                    year_month,
                    year,
                    month,
                    feeds_added[(year, month)],
                    feeds_removed[(year, month)],
                    episodes_played[(year, month)],
                    updated_at
                ))
        
        return len(all_months)
