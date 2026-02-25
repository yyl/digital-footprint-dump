"""Sync manager for Hardcover book data."""

from typing import Optional, Dict, Any, List

from .database import HardcoverDatabase
from .api_client import HardcoverAPIClient


class HardcoverSyncManager:
    """Orchestrates synchronization between Hardcover API and local database."""
    
    def __init__(
        self,
        db: Optional[HardcoverDatabase] = None,
        api: Optional[HardcoverAPIClient] = None,
    ):
        """Initialize sync manager.
        
        Args:
            db: Database manager instance.
            api: API client instance.
        """
        self.db = db or HardcoverDatabase()
        self.api = api or HardcoverAPIClient()
    
    def _extract_author(self, cached_contributors) -> Optional[str]:
        """Extract author name from cached_contributors field.
        
        Args:
            cached_contributors: Contributors data from API (list of dicts).
            
        Returns:
            Author name or None.
        """
        if not cached_contributors:
            return None
        
        if isinstance(cached_contributors, list) and len(cached_contributors) > 0:
            contributor = cached_contributors[0]
            if isinstance(contributor, dict):
                # Try common field patterns
                author = contributor.get("author", {})
                if isinstance(author, dict):
                    return author.get("name")
                return contributor.get("name")
        
        return None
    
    def sync(self) -> Dict[str, Any]:
        """Fetch finished books from API and upsert into database.
        
        Returns:
            Dictionary with sync statistics.
        """
        self.db.init_tables()
        
        print("Fetching finished books from Hardcover...")
        user_books = self.api.get_finished_books()
        
        books_to_upsert = []
        for ub in user_books:
            book_data = ub.get("book", {})
            
            date_added = ub.get("date_added")
            reviewed_at = ub.get("reviewed_at")
            date_read = reviewed_at if reviewed_at else date_added
            
            author = self._extract_author(book_data.get("cached_contributors"))
            
            book = {
                "slug": book_data.get("slug", ""),
                "title": book_data.get("title", ""),
                "author": author,
                "rating": ub.get("rating"),
                "date_added": date_added,
                "reviewed_at": reviewed_at,
                "date_read": date_read,
            }
            
            if book["slug"]:
                books_to_upsert.append(book)

        count = len(books_to_upsert)
        if count > 0:
            self.db.upsert_books(books_to_upsert)
        
        print(f"Synced {count} finished books")
        return {"books": count}
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync status.
        
        Returns:
            Dictionary with database stats.
        """
        if not self.db.exists():
            return {"status": "not initialized"}
        return self.db.get_stats()
