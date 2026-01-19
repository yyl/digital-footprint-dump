"""Analytics module for Readwise data."""

import csv
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

    def analyze_archived(self) -> Path:
        """Analyze archived articles by month.

        Computes the number of articles and total words read (archived) each month.
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
            COUNT(*) as article_count,
            SUM(word_count) as total_words
        FROM documents
        WHERE location = 'archive' AND last_moved_at IS NOT NULL
        GROUP BY year, month
        ORDER BY year DESC, month DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['month', 'year', 'articles', 'words'])

            for row in rows:
                # Handle None word_count as 0
                total_words = row['total_words'] if row['total_words'] is not None else 0
                writer.writerow([
                    row['month'],
                    row['year'],
                    row['article_count'],
                    total_words
                ])

        return output_path
