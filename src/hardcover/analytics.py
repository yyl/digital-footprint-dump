"""Analytics for Hardcover book data."""

from collections import defaultdict
from typing import Optional

from .database import HardcoverDatabase
from . import models
from ..time_utils import utc_now_iso


class HardcoverAnalytics:
    """Generates monthly analysis from Hardcover book data."""
    
    def __init__(self, db: Optional[HardcoverDatabase] = None):
        """Initialize analytics.
        
        Args:
            db: Database manager instance.
        """
        self.db = db or HardcoverDatabase()

    def _ensure_analysis_table(self) -> None:
        """Create analysis table if it doesn't exist."""
        with self.db.get_connection() as conn:
            conn.execute(models.CREATE_ANALYSIS_TABLE)
    
    def analyze_books(self) -> int:
        """Aggregate books by month and write to analysis table.
        
        Groups books by the date_read field (YYYY-MM) and computes:
        - books_finished: count of books
        - avg_rating: average rating (excluding unrated books)
        
        Returns:
            Number of monthly records written.
        """
        self._ensure_analysis_table()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch all books with date_read
            cursor.execute("""
                SELECT date_read, rating
                FROM books
                WHERE date_read IS NOT NULL
            """)
            rows = cursor.fetchall()
        
        # Group by year-month
        monthly: dict = defaultdict(lambda: {"count": 0, "ratings": []})
        
        for row in rows:
            date_str = row["date_read"]
            try:
                # Handle various date formats — extract YYYY-MM
                if len(date_str) >= 10:
                    year_month = date_str[:7]  # e.g. "2025-04"
                elif len(date_str) >= 7:
                    year_month = date_str[:7]
                else:
                    continue
                
                # Validate format
                parts = year_month.split("-")
                if len(parts) != 2 or len(parts[0]) != 4:
                    continue
                    
            except (ValueError, TypeError):
                continue
            
            monthly[year_month]["count"] += 1
            if row["rating"] is not None:
                monthly[year_month]["ratings"].append(row["rating"])
        
        # Write to analysis table
        now = utc_now_iso()
        count = 0
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            for year_month, data in sorted(monthly.items()):
                year, month = year_month.split("-")
                ratings = data["ratings"]
                avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
                
                cursor.execute("""
                    INSERT INTO analysis (year_month, year, month, books_finished, avg_rating, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year_month) DO UPDATE SET
                        books_finished = excluded.books_finished,
                        avg_rating = excluded.avg_rating,
                        updated_at = excluded.updated_at
                """, (year_month, year, month, data["count"], avg_rating, now))
                count += 1
        
        return count
