"""Analytics for GitHub activity data."""

from collections import defaultdict
from datetime import datetime
from typing import Optional

from .database import GitHubDatabase


class GitHubAnalytics:
    """Generates monthly analysis from GitHub commit data."""
    
    def __init__(self, db: Optional[GitHubDatabase] = None):
        """Initialize analytics.
        
        Args:
            db: Database manager instance.
        """
        self.db = db or GitHubDatabase()
    
    def analyze_commits(self) -> int:
        """Aggregate commits by month and write to analysis table.
        
        Groups commits by date_month and computes:
        - commits: count of commits
        - repos_touched: count of distinct repos
        
        Returns:
            Number of monthly records written.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT date_month, COUNT(*) as commits, COUNT(DISTINCT repo) as repos_touched
                FROM commits
                WHERE date_month IS NOT NULL AND date_month != ''
                GROUP BY date_month
                ORDER BY date_month
            """)
            rows = cursor.fetchall()
        
        now = datetime.utcnow().isoformat() + "Z"
        count = 0
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            for row in rows:
                year_month = row["date_month"]
                parts = year_month.split("-")
                if len(parts) != 2 or len(parts[0]) != 4:
                    continue
                
                year, month = parts
                
                cursor.execute("""
                    INSERT INTO analysis (year_month, year, month, commits, repos_touched, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year_month) DO UPDATE SET
                        commits = excluded.commits,
                        repos_touched = excluded.repos_touched,
                        updated_at = excluded.updated_at
                """, (year_month, year, month, row["commits"], row["repos_touched"], now))
                count += 1
        
        return count
