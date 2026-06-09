"""Analytics module for Oura Ring data.

Computes monthly min/median/avg/max for numeric columns
from daily_sleep and daily_readiness tables.
"""

import statistics
from collections import defaultdict
from typing import Optional, List, Tuple

from .database import OuraDatabase
from .models import CREATE_ANALYSIS_TABLE, ANALYSIS_INDEXES
from ..time_utils import utc_now_iso


# Numeric columns to aggregate from each source table.
# Text/id/timestamp/synced_at columns are excluded.
SLEEP_METRICS = [
    "score",
    "contributor_deep_sleep",
    "contributor_efficiency",
    "contributor_latency",
    "contributor_rem_sleep",
    "contributor_restfulness",
    "contributor_timing",
    "contributor_total_sleep",
]

READINESS_METRICS = [
    "score",
    "temperature_deviation",
    "temperature_trend_deviation",
    "contributor_activity_balance",
    "contributor_body_temperature",
    "contributor_hrv_balance",
    "contributor_previous_day_activity",
    "contributor_previous_night",
    "contributor_recovery_index",
    "contributor_resting_heart_rate",
    "contributor_sleep_balance",
    "contributor_sleep_regularity",
]

# Maps source table name → list of numeric columns to aggregate.
TABLE_METRICS = {
    "daily_sleep": SLEEP_METRICS,
    "daily_readiness": READINESS_METRICS,
}


class OuraAnalytics:
    """Analyzes Oura Ring daily data by month."""

    def __init__(self, db: Optional[OuraDatabase] = None):
        """Initialize analytics.

        Args:
            db: Database manager instance.
        """
        self.db = db or OuraDatabase()

    def _ensure_analysis_table(self) -> None:
        """Create the analysis table and indexes if they don't exist."""
        with self.db.get_connection() as conn:
            conn.execute(CREATE_ANALYSIS_TABLE)
            for index_sql in ANALYSIS_INDEXES:
                conn.execute(index_sql)

    def _collect_monthly_values(
        self, table: str, metrics: List[str]
    ) -> dict:
        """Query a daily table and bucket non-null values by (year_month, metric).

        Returns:
            dict mapping (year_month, metric) → list[float].
        """
        buckets: dict[Tuple[str, str], list] = defaultdict(list)

        cols = ", ".join(metrics)
        query = f"""
            SELECT strftime('%Y-%m', day) AS year_month, {cols}
            FROM {table}
            WHERE day IS NOT NULL
            ORDER BY day
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                ym = row["year_month"]
                if not ym:
                    continue
                for metric in metrics:
                    value = row[metric]
                    if value is not None:
                        buckets[(ym, metric)].append(float(value))

        return buckets

    def analyze_daily_summaries(self) -> int:
        """Compute monthly min/median/avg/max for sleep & readiness.

        Writes one row per (year_month, source_table, metric) into the
        analysis table.

        Returns:
            Total number of analysis rows written.
        """
        self._ensure_analysis_table()
        updated_at = utc_now_iso()
        total = 0

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            for table, metrics in TABLE_METRICS.items():
                buckets = self._collect_monthly_values(table, metrics)

                for (ym, metric), values in buckets.items():
                    if not values:
                        continue

                    cursor.execute(
                        """
                        INSERT INTO analysis
                            (year_month, source_table, metric,
                             min_value, median_value, avg_value, max_value,
                             sample_count, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(year_month, source_table, metric)
                        DO UPDATE SET
                            min_value      = excluded.min_value,
                            median_value   = excluded.median_value,
                            avg_value      = excluded.avg_value,
                            max_value      = excluded.max_value,
                            sample_count   = excluded.sample_count,
                            updated_at     = excluded.updated_at
                        """,
                        (
                            ym,
                            table,
                            metric,
                            min(values),
                            statistics.median(values),
                            round(statistics.mean(values), 2),
                            max(values),
                            len(values),
                            updated_at,
                        ),
                    )
                    total += 1

        return total
