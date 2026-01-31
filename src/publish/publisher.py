"""Publisher module for generating and committing monthly summaries."""

import logging
from typing import Dict, Any, Optional

from ..config import Config
from ..readwise.database import DatabaseManager
from .github_client import GitHubClient
from .markdown_generator import MarkdownGenerator

logger = logging.getLogger(__name__)


class Publisher:
    """Orchestrates the generation and publishing of monthly summaries."""
    
    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        github_client: Optional[GitHubClient] = None
    ):
        """Initialize publisher.
        
        Args:
            db: Database manager for reading analysis data.
            github_client: GitHub client for committing files.
        """
        self.db = db or DatabaseManager()
        self.github_client = github_client
        self.markdown_generator = MarkdownGenerator()
    
    def _get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the latest month's analysis from the database."""
        query = """
        SELECT year_month, year, month, articles, words, reading_time_mins
        FROM analysis
        ORDER BY year_month DESC
        LIMIT 1
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def publish(self) -> Dict[str, Any]:
        """Generate and publish the monthly summary.
        
        Returns:
            Dictionary with commit information.
        """
        # Get latest analysis
        analysis = self._get_latest_analysis()
        if not analysis:
            raise ValueError("No analysis data found. Run 'readwise-analyze' first.")
        
        logger.info(f"Publishing summary for {analysis['year']}-{analysis['month']}")
        
        # Prepare data for markdown generation
        data = {
            'year': analysis['year'],
            'month': analysis['month'],
            'readwise': {
                'articles': analysis['articles'],
                'words': analysis['words'],
                'reading_time_mins': analysis['reading_time_mins']
            }
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
        file_path = f"content/posts/{analysis['year']}-{analysis['month']}-monthly-summary.md"
        commit_message = f"feat: Add monthly summary draft for {analysis['month']}/{analysis['year']}"
        
        # Commit to GitHub
        result = self.github_client.create_or_update_file(
            file_path=file_path,
            content=markdown_content,
            commit_message=commit_message
        )
        
        logger.info(f"Published to {result['url']}")
        return result
