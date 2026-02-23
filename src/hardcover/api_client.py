"""Hardcover GraphQL API client."""

import time
from typing import Optional, List, Dict, Any
import requests

from ..config import Config


class HardcoverAPIClient:
    """Client for the Hardcover GraphQL API."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize API client.
        
        Args:
            access_token: Hardcover API token. Defaults to config value.
        """
        self.access_token = access_token or Config.HARDCOVER_ACCESS_TOKEN
        self.api_url = Config.HARDCOVER_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        })
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a GraphQL query.
        
        Args:
            query: GraphQL query string.
            
        Returns:
            Response data dictionary.
            
        Raises:
            requests.HTTPError: On API errors.
            ValueError: On GraphQL errors.
        """
        self._rate_limit()
        
        response = self.session.post(
            self.api_url,
            json={"query": query},
            timeout=60,
        )
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self._execute_query(query)
        
        response.raise_for_status()
        result = response.json()
        
        if "errors" in result:
            raise ValueError(f"GraphQL errors: {result['errors']}")
        
        return result.get("data", {})
    
    def validate_token(self) -> bool:
        """Validate the access token by making a simple query.
        
        Returns:
            True if token is valid.
        """
        try:
            data = self._execute_query("{ me { id } }")
            return bool(data.get("me"))
        except Exception:
            return False
    
    def get_finished_books(self) -> List[Dict[str, Any]]:
        """Fetch all books marked as 'read' (status_id = 3).
        
        Returns:
            List of user_book objects with nested book data.
        """
        query = """
        {
          me {
            user_books(where: {status_id: {_eq: 3}}) {
              rating
              date_added
              reviewed_at
              book {
                title
                slug
                cached_contributors
              }
            }
          }
        }
        """
        
        data = self._execute_query(query)
        
        # me returns a list with one element
        me = data.get("me", [])
        if not me:
            return []
        
        return me[0].get("user_books", [])
