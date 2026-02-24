"""Database manager for GitHub activity data."""

from typing import Optional, Dict, Any, List

from ..config import Config
from ..database import BaseDatabase
from . import models


class GitHubDatabase(BaseDatabase):
    """SQLite database manager for GitHub commits."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database. Defaults to config value.
        """
        super().__init__(str(db_path or Config.GITHUB_DATABASE_PATH))
    
    def init_tables(self) -> None:
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(models.CREATE_COMMITS_TABLE)
            cursor.execute(models.CREATE_ANALYSIS_TABLE)
        print(f"GitHub database initialized at: {self.db_path}")
    
    def upsert_commit(self, commit: Dict[str, Any]) -> None:
        """Insert or update a commit.
        
        Args:
            commit: Dictionary with sha, repo, message, author_date, date_month.
        """
        self.upsert_commits([commit])

    def upsert_commits(self, commits: List[Dict[str, Any]]) -> None:
        """Insert or update multiple commits.

        Args:
            commits: List of dictionaries with sha, repo, message, author_date, date_month.
        """
        if not commits:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO commits (sha, repo, message, author_date, date_month)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(sha) DO UPDATE SET
                    repo = excluded.repo,
                    message = excluded.message,
                    author_date = excluded.author_date,
                    date_month = excluded.date_month
            """, [
                (
                    c["sha"],
                    c["repo"],
                    c.get("message"),
                    c["author_date"],
                    c["date_month"],
                ) for c in commits
            ])
    
    def get_latest_commit_date(self, repo: str) -> Optional[str]:
        """Get the latest commit date for a repo (for incremental sync).
        
        Args:
            repo: Repository in owner/name format.
            
        Returns:
            ISO timestamp of latest commit, or None.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(author_date) FROM commits WHERE repo = ?",
                (repo,)
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM commits")
            commits_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT repo) FROM commits")
            repos_count = cursor.fetchone()[0]
            
            return {
                "commits": commits_count,
                "repos": repos_count,
            }
