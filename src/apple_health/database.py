"""SQLite database manager for Apple Health workout data."""

import sqlite3
from typing import Any, Dict, List, Optional

from ..config import Config
from ..database import BaseDatabase
from .models import RAW_TABLES, RAW_INDEXES


class AppleHealthDatabase(BaseDatabase):
    """Manages SQLite storage for Apple Health workouts."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        super().__init__(db_path or str(Config.APPLE_HEALTH_DATABASE_PATH))

    def init_tables(self) -> None:
        """Create raw sync tables if they do not exist."""
        is_new = not self.exists()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table_sql in RAW_TABLES:
                cursor.execute(table_sql)
            for index_sql in RAW_INDEXES:
                cursor.execute(index_sql)

        if is_new:
            print(f"Apple Health database initialized at: {self.db_path}")

    def save_workouts(self, workouts: List[Dict[str, Any]]) -> int:
        """Bulk upsert Apple Health workouts."""
        if not workouts:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO workouts (
                    id, activity_type, activity_type_raw, started_at, ended_at,
                    duration_seconds, active_calories, total_calories,
                    avg_heart_rate, max_heart_rate, source_name, source_version,
                    device, creation_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    activity_type = excluded.activity_type,
                    activity_type_raw = excluded.activity_type_raw,
                    started_at = excluded.started_at,
                    ended_at = excluded.ended_at,
                    duration_seconds = excluded.duration_seconds,
                    active_calories = excluded.active_calories,
                    total_calories = excluded.total_calories,
                    avg_heart_rate = excluded.avg_heart_rate,
                    max_heart_rate = excluded.max_heart_rate,
                    source_name = excluded.source_name,
                    source_version = excluded.source_version,
                    device = excluded.device,
                    creation_date = excluded.creation_date
                """,
                [
                    (
                        workout["id"],
                        workout["activity_type"],
                        workout["activity_type_raw"],
                        workout["started_at"],
                        workout["ended_at"],
                        workout["duration_seconds"],
                        workout.get("active_calories"),
                        workout.get("total_calories"),
                        workout.get("avg_heart_rate"),
                        workout.get("max_heart_rate"),
                        workout.get("source_name"),
                        workout.get("source_version"),
                        workout.get("device"),
                        workout.get("creation_date"),
                    )
                    for workout in workouts
                ],
            )
        return len(workouts)

    def get_stats(self) -> Dict[str, int]:
        """Get counts of stored workouts and analysis rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            cursor.execute("SELECT COUNT(*) FROM workouts")
            stats["workouts"] = cursor.fetchone()[0]
            try:
                cursor.execute("SELECT COUNT(*) FROM analysis")
                stats["analysis"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                pass
            return stats
