"""HTTP client for the public blog posts export."""

from typing import Any, Dict, List, Optional

import requests

from ..config import Config


DEFAULT_TIMEOUT = 60


class BlogAPIClient:
    """Fetches the public Hugo JSON export for blog posts."""

    def __init__(self, posts_index_url: Optional[str] = None):
        """Initialize API client."""
        self.posts_index_url = posts_index_url or Config.BLOG_POSTS_INDEX_URL
        self.session = requests.Session()

    def fetch_posts(self) -> List[Dict[str, Any]]:
        """Fetch the full posts snapshot from the public JSON export."""
        response = self.session.get(self.posts_index_url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list):
            raise ValueError("Blog posts export must be a JSON array")

        return payload
