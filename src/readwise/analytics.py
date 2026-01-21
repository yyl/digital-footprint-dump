"""Analytics module for Readwise data."""

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .database import DatabaseManager
from ..config import Config


class ReadwiseAnalytics:
    """Analyzes Readwise data."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        """Initialize analytics.

        Args:
            db: Database manager instance.
        """
        self.db = db or DatabaseManager()

    def _parse_reading_time(self, reading_time_str: str) -> int:
        """Extract minutes from reading time string."""
        if not reading_time_str:
            return 0
        match = re.search(r'(\d+)', str(reading_time_str))
        if match:
            return int(match.group(1))
        return 0

    def analyze_archived(self) -> Path:
        """Analyze archived articles by month.

        Computes the number of articles, total words, reading time,
        location counts, and site counts for archived items each month.
        Writes the result to a CSV file.

        Returns:
            Path to the generated CSV file.
        """
        output_path = Config.DATA_DIR / "readwise_analysis.csv"
        Config.ensure_data_dir()

        query = """
        SELECT
            strftime('%m', last_moved_at) as month,
            strftime('%Y', last_moved_at) as year,
            location,
            site_name,
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
            'reading_time_mins': 0,
            'locations': defaultdict(int),
            'sites': defaultdict(int)
        })

        for row in rows:
            key = (row['year'], row['month'])

            stats[key]['articles'] += 1
            stats[key]['words'] += (row['word_count'] or 0)
            stats[key]['reading_time_mins'] += self._parse_reading_time(row['reading_time'])

            loc = row['location'] or 'unknown'
            stats[key]['locations'][loc] += 1

            site = row['site_name'] or 'unknown'
            stats[key]['sites'][site] += 1

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['month', 'year', 'articles', 'words', 'reading_time_mins', 'location_counts', 'site_counts'])

            # Sort by year desc, month desc
            sorted_keys = sorted(stats.keys(), key=lambda x: (x[0], x[1]), reverse=True)

            for year, month in sorted_keys:
                data = stats[(year, month)]
                writer.writerow([
                    month,
                    year,
                    data['articles'],
                    data['words'],
                    data['reading_time_mins'],
                    dict(data['locations']),
                    dict(data['sites'])
                ])

        return output_path
