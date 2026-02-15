"""Analytics module for Strong workout data."""

from collections import defaultdict
from datetime import datetime
from typing import Optional, Dict, Any

from .database import StrongDatabase
from .models import CREATE_ANALYSIS_TABLE, CREATE_INDEXES


class StrongAnalytics:
    """Analyzes Strong workout data."""

    def __init__(self, db: Optional[StrongDatabase] = None):
        """Initialize analytics.

        Args:
            db: Database manager instance.
        """
        self.db = db or StrongDatabase()

    def _ensure_analysis_table(self) -> None:
        """Create analysis table if it doesn't exist."""
        with self.db.get_connection() as conn:
            conn.execute(CREATE_ANALYSIS_TABLE)
            for index_sql in CREATE_INDEXES:
                conn.execute(index_sql)

    def analyze_workouts(self) -> int:
        """Analyze workout activity by month.

        Computes workout count, total minutes, unique exercises, and total
        sets for each month. Writes results to the analysis table.

        Returns:
            Number of monthly records written to the database.
        """
        self._ensure_analysis_table()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get workout counts and total minutes by month
            workout_stats: Dict[tuple, Dict[str, Any]] = defaultdict(
                lambda: {"workouts": 0, "total_minutes": 0}
            )
            cursor.execute("""
                SELECT
                    strftime('%Y', started_at) as year,
                    strftime('%m', started_at) as month,
                    COUNT(*) as cnt,
                    SUM(duration_minutes) as total_mins
                FROM workouts
                WHERE started_at IS NOT NULL
                GROUP BY year, month
            """)
            for row in cursor.fetchall():
                if row['year'] and row['month']:
                    key = (row['year'], row['month'])
                    workout_stats[key]['workouts'] = row['cnt']
                    workout_stats[key]['total_minutes'] = row['total_mins'] or 0

            # Get unique exercises and total sets by month
            exercise_stats: Dict[tuple, Dict[str, int]] = defaultdict(
                lambda: {"unique_exercises": 0, "total_sets": 0}
            )
            cursor.execute("""
                SELECT
                    strftime('%Y', w.started_at) as year,
                    strftime('%m', w.started_at) as month,
                    COUNT(DISTINCT e.exercise_name) as unique_ex,
                    COUNT(*) as total_sets
                FROM exercises e
                JOIN workouts w ON e.workout_id = w.id
                WHERE w.started_at IS NOT NULL
                GROUP BY year, month
            """)
            for row in cursor.fetchall():
                if row['year'] and row['month']:
                    key = (row['year'], row['month'])
                    exercise_stats[key]['unique_exercises'] = row['unique_ex']
                    exercise_stats[key]['total_sets'] = row['total_sets']

            # Merge all months
            all_months = set(workout_stats.keys()) | set(exercise_stats.keys())

            # Write to database
            updated_at = datetime.utcnow().isoformat() + "Z"

            for year, month in all_months:
                year_month = f"{year}-{month}"
                ws = workout_stats[(year, month)]
                es = exercise_stats[(year, month)]

                cursor.execute("""
                    INSERT INTO analysis (year_month, year, month, workouts, total_minutes, unique_exercises, total_sets, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year_month) DO UPDATE SET
                        workouts = excluded.workouts,
                        total_minutes = excluded.total_minutes,
                        unique_exercises = excluded.unique_exercises,
                        total_sets = excluded.total_sets,
                        updated_at = excluded.updated_at
                """, (
                    year_month,
                    year,
                    month,
                    ws['workouts'],
                    ws['total_minutes'],
                    es['unique_exercises'],
                    es['total_sets'],
                    updated_at
                ))

        return len(all_months)
