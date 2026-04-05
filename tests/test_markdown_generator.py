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
