"""Analytics module for Readwise data."""

import re
from collections import defaultdict
from datetime import datetime
from typing import Optional

from .database import ReadwiseDatabase


class ReadwiseAnalytics:
    """Analyzes Readwise data."""

    def __init__(self, db: Optional[ReadwiseDatabase] = None):
        """Initialize analytics.

        Args:
            db: Database manager instance.
        """
        self.db = db or ReadwiseDatabase()

    def _parse_reading_time(self, reading_time_str: str) -> int:
        """Extract minutes from reading time string."""
        if not reading_time_str:
            return 0
        match = re.search(r'(\d+)', str(reading_time_str))
        if match:
            return int(match.group(1))
        return 0

    def analyze_archived(self) -> int:
        """Analyze archived articles by month.

        Computes the number of articles, total words, and reading time
        for archived items each month. Writes the result to the analysis
        table in the database.

        Returns:
            Number of monthly records written to the database.
        """
        query = """
        SELECT
            strftime('%m', last_moved_at) as month,
            strftime('%Y', last_moved_at) as year,
            reading_time,
            word_count
        FROM documents
        WHERE location = 'archive' AND last_moved_at IS NOT NULL
        ORDER BY year DESC, month DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        # Aggregation
        stats = defaultdict(lambda: {
            'articles': 0,
            'words': 0,
            'reading_time_mins': 0
        })

        for row in rows:
            key = (row['year'], row['month'])

            stats[key]['articles'] += 1
            stats[key]['words'] += (row['word_count'] or 0)
            stats[key]['reading_time_mins'] += self._parse_reading_time(row['reading_time'])

        # Write to database
        updated_at = datetime.utcnow().isoformat() + "Z"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for (year, month), data in stats.items():
                year_month = f"{year}-{month}"
                cursor.execute("""
                    INSERT INTO analysis (year_month, year, month, articles, words, reading_time_mins, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year_month) DO UPDATE SET
                        articles = excluded.articles,
                        words = excluded.words,
                        reading_time_mins = excluded.reading_time_mins,
                        updated_at = excluded.updated_at
                """, (
                    year_month,
                    year,
                    month,
                    data['articles'],
                    data['words'],
                    data['reading_time_mins'],
                    updated_at
                ))

        return len(stats)
