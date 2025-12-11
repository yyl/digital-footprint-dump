"""Readwise API client with pagination and rate limiting support."""

import time
from typing import Optional, Generator, Dict, Any, List
import requests

from ..config import Config


class ReadwiseAPIClient:
    """Client for Readwise and Reader APIs."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize API client.
        
        Args:
            access_token: Readwise access token. Defaults to config value.
        """
        self.access_token = access_token or Config.READWISE_ACCESS_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.access_token}",
            "Content-Type": "application/json"
        })
        self._last_request_time = 0
        self._min_request_interval = 60 / Config.READWISE_RATE_LIMIT  # seconds between requests
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response with rate limit retry."""
        if response.status_code == 429:
            # Rate limited - wait and retry
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return None  # Signal to retry
        
        response.raise_for_status()
        return response.json()
    
    def validate_token(self) -> bool:
        """Validate the access token."""
        self._rate_limit()
        response = self.session.get(f"{Config.READWISE_API_V2_BASE}/auth/")
        return response.status_code == 204
    
    # ==========================================================================
    # Readwise API v2 - Export (Books + Highlights)
    # ==========================================================================
    
    def export_highlights(
        self,
        updated_after: Optional[str] = None,
        include_deleted: bool = True
    ) -> Generator[Dict[str, Any], None, None]:
        """Export all books and highlights with pagination.
        
        Args:
            updated_after: ISO 8601 datetime to fetch updates after
            include_deleted: Include deleted highlights
            
        Yields:
            Book objects with nested highlights
        """
        next_cursor = None
        
        while True:
            self._rate_limit()
            
            params = {}
            if next_cursor:
                params["pageCursor"] = next_cursor
            if updated_after:
                params["updatedAfter"] = updated_after
            if include_deleted:
                params["includeDeleted"] = "true"
            
            response = self.session.get(
                f"{Config.READWISE_API_V2_BASE}/export/",
                params=params
            )
            
            data = self._handle_response(response)
            if data is None:
                # Rate limited, retry
                continue
            
            for book in data.get("results", []):
                yield book
            
            next_cursor = data.get("nextPageCursor")
            if not next_cursor:
                break
    
    # ==========================================================================
    # Reader API v3 - Documents
    # ==========================================================================
    
    def list_documents(
        self,
        updated_after: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """List all Reader documents with pagination.
        
        Args:
            updated_after: ISO 8601 datetime to fetch updates after
            location: Filter by location (new, later, archive, feed)
            category: Filter by category (article, email, rss, etc.)
            
        Yields:
            Document objects
        """
        next_cursor = None
        
        while True:
            self._rate_limit()
            
            params = {}
            if next_cursor:
                params["pageCursor"] = next_cursor
            if updated_after:
                params["updatedAfter"] = updated_after
            if location:
                params["location"] = location
            if category:
                params["category"] = category
            
            response = self.session.get(
                f"{Config.READER_API_V3_BASE}/list/",
                params=params
            )
            
            data = self._handle_response(response)
            if data is None:
                # Rate limited, retry
                continue
            
            for doc in data.get("results", []):
                yield doc
            
            next_cursor = data.get("nextPageCursor")
            if not next_cursor:
                break
    
    # ==========================================================================
    # Readwise API v2 - Daily Review
    # ==========================================================================
    
    def get_daily_review(self) -> Dict[str, Any]:
        """Get today's daily review highlights."""
        self._rate_limit()
        response = self.session.get(f"{Config.READWISE_API_V2_BASE}/review/")
        return self._handle_response(response)
