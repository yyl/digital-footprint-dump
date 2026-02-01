"""Publisher module for generating and committing monthly summaries."""

import logging
from typing import Dict, Any, Optional

from ..config import Config
from ..readwise.database import DatabaseManager
from ..letterboxd.database import LetterboxdDatabase
from ..overcast.database import OvercastDatabase
from .github_client import GitHubClient
from .markdown_generator import MarkdownGenerator

logger = logging.getLogger(__name__)


class Publisher:
    """Orchestrates the generation and publishing of monthly summaries."""
    
    def __init__(
        self,
        readwise_db: Optional[DatabaseManager] = None,
        letterboxd_db: Optional[LetterboxdDatabase] = None,
        overcast_db: Optional[OvercastDatabase] = None,
        github_client: Optional[GitHubClient] = None
    ):
        """Initialize publisher.
        
        Args:
            readwise_db: Readwise database manager for reading analysis data.
            letterboxd_db: Letterboxd database manager.
            overcast_db: Overcast database manager.
            github_client: GitHub client for committing files.
        """
        self.readwise_db = readwise_db or DatabaseManager()
        self.letterboxd_db = letterboxd_db or LetterboxdDatabase()
        self.overcast_db = overcast_db or OvercastDatabase()
        self.github_client = github_client
        self.markdown_generator = MarkdownGenerator()
    
    def _get_readwise_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Readwise analysis for a specific month."""
        query = """
        SELECT year_month, year, month, articles, words, reading_time_mins
        FROM analysis
        WHERE year_month = ?
        """
        
        with self.readwise_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (year_month,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def _get_letterboxd_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Letterboxd analysis for a specific month."""
        query = """
        SELECT year_month, year, month, movies_watched, avg_rating, min_rating, max_rating, avg_years_since_release
        FROM analysis
        WHERE year_month = ?
        """
        
        with self.letterboxd_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (year_month,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def _get_overcast_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Overcast analysis for a specific month."""
        if not self.overcast_db.exists():
            return None
        
        query = """
        SELECT year_month, year, month, feeds_added, feeds_removed, episodes_played
        FROM analysis
        WHERE year_month = ?
        """
        
        try:
            with self.overcast_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (year_month,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
        except Exception:
            pass
        return None
    
    def _get_latest_year_month(self) -> Optional[str]:
        """Get the latest year_month from any analysis source."""
        # Check Readwise first
        with self.readwise_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT year_month FROM analysis ORDER BY year_month DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row['year_month']
        
        # Check Letterboxd
        with self.letterboxd_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT year_month FROM analysis ORDER BY year_month DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row['year_month']
        
        return None
    
    def publish(self) -> Dict[str, Any]:
        """Generate and publish the monthly summary.
        
        Returns:
            Dictionary with commit information.
        """
        # Get latest year_month
        year_month = self._get_latest_year_month()
        if not year_month:
            raise ValueError("No analysis data found. Run 'analyze' first.")
        
        year, month = year_month.split('-')
        logger.info(f"Publishing summary for {year_month}")
        
        # Prepare data for markdown generation
        data = {
            'year': year,
            'month': month,
        }
        
        # Get Readwise analysis
        readwise = self._get_readwise_analysis(year_month)
        if readwise:
            data['readwise'] = {
                'articles': readwise['articles'],
                'words': readwise['words'],
                'reading_time_mins': readwise['reading_time_mins']
            }
        
        # Get Letterboxd analysis
        letterboxd = self._get_letterboxd_analysis(year_month)
        if letterboxd:
            data['letterboxd'] = {
                'movies_watched': letterboxd['movies_watched'],
                'avg_rating': letterboxd['avg_rating'],
                'min_rating': letterboxd['min_rating'],
                'max_rating': letterboxd['max_rating'],
                'avg_years_since_release': letterboxd['avg_years_since_release']
            }
        
        # Get Overcast analysis
        overcast = self._get_overcast_analysis(year_month)
        if overcast:
            data['overcast'] = {
                'feeds_added': overcast['feeds_added'],
                'feeds_removed': overcast['feeds_removed'],
                'episodes_played': overcast['episodes_played']
            }
        
        # Generate markdown
        markdown_content = self.markdown_generator.generate_monthly_summary(data)
        
        # Initialize GitHub client if not provided
        if not self.github_client:
            Config.validate_github()
            self.github_client = GitHubClient(
                token=Config.GITHUB_TOKEN,
                repo_owner=Config.GITHUB_REPO_OWNER,
                repo_name=Config.GITHUB_REPO_NAME,
                target_branch=Config.GITHUB_TARGET_BRANCH
            )
        
        # Create file path
        file_path = f"content/posts/{year}-{month}-monthly-summary.md"
        commit_message = f"feat: Add monthly summary draft for {month}/{year}"
        
        # Commit to GitHub
        result = self.github_client.create_or_update_file(
            file_path=file_path,
            content=markdown_content,
            commit_message=commit_message
        )
        
        logger.info(f"Published to {result['url']}")
        return result

