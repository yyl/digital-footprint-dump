"""Publisher module for generating and committing monthly summaries."""

import logging
from typing import Dict, Any, Optional

from ..config import Config
from ..comparison import compute_comparisons
from ..readwise.database import ReadwiseDatabase
from ..foursquare.database import FoursquareDatabase
from ..letterboxd.database import LetterboxdDatabase
from ..overcast.database import OvercastDatabase
from .github_client import GitHubClient
from .markdown_generator import MarkdownGenerator
from .data_generator import DataGenerator

logger = logging.getLogger(__name__)


class Publisher:
    """Orchestrates the generation and publishing of monthly summaries."""
    
    def __init__(
        self,
        readwise_db: Optional[ReadwiseDatabase] = None,
        foursquare_db: Optional[FoursquareDatabase] = None,
        letterboxd_db: Optional[LetterboxdDatabase] = None,
        overcast_db: Optional[OvercastDatabase] = None,
        github_client: Optional[GitHubClient] = None
    ):
        """Initialize publisher.
        
        Args:
            readwise_db: Readwise database manager for reading analysis data.
            foursquare_db: Foursquare database manager.
            letterboxd_db: Letterboxd database manager.
            overcast_db: Overcast database manager.
            github_client: GitHub client for committing files.
        """
        self.readwise_db = readwise_db or ReadwiseDatabase()
        self.foursquare_db = foursquare_db or FoursquareDatabase()
        self.letterboxd_db = letterboxd_db or LetterboxdDatabase()
        self.overcast_db = overcast_db or OvercastDatabase()
        self.github_client = github_client
        self.markdown_generator = MarkdownGenerator()
        self.data_generator = DataGenerator(
            readwise_db=self.readwise_db,
            foursquare_db=self.foursquare_db,
            letterboxd_db=self.letterboxd_db,
            overcast_db=self.overcast_db,
        )
    
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
    
    def _get_foursquare_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Foursquare analysis for a specific month."""
        query = """
        SELECT year_month, year, month, checkins, unique_places
        FROM analysis
        WHERE year_month = ?
        """
        
        try:
            with self.foursquare_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (year_month,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
        except Exception:
            pass
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
    
    def _ensure_github_client(self):
        """Initialize GitHub client if not already provided."""
        if not self.github_client:
            Config.validate_github()
            self.github_client = GitHubClient(
                token=Config.BLOG_GITHUB_TOKEN,
                repo_owner=Config.BLOG_REPO_OWNER,
                repo_name=Config.BLOG_REPO_NAME,
                target_branch=Config.BLOG_GITHUB_TARGET_BRANCH
            )
    
    def publish(self) -> Dict[str, Any]:
        """Generate and publish the monthly summary blog post.
        
        Returns:
            Dictionary with commit information.
        """
        # Get latest year_month
        year_month = self._get_latest_year_month()
        if not year_month:
            raise ValueError("No analysis data found. Run 'analyze' first.")
        
        year, month = year_month.split('-')
        logger.info(f"Publishing summary for {year_month}")
        
        # Generate markdown using shared method
        markdown_content = self.generate_markdown(year_month)
        
        self._ensure_github_client()
        
        # Commit blog post
        file_path = f"content/posts/{year}-{month}-monthly-summary.md"
        commit_message = f"feat: Add monthly summary draft for {month}/{year}"
        
        result = self.github_client.create_or_update_files(
            files={file_path: markdown_content},
            commit_message=commit_message
        )
        
        logger.info(f"Published to {result['url']}")
        return result
    
    def backfill(self) -> Dict[str, Any]:
        """Generate and commit Hugo data files from all analysis data.
        
        Returns:
            Dictionary with commit information.
        """
        # Generate Hugo data files
        data_files = self.data_generator.generate_data_files()
        
        if not data_files:
            raise ValueError("No analysis data found. Run 'analyze' first.")
        
        logger.info(f"Generated {len(data_files)} data files")
        
        self._ensure_github_client()
        
        # Commit data files
        commit_message = "data: Update activity data files"
        
        result = self.github_client.create_or_update_files(
            files=data_files,
            commit_message=commit_message
        )
        
        logger.info(f"Backfilled data to {result['url']}")
        return result
    
    def generate_markdown(self, year_month: Optional[str] = None) -> str:
        """Generate markdown content for a monthly summary.
        
        Args:
            year_month: Period to generate for (YYYY-MM format). Defaults to latest.
            
        Returns:
            Generated markdown content as string.
        """
        if not year_month:
            year_month = self._get_latest_year_month()
        
        if not year_month:
            raise ValueError("No analysis data found. Run 'analyze' first.")
        
        year, month = year_month.split('-')
        
        # Prepare data for markdown generation
        data = {
            'year': year,
            'month': month,
        }
        
        # Get Readwise analysis
        readwise = self._get_readwise_analysis(year_month)
        if readwise:
            readwise_comparisons = compute_comparisons(
                current_stats=readwise,
                historical_getter=self._get_readwise_analysis,
                year_month=year_month,
                metrics=['articles', 'words', 'reading_time_mins']
            )
            data['readwise'] = {
                'articles': readwise['articles'],
                'words': readwise['words'],
                'reading_time_mins': readwise['reading_time_mins'],
                'comparisons': readwise_comparisons
            }
        
        # Get Foursquare analysis
        foursquare = self._get_foursquare_analysis(year_month)
        if foursquare:
            foursquare_comparisons = compute_comparisons(
                current_stats=foursquare,
                historical_getter=self._get_foursquare_analysis,
                year_month=year_month,
                metrics=['checkins', 'unique_places']
            )
            data['foursquare'] = {
                'checkins': foursquare['checkins'],
                'unique_places': foursquare['unique_places'],
                'comparisons': foursquare_comparisons
            }
        
        # Get Letterboxd analysis
        letterboxd = self._get_letterboxd_analysis(year_month)
        if letterboxd:
            letterboxd_comparisons = compute_comparisons(
                current_stats=letterboxd,
                historical_getter=self._get_letterboxd_analysis,
                year_month=year_month,
                metrics=['movies_watched', 'avg_rating']
            )
            data['letterboxd'] = {
                'movies_watched': letterboxd['movies_watched'],
                'avg_rating': letterboxd['avg_rating'],
                'min_rating': letterboxd['min_rating'],
                'max_rating': letterboxd['max_rating'],
                'avg_years_since_release': letterboxd['avg_years_since_release'],
                'comparisons': letterboxd_comparisons
            }
        
        # Get Overcast analysis
        overcast = self._get_overcast_analysis(year_month)
        if overcast:
            overcast_comparisons = compute_comparisons(
                current_stats=overcast,
                historical_getter=self._get_overcast_analysis,
                year_month=year_month,
                metrics=['episodes_played']
            )
            data['overcast'] = {
                'feeds_added': overcast['feeds_added'],
                'feeds_removed': overcast['feeds_removed'],
                'episodes_played': overcast['episodes_played'],
                'comparisons': overcast_comparisons
            }
        
        return self.markdown_generator.generate_monthly_summary(data)

