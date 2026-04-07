"""Analytics module for blog post tracking."""

from typing import Optional

from ..time_utils import utc_now_iso
from .database import BlogDatabase
from .models import ANALYSIS_INDEXES, CREATE_ANALYSIS_TABLE


class BlogAnalytics:
    """Rolls up published blog posts into monthly analysis rows."""

    def __init__(self, db: Optional[BlogDatabase] = None):
        """Initialize analytics."""
        self.db = db or BlogDatabase()

    def _ensure_analysis_table(self) -> None:
        """Create the analysis table if it does not exist."""
        with self.db.get_connection() as conn:
            conn.execute(CREATE_ANALYSIS_TABLE)
            for index_sql in ANALYSIS_INDEXES:
                conn.execute(index_sql)

    def analyze_posts(self) -> int:
        """Aggregate posts by publish month."""
        self._ensure_analysis_table()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    strftime('%Y', published_at) AS year,
                    strftime('%m', published_at) AS month,
                    COUNT(*) AS posts,
                    COALESCE(SUM(word_count), 0) AS total_words
                FROM posts
                WHERE published_at IS NOT NULL
                GROUP BY year, month
                ORDER BY year ASC, month ASC
                """
            )
            rows = cursor.fetchall()
            updated_at = utc_now_iso()

            cursor.execute("DELETE FROM analysis")

            for row in rows:
                if not row["year"] or not row["month"]:
                    continue

                year_month = f"{row['year']}-{row['month']}"
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT pt.tag)
                    FROM post_tags pt
                    JOIN posts p ON p.permalink = pt.permalink
                    WHERE strftime('%Y-%m', p.published_at) = ?
                    """,
                    (year_month,),
                )
                unique_tags = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO analysis (
                        year_month, year, month, posts, total_words, unique_tags, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        year_month,
                        row["year"],
                        row["month"],
                        row["posts"] or 0,
                        row["total_words"] or 0,
                        unique_tags or 0,
                        updated_at,
                    ),
                )

        return len(rows)
