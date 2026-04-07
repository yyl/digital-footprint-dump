"""Sync manager for public blog post tracking."""

from typing import Any, Dict, List, Optional

from .api_client import BlogAPIClient
from .database import BlogDatabase


class BlogSyncManager:
    """Syncs published blog posts from the public JSON export."""

    def __init__(
        self,
        db: Optional[BlogDatabase] = None,
        api: Optional[BlogAPIClient] = None,
    ):
        """Initialize sync manager."""
        self.db = db or BlogDatabase()
        self.api = api or BlogAPIClient()

    def sync(self) -> Dict[str, int]:
        """Fetch the latest public snapshot and replace local raw tables."""
        self.db.init_tables()
        posts = self._normalize_posts(self.api.fetch_posts())
        saved = self.db.replace_posts(posts)
        print(f"Synced {saved} published blog posts")
        return {"posts": saved}

    def get_status(self) -> Dict[str, Any]:
        """Get raw-table counts and latest published post metadata."""
        self.db.init_tables()
        latest_post = None

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT title, published_at, permalink
                FROM posts
                ORDER BY datetime(published_at) DESC, permalink ASC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row:
                latest_post = dict(row)

        return {
            "database_stats": self.db.get_stats(),
            "source_url": self.api.posts_index_url,
            "latest_post": latest_post,
        }

    def _normalize_posts(self, payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize the JSON export into DB-ready post records."""
        posts = []

        for item in payload:
            if not isinstance(item, dict):
                continue

            permalink = _clean_string(item.get("permalink"))
            published_at = _clean_string(item.get("date"))
            if not permalink or not published_at or item.get("draft"):
                continue

            tags = sorted(
                {
                    tag
                    for tag in (_clean_string(value) for value in item.get("tags") or [])
                    if tag
                }
            )

            posts.append(
                {
                    "permalink": permalink,
                    "title": _clean_string(item.get("title")) or permalink,
                    "published_at": published_at,
                    "last_modified_at": _clean_string(item.get("lastmod")),
                    "slug": _clean_string(item.get("slug")),
                    "word_count": _to_int(item.get("wordCount")),
                    "reading_time": _to_int(item.get("readingTime")),
                    "summary": _clean_string(item.get("summary")),
                    "section": _clean_string(item.get("section")),
                    "draft": False,
                    "tags": tags,
                }
            )

        posts.sort(key=lambda post: (post["published_at"], post["permalink"]))
        return posts


def _clean_string(value: Any) -> Optional[str]:
    """Normalize string-ish values."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_int(value: Any) -> int:
    """Parse integer-like JSON values."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
