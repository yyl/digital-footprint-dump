import unittest

from src.publish.markdown_generator import MarkdownGenerator


class TestMarkdownGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = MarkdownGenerator()

    def test_markdown_link_skips_mailto_urls(self):
        result = self.generator._markdown_link(
            "Newsletter edition",
            "mailto:newsletter@example.com",
        )

        self.assertEqual(result, "Newsletter edition")

    def test_generate_readwise_articles_block_skips_mailto_links(self):
        result = self.generator._generate_readwise_articles_block([
            {
                "title": "Inbox essay",
                "link": "mailto:newsletter@example.com",
                "site_name": "TinyLetter",
                "last_moved_at": "2026-04-04T10:00:00Z",
                "reading_speed_wpm": 250,
            },
            {
                "title": "Web essay",
                "link": "https://example.com/post",
                "site_name": "TinyLetter",
                "last_moved_at": "2026-04-03T10:00:00Z",
                "reading_speed_wpm": 300,
            },
            {
                "title": "Another web essay",
                "link": "https://example.com/post-2",
                "site_name": "TinyLetter",
                "last_moved_at": "2026-04-02T10:00:00Z",
                "reading_speed_wpm": 320,
            },
        ])

        self.assertIn("| 2026-04-04 | Inbox essay | 250 wpm |", result)
        self.assertIn("| 2026-04-03 | [Web essay](https://example.com/post) | 300 wpm |", result)
        self.assertNotIn("[Inbox essay](mailto:newsletter@example.com)", result)

    def test_generate_readwise_articles_block_adds_ranked_source_summary(self):
        result = self.generator._generate_readwise_articles_block([
            {
                "title": "Essay A",
                "link": "https://example.com/a",
                "site_name": "Alpha",
                "last_moved_at": "2026-04-04T10:00:00Z",
                "reading_speed_wpm": 250,
            },
            {
                "title": "Essay B",
                "link": "https://example.com/b",
                "site_name": "Alpha",
                "last_moved_at": "2026-04-03T10:00:00Z",
                "reading_speed_wpm": 260,
            },
            {
                "title": "Essay C",
                "link": "https://example.com/c",
                "site_name": "Beta",
                "last_moved_at": "2026-04-02T10:00:00Z",
                "reading_speed_wpm": 270,
            },
            {
                "title": "Essay D",
                "link": "https://example.com/d",
                "site_name": "Gamma",
                "last_moved_at": "2026-04-01T10:00:00Z",
                "reading_speed_wpm": 280,
            },
        ])

        self.assertIn("| Source | Articles |", result)
        self.assertIn("| Alpha | 2 |", result)
        self.assertIn("| Other | 2 |", result)
        self.assertIn("#### Alpha", result)
        self.assertIn("#### Other", result)
        self.assertNotIn("#### Beta", result)
        self.assertNotIn("#### Gamma", result)

    def test_generate_podcasts_block_adds_ranked_summary_and_groups_other(self):
        result = self.generator._generate_podcasts_block([
            {
                "podcast_title": "Alpha Show",
                "podcast_link": "https://example.com/alpha",
                "episode_title": "Episode 1",
                "episode_link": "https://example.com/alpha-1",
                "userUpdatedDate": "2026-04-04T10:00:00Z",
            },
            {
                "podcast_title": "Alpha Show",
                "podcast_link": "https://example.com/alpha",
                "episode_title": "Episode 2",
                "episode_link": "https://example.com/alpha-2",
                "userUpdatedDate": "2026-04-03T10:00:00Z",
            },
            {
                "podcast_title": "Beta Show",
                "podcast_link": "https://example.com/beta",
                "episode_title": "Episode 3",
                "episode_link": "https://example.com/beta-1",
                "userUpdatedDate": "2026-04-02T10:00:00Z",
            },
            {
                "podcast_title": "Gamma Show",
                "podcast_link": "https://example.com/gamma",
                "episode_title": "Episode 4",
                "episode_link": "https://example.com/gamma-1",
                "userUpdatedDate": "2026-04-01T10:00:00Z",
            },
        ])

        self.assertIn("| Podcast | Episodes |", result)
        self.assertIn("| Alpha Show | 2 |", result)
        self.assertIn("| Other | 2 |", result)
        self.assertIn("#### [Alpha Show](https://example.com/alpha)", result)
        self.assertIn("#### Other", result)
        self.assertIn("| Date | Episode | Podcast |", result)
        self.assertNotIn("#### [Beta Show]", result)

    def test_generate_commit_groups_block_adds_ranked_summary_and_groups_other(self):
        result = self.generator._generate_commit_groups_block([
            {
                "repo": "user/alpha",
                "commits": [
                    {"repo": "user/alpha", "message": "feat: one", "author_date": "2026-04-04T10:00:00Z"},
                    {"repo": "user/alpha", "message": "fix: two", "author_date": "2026-04-03T10:00:00Z"},
                ],
            },
            {
                "repo": "user/beta",
                "commits": [
                    {"repo": "user/beta", "message": "chore: three", "author_date": "2026-04-02T10:00:00Z"},
                ],
            },
            {
                "repo": "user/gamma",
                "commits": [
                    {"repo": "user/gamma", "message": "docs: four", "author_date": "2026-04-01T10:00:00Z"},
                ],
            },
        ])

        self.assertIn("| Repo | Commits |", result)
        self.assertIn("| user/alpha | 2 |", result)
        self.assertIn("| Other | 2 |", result)
        self.assertIn("#### [user/alpha](https://github.com/user/alpha)", result)
        self.assertIn("#### Other", result)
        self.assertIn("| Date | Commit Message | Repo |", result)
        self.assertNotIn("#### [user/beta]", result)
