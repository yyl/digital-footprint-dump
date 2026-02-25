"""Sync manager for orchestrating Readwise data synchronization."""

from datetime import datetime
from typing import Optional

from ..config import Config
from .database import ReadwiseDatabase
from .api_client import ReadwiseAPIClient


class SyncManager:
    """Orchestrates synchronization between Readwise APIs and local database."""
    
    # Entity type constants for sync state
    ENTITY_BOOKS = "books"
    ENTITY_DOCUMENTS = "documents"
    
    def __init__(
        self,
        db: Optional[ReadwiseDatabase] = None,
        api: Optional[ReadwiseAPIClient] = None
    ):
        """Initialize sync manager.
        
        Args:
            db: Database manager instance
            api: API client instance
        """
        self.db = db or ReadwiseDatabase()
        self.api = api or ReadwiseAPIClient()
    
    def sync_all(self) -> dict:
        """Sync all data from Readwise.
        
        Returns:
            Dictionary with sync statistics
        """
        print("Starting full sync...")
        stats = {
            "books": 0,
            "highlights": 0,
            "documents": 0,
        }
        
        # Sync books and highlights from Readwise Export API
        book_stats = self.sync_books_and_highlights()
        stats["books"] = book_stats["books"]
        stats["highlights"] = book_stats["highlights"]
        
        # Sync documents from Reader API
        stats["documents"] = self.sync_documents()
        
        print(f"\nSync complete!")
        print(f"  Books: {stats['books']}")
        print(f"  Highlights: {stats['highlights']}")
        print(f"  Documents: {stats['documents']}")
        
        return stats
    
    def sync_books_and_highlights(self) -> dict:
        """Sync books and highlights from Readwise Export API.
        
        Returns:
            Dictionary with counts of synced books and highlights
        """
        stats = {"books": 0, "highlights": 0}
        
        # Get last sync time
        sync_state = self.db.get_sync_state(self.ENTITY_BOOKS)
        updated_after = sync_state["last_sync_at"] if sync_state else None
        
        if updated_after:
            print(f"Syncing books/highlights updated after: {updated_after}")
        else:
            print("Performing initial full sync of books/highlights...")
        
        # Record sync start time
        sync_start = datetime.utcnow().isoformat() + "Z"
        
        # Fetch and save books with highlights
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for book in self.api.export_highlights(updated_after=updated_after):
                    # Save book
                    self.db.upsert_book(book, cursor=cursor)
                    stats["books"] += 1

                    # Save highlights
                    for highlight in book.get("highlights", []):
                        self.db.upsert_highlight(highlight, book["user_book_id"], cursor=cursor)
                        stats["highlights"] += 1

                    # Progress indicator
                    if stats["books"] % 10 == 0:
                        print(f"  Processed {stats['books']} books, {stats['highlights']} highlights...")
                        conn.commit()
            finally:
                cursor.close()
        
        # Update sync state
        self.db.update_sync_state(self.ENTITY_BOOKS, last_sync_at=sync_start)
        
        return stats
    
    def sync_documents(self) -> int:
        """Sync documents from Reader API.
        
        Returns:
            Count of synced documents
        """
        count = 0
        
        # Get last sync time
        sync_state = self.db.get_sync_state(self.ENTITY_DOCUMENTS)
        updated_after = sync_state["last_sync_at"] if sync_state else None
        
        if updated_after:
            print(f"Syncing documents updated after: {updated_after}")
        else:
            print("Performing initial full sync of documents...")
        
        # Record sync start time
        sync_start = datetime.utcnow().isoformat() + "Z"
        
        # Fetch and save documents
        for doc in self.api.list_documents(updated_after=updated_after):
            self.db.upsert_document(doc)
            count += 1
            
            # Progress indicator
            if count % 50 == 0:
                print(f"  Processed {count} documents...")
        
        # Update sync state
        self.db.update_sync_state(self.ENTITY_DOCUMENTS, last_sync_at=sync_start)
        
        return count
    
    def get_sync_status(self) -> dict:
        """Get current sync status and statistics.
        
        Returns:
            Dictionary with sync state and entity counts
        """
        status = {
            "database_stats": self.db.get_stats(),
            "sync_states": {}
        }
        
        for entity in [self.ENTITY_BOOKS, self.ENTITY_DOCUMENTS]:
            state = self.db.get_sync_state(entity)
            status["sync_states"][entity] = state
        
        return status
