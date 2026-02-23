"""SQLite database manager for Strong workout data."""

import sqlite3
from typing import Optional, Dict, Any

from ..config import Config
from ..database import BaseDatabase
from .models import ALL_TABLES, CREATE_INDEXES


class StrongDatabase(BaseDatabase):
    """Manages SQLite database for Strong workout data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        super().__init__(db_path or str(Config.STRONG_DATABASE_PATH))
        self.use_foreign_keys = True
    
    def init_tables(self) -> None:
        """Create all tables if they don't exist."""
        is_new = not self.exists()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table_sql in ALL_TABLES:
                cursor.execute(table_sql)
            for index_sql in CREATE_INDEXES:
                cursor.execute(index_sql)
        
        if is_new:
            print(f"Strong database initialized at: {self.db_path}")
    
    def upsert_workout(self, workout_data: Dict[str, Any]) -> bool:
        """Insert or update a workout session."""
        workout_id = workout_data.get("id")
        if not workout_id:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workouts (
                    id, workout_name, started_at, duration_minutes, notes
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    workout_name = excluded.workout_name,
                    started_at = excluded.started_at,
                    duration_minutes = excluded.duration_minutes,
                    notes = excluded.notes
            """, (
                workout_id,
                workout_data.get("workout_name"),
                workout_data.get("started_at"),
                workout_data.get("duration_minutes", 0),
                workout_data.get("notes"),
            ))
            return True
    
    def insert_exercises(self, workout_id: str, exercises: list) -> int:
        """Insert exercise sets for a workout, replacing any existing ones."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Remove existing exercises for this workout (full re-import)
            cursor.execute("DELETE FROM exercises WHERE workout_id = ?", (workout_id,))
            
            count = 0
            for ex in exercises:
                cursor.execute("""
                    INSERT INTO exercises (
                        workout_id, exercise_name, set_order,
                        weight, reps, distance, seconds, notes, rpe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workout_id,
                    ex.get("exercise_name"),
                    ex.get("set_order"),
                    ex.get("weight", 0),
                    ex.get("reps", 0),
                    ex.get("distance", 0),
                    ex.get("seconds", 0),
                    ex.get("notes"),
                    ex.get("rpe"),
                ))
                count += 1
            return count
    
    def get_stats(self) -> Dict[str, int]:
        """Get counts of all entities."""
        stats = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table in ["workouts", "exercises"]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
        return stats
