from src.blog.analytics import BlogAnalytics
from src.blog.database import BlogDatabase


def test_blog_analytics_rolls_up_posts_words_and_unique_tags(tmp_path):
    db = BlogDatabase(str(tmp_path / "blog.db"))
    db.init_tables()
    db.replace_posts(
        [
            {
                "permalink": "https://example.com/posts/a/",
                "title": "A",
                "published_at": "2026-03-01T10:00:00-08:00",
                "last_modified_at": None,
                "slug": "a",
                "word_count": 1000,
                "reading_time": 5,
                "summary": "A",
                "section": "posts",
                "draft": False,
                "tags": ["python", "hugo"],
            },
            {
                "permalink": "https://example.com/posts/b/",
                "title": "B",
                "published_at": "2026-03-15T10:00:00-07:00",
                "last_modified_at": None,
                "slug": "b",
                "word_count": 500,
                "reading_time": 3,
                "summary": "B",
                "section": "posts",
                "draft": False,
                "tags": ["python", "notes"],
            },
            {
                "permalink": "https://example.com/posts/c/",
                "title": "C",
                "published_at": "2026-04-03T10:00:00-07:00",
                "last_modified_at": None,
                "slug": "c",
                "word_count": 750,
                "reading_time": 4,
                "summary": "C",
                "section": "posts",
                "draft": False,
                "tags": [],
            },
        ]
    )

    analytics = BlogAnalytics(db=db)
    assert analytics.analyze_posts() == 2

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT year_month, posts, total_words, unique_tags FROM analysis ORDER BY year_month ASC")
        rows = [dict(row) for row in cursor.fetchall()]

    assert rows == [
        {"year_month": "2026-03", "posts": 2, "total_words": 1500, "unique_tags": 3},
        {"year_month": "2026-04", "posts": 1, "total_words": 750, "unique_tags": 0},
    ]
