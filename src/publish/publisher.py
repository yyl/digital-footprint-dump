"""Publisher module for generating and committing monthly summaries."""

import logging
import re
from typing import Dict, Any, Optional, List

from ..config import Config
from ..comparison import compute_comparisons
from ..readwise.database import ReadwiseDatabase
from ..foursquare.database import FoursquareDatabase
from ..letterboxd.database import LetterboxdDatabase
from ..overcast.database import OvercastDatabase
from ..strong.database import StrongDatabase
from ..hardcover.database import HardcoverDatabase
from ..github.database import GitHubDatabase
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
        strong_db: Optional[StrongDatabase] = None,
        hardcover_db: Optional[HardcoverDatabase] = None,
        github_activity_db: Optional[GitHubDatabase] = None,
        github_client: Optional[GitHubClient] = None
    ):
        """Initialize publisher.
        
        Args:
            readwise_db: Readwise database manager for reading analysis data.
            foursquare_db: Foursquare database manager.
            letterboxd_db: Letterboxd database manager.
            overcast_db: Overcast database manager.
            strong_db: Strong database manager.
            hardcover_db: Hardcover database manager.
            github_activity_db: GitHub activity database manager.
            github_client: GitHub client for committing files.
        """
        self.readwise_db = readwise_db or ReadwiseDatabase()
        self.foursquare_db = foursquare_db or FoursquareDatabase()
        self.letterboxd_db = letterboxd_db or LetterboxdDatabase()
        self.overcast_db = overcast_db or OvercastDatabase()
        self.strong_db = strong_db or StrongDatabase()
        self.hardcover_db = hardcover_db or HardcoverDatabase()
        self.github_activity_db = github_activity_db or GitHubDatabase()
        self.github_client = github_client
        self.markdown_generator = MarkdownGenerator()
        self.data_generator = DataGenerator(
            readwise_db=self.readwise_db,
            foursquare_db=self.foursquare_db,
            letterboxd_db=self.letterboxd_db,
            overcast_db=self.overcast_db,
            strong_db=self.strong_db,
            hardcover_db=self.hardcover_db,
            github_activity_db=self.github_activity_db,
        )
    
    def _fetch_analysis(
        self,
        db: Any,
        query: str,
        params: tuple,
        check_exists: bool = False,
        suppress_errors: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Helper to fetch analysis data from a database.

        Args:
            db: Database manager instance.
            query: SQL query to execute.
            params: Tuple of query parameters.
            check_exists: Whether to check if DB exists first.
            suppress_errors: Whether to suppress exceptions.

        Returns:
            Dictionary with result row or None.
        """
        if check_exists and not db.exists():
            return None

        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                row = cursor.fetchone()

                if row:
                    return dict(row)
        except Exception:
            if not suppress_errors:
                raise
            # Fallthrough to return None
            pass

        return None

    def _fetch_rows(
        self,
        db: Any,
        query: str,
        params: tuple,
        check_exists: bool = False,
        suppress_errors: bool = False
    ) -> List[Dict[str, Any]]:
        """Helper to fetch multiple rows from a database."""
        if check_exists and not db.exists():
            return []

        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            if not suppress_errors:
                raise
            return []

    def _get_readwise_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Readwise analysis for a specific month."""
        query = """
        SELECT year_month, year, month, articles, words, reading_time_mins,
               max_words_per_article, median_words_per_article, min_words_per_article
        FROM analysis
        WHERE year_month = ?
        """
        return self._fetch_analysis(self.readwise_db, query, (year_month,))
    
    def _get_foursquare_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Foursquare analysis for a specific month."""
        query = """
        SELECT year_month, year, month, checkins, unique_places
        FROM analysis
        WHERE year_month = ?
        """
        return self._fetch_analysis(
            self.foursquare_db,
            query,
            (year_month,),
            suppress_errors=True
        )
    
    def _get_letterboxd_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Letterboxd analysis for a specific month."""
        query = """
        SELECT year_month, year, month, movies_watched, avg_rating, min_rating, max_rating, avg_years_since_release
        FROM analysis
        WHERE year_month = ?
        """
        return self._fetch_analysis(self.letterboxd_db, query, (year_month,))
    
    def _get_overcast_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Overcast analysis for a specific month."""
        query = """
        SELECT year_month, year, month, feeds_added, feeds_removed, episodes_played
        FROM analysis
        WHERE year_month = ?
        """
        return self._fetch_analysis(
            self.overcast_db,
            query,
            (year_month,),
            check_exists=True,
            suppress_errors=True
        )
    
    def _get_strong_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Strong analysis for a specific month."""
        query = """
        SELECT year_month, year, month, workouts, total_minutes, unique_exercises, total_sets
        FROM analysis
        WHERE year_month = ?
        """
        return self._fetch_analysis(
            self.strong_db,
            query,
            (year_month,),
            check_exists=True,
            suppress_errors=True
        )
    
    def _get_hardcover_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get Hardcover analysis for a specific month."""
        query = """
        SELECT year_month, year, month, books_finished, avg_rating
        FROM analysis
        WHERE year_month = ?
        """
        return self._fetch_analysis(
            self.hardcover_db,
            query,
            (year_month,),
            check_exists=True,
            suppress_errors=True
        )
    
    def _get_github_analysis(self, year_month: str) -> Optional[Dict[str, Any]]:
        """Get GitHub analysis for a specific month."""
        query = """
        SELECT year_month, year, month, commits, repos_touched
        FROM analysis
        WHERE year_month = ?
        """
        return self._fetch_analysis(
            self.github_activity_db,
            query,
            (year_month,),
            check_exists=True,
            suppress_errors=True
        )

    def _get_readwise_articles(self, year_month: str) -> List[Dict[str, Any]]:
        """Get archived Readwise articles for a specific month."""
        query = """
        SELECT
            title,
            COALESCE(source_url, url) AS link,
            site_name,
            author,
            word_count,
            reading_time,
            last_moved_at
        FROM documents
        WHERE location = 'archive'
          AND last_moved_at IS NOT NULL
          AND strftime('%Y-%m', last_moved_at) = ?
        ORDER BY datetime(last_moved_at) DESC, title ASC
        """
        articles = self._fetch_rows(self.readwise_db, query, (year_month,))
        for article in articles:
            article['reading_speed_wpm'] = self._compute_reading_speed(
                article.get('word_count'),
                article.get('reading_time')
            )
        return articles

    def _get_readwise_highlights(self, year_month: str) -> List[Dict[str, Any]]:
        """Get Readwise highlights grouped-able by source item for a specific month."""
        query = """
        SELECT
            b.title AS source_title,
            b.category AS source_category,
            COALESCE(b.source_url, b.readwise_url, b.unique_url) AS source_link,
            h.text,
            h.note,
            h.highlighted_at
        FROM highlights h
        JOIN books b ON b.user_book_id = h.book_id
        WHERE h.highlighted_at IS NOT NULL
          AND h.is_deleted = 0
          AND strftime('%Y-%m', h.highlighted_at) = ?
        ORDER BY datetime(h.highlighted_at) DESC, b.title ASC, h.id ASC
        """
        return self._fetch_rows(self.readwise_db, query, (year_month,))

    def _get_movies_watched(self, year_month: str) -> List[Dict[str, Any]]:
        """Get movies watched in a specific month."""
        query = """
        SELECT
            w.movie_name,
            w.year,
            w.watched_at,
            w.letterboxd_uri,
            r.rating
        FROM watched w
        LEFT JOIN ratings r ON r.letterboxd_uri = w.letterboxd_uri
        WHERE strftime('%Y-%m', w.watched_at) = ?
        ORDER BY date(w.watched_at) DESC, w.movie_name ASC
        """
        return self._fetch_rows(self.letterboxd_db, query, (year_month,))

    def _get_podcast_episodes(self, year_month: str) -> List[Dict[str, Any]]:
        """Get played podcast episodes in a specific month."""
        query = """
        SELECT
            f.title AS podcast_title,
            f.htmlUrl AS podcast_link,
            e.title AS episode_title,
            e.overcastUrl AS episode_link,
            e.userUpdatedDate
        FROM episodes e
        LEFT JOIN feeds f ON f.overcastId = e.feedId
        WHERE e.played = 1
          AND e.userUpdatedDate IS NOT NULL
          AND strftime('%Y-%m', e.userUpdatedDate) = ?
        ORDER BY datetime(e.userUpdatedDate) DESC, f.title ASC, e.title ASC
        """
        return self._fetch_rows(
            self.overcast_db,
            query,
            (year_month,),
            check_exists=True,
            suppress_errors=True
        )

    def _get_github_commits(self, year_month: str) -> List[Dict[str, Any]]:
        """Get GitHub commits for a specific month."""
        query = """
        SELECT repo, message, author_date, sha
        FROM commits
        WHERE date_month = ?
          AND (
            message IS NULL
            OR message NOT LIKE 'Merge pull request #%'
          )
        ORDER BY datetime(author_date) DESC, repo ASC, sha ASC
        """
        return self._fetch_rows(
            self.github_activity_db,
            query,
            (year_month,),
            check_exists=True,
            suppress_errors=True
        )
    
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
        logger.info(f"Generating report for {year_month}")
        
        # Generate markdown using shared method
        markdown_content = self.generate_markdown(year_month)
        
        self._ensure_github_client()
        
        # Commit blog post
        file_path = f"content/posts/{year}-{month}-monthly-report.md"
        commit_message = f"feat: Add monthly report draft for {month}/{year}"
        
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
                'max_words_per_article': readwise['max_words_per_article'],
                'median_words_per_article': readwise['median_words_per_article'],
                'min_words_per_article': readwise['min_words_per_article'],
                'article_list': self._get_readwise_articles(year_month),
                'highlight_groups': self._group_readwise_highlights(
                    self._get_readwise_highlights(year_month)
                ),
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
                'movies': self._get_movies_watched(year_month),
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
                'episodes': self._get_podcast_episodes(year_month),
                'comparisons': overcast_comparisons
            }
        
        # Get Strong analysis
        strong = self._get_strong_analysis(year_month)
        if strong:
            strong_comparisons = compute_comparisons(
                current_stats=strong,
                historical_getter=self._get_strong_analysis,
                year_month=year_month,
                metrics=['workouts', 'total_minutes']
            )
            data['strong'] = {
                'workouts': strong['workouts'],
                'total_minutes': strong['total_minutes'],
                'unique_exercises': strong['unique_exercises'],
                'total_sets': strong['total_sets'],
                'comparisons': strong_comparisons
            }
        
        # Get Hardcover analysis
        hardcover = self._get_hardcover_analysis(year_month)
        if hardcover:
            hardcover_comparisons = compute_comparisons(
                current_stats=hardcover,
                historical_getter=self._get_hardcover_analysis,
                year_month=year_month,
                metrics=['books_finished', 'avg_rating']
            )
            data['hardcover'] = {
                'books_finished': hardcover['books_finished'],
                'avg_rating': hardcover['avg_rating'],
                'comparisons': hardcover_comparisons
            }
        
        # Get GitHub analysis
        github = self._get_github_analysis(year_month)
        if github:
            github_comparisons = compute_comparisons(
                current_stats=github,
                historical_getter=self._get_github_analysis,
                year_month=year_month,
                metrics=['commits', 'repos_touched']
            )
            data['github'] = {
                'commits': github['commits'],
                'repos_touched': github['repos_touched'],
                'commit_groups': self._group_commits_by_repo(
                    self._get_github_commits(year_month)
                ),
                'comparisons': github_comparisons
            }

        return self.markdown_generator.generate_monthly_summary(data)

    def _group_readwise_highlights(self, highlights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group Readwise highlights by article or book title."""
        groups: Dict[str, Dict[str, Any]] = {}

        for highlight in highlights:
            title = highlight.get('source_title') or "Untitled"
            if title not in groups:
                groups[title] = {
                    'title': title,
                    'category': highlight.get('source_category'),
                    'link': highlight.get('source_link'),
                    'highlights': [],
                }

            text = (highlight.get('text') or '').strip()
            note = (highlight.get('note') or '').strip()
            if text or note:
                groups[title]['highlights'].append({
                    'date': highlight.get('highlighted_at'),
                    'text': text,
                    'note': note,
                })

        return list(groups.values())

    def _group_commits_by_repo(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group commits by repository."""
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for commit in commits:
            repo = commit.get('repo') or "unknown"
            groups.setdefault(repo, []).append(commit)

        return [
            {'repo': repo, 'commits': repo_commits}
            for repo, repo_commits in groups.items()
        ]

    def _compute_reading_speed(self, word_count: Any, reading_time: Any) -> Optional[int]:
        """Compute words-per-minute from Readwise document fields."""
        if not word_count or not reading_time:
            return None

        match = re.search(r'(\d+)', str(reading_time))
        if not match:
            return None

        minutes = int(match.group(1))
        if minutes <= 0:
            return None

        return round(int(word_count) / minutes)
