from unittest.mock import MagicMock

from src.blog.api_client import BlogAPIClient
from src.blog.database import BlogDatabase
from src.blog.sync import BlogSyncManager


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_api_client_fetch_posts_requires_json_array():
    client = BlogAPIClient("https://example.com/posts.json")
    client.session.get = MagicMock(return_value=_FakeResponse([{"title": "Post"}]))

    payload = client.fetch_posts()

    assert payload == [{"title": "Post"}]
    client.session.get.assert_called_once_with("https://example.com/posts.json", timeout=60)


def test_sync_imports_posts_tags_and_prunes_missing_posts(tmp_path):
    db = BlogDatabase(str(tmp_path / "blog.db"))
    api = MagicMock()
    api.posts_index_url = "https://example.com/posts.json"
    api.fetch_posts.side_effect = [
        [
            {
                "title": "First Post",
                "date": "2026-03-10T08:00:00-07:00",
                "lastmod": "2026-03-11T08:00:00-07:00",
                "permalink": "https://example.com/posts/first/",
                "slug": "first",
                "tags": ["writing", "hugo", "writing"],
                "wordCount": 1200,
                "readingTime": 6,
                "summary": "Hello",
                "section": "posts",
                "draft": False,
            },
            {
                "title": "Draft Post",
                "date": "2026-03-12T08:00:00-07:00",
                "permalink": "https://example.com/posts/draft/",
                "slug": "draft",
                "tags": ["draft"],
                "wordCount": 800,
                "readingTime": 4,
                "summary": "Draft",
                "section": "posts",
                "draft": True,
            },
            {
                "title": "Second Post",
                "date": "2026-04-02T08:00:00-07:00",
                "permalink": "https://example.com/posts/second/",
                "slug": "second",
                "tags": ["python"],
                "wordCount": 900,
                "readingTime": 5,
                "summary": "World",
                "section": "posts",
                "draft": False,
            },
        ],
        [
            {
                "title": "Second Post",
                "date": "2026-04-02T08:00:00-07:00",
                "permalink": "https://example.com/posts/second/",
                "slug": "second",
                "tags": ["python", "tracking"],
                "wordCount": 950,
                "readingTime": 5,
                "summary": "Updated",
                "section": "posts",
                "draft": False,
            },
        ],
    ]

    manager = BlogSyncManager(db=db, api=api)

    assert manager.sync() == {"posts": 2}
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts")
        assert cursor.fetchone()[0] == 2
        cursor.execute("SELECT COUNT(*) FROM post_tags")
        assert cursor.fetchone()[0] == 3

    assert manager.sync() == {"posts": 1}
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT COUNT(*) FROM post_tags")
        assert cursor.fetchone()[0] == 2
        cursor.execute("SELECT title, word_count FROM posts")
        row = cursor.fetchone()
        assert row["title"] == "Second Post"
        assert row["word_count"] == 950
