"""Analytics module for Foursquare data."""

from collections import defaultdict
from datetime import datetime
from typing import Optional, Dict, Any

from .database import FoursquareDatabase


class FoursquareAnalytics:
    """Analyzes Foursquare checkin data."""

    def __init__(self, db: Optional[FoursquareDatabase] = None):
        """Initialize analytics.

        Args:
            db: Database manager instance.
        """
        self.db = db or FoursquareDatabase()

    def analyze_checkins(self) -> int:
        """Analyze checkin activity by month.

        Computes number of checkins and unique places visited
        for each month. Writes results to the analysis table.

        Returns:
            Number of monthly records written to the database.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get checkins grouped by month with unique place count
            cursor.execute("""
                SELECT 
                    strftime('%Y', created_at, 'unixepoch') as year,
                    strftime('%m', created_at, 'unixepoch') as month,
                    COUNT(*) as checkins,
                    COUNT(DISTINCT place_fsq_id) as unique_places
                FROM checkins
                GROUP BY year, month
                ORDER BY year DESC, month DESC
            """)
            
            rows = cursor.fetchall()
            
            # Write to database
            updated_at = datetime.utcnow().isoformat() + "Z"
            
            for row in rows:
                year = row['year']
                month = row['month']
                year_month = f"{year}-{month}"
                
                cursor.execute("""
                    INSERT INTO analysis (year_month, year, month, checkins, unique_places, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year_month) DO UPDATE SET
                        checkins = excluded.checkins,
                        unique_places = excluded.unique_places,
                        updated_at = excluded.updated_at
                """, (
                    year_month,
                    year,
                    month,
                    row['checkins'],
                    row['unique_places'],
                    updated_at
                ))
        
        return len(rows)
