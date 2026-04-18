"""Fetch episode durations from podcast RSS feeds."""

import html
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError

from .duration import parse_duration

logger = logging.getLogger(__name__)

# itunes namespace used by most podcast RSS feeds
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"


class RSSFetcher:
    """Fetches episode durations from podcast RSS feeds."""

    def __init__(self, timeout: int = 10):
        """Initialize fetcher.

        Args:
            timeout: HTTP request timeout in seconds per feed.
        """
        self.timeout = timeout

    def fetch_durations(
        self, feeds: list[dict]
    ) -> Dict[Tuple[int, str], int]:
        """Fetch durations for episodes across all given feeds.

        Args:
            feeds: List of dicts with 'overcastId' (int) and 'xmlUrl' (str).

        Returns:
            Mapping of (feedId, episode_title) -> duration_seconds.
        """
        durations: Dict[Tuple[int, str], int] = {}

        for feed in feeds:
            feed_id = feed["overcastId"]
            xml_url = feed.get("xmlUrl")
            feed_title = feed.get("title", f"feed {feed_id}")

            if not xml_url:
                continue

            feed_durations = self._fetch_feed_durations(
                feed_id, xml_url, feed_title
            )
            durations.update(feed_durations)

        return durations

    def _fetch_feed_durations(
        self, feed_id: int, xml_url: str, feed_title: str
    ) -> Dict[Tuple[int, str], int]:
        """Fetch durations from a single RSS feed.

        Returns:
            Mapping of (feedId, episode_title) -> duration_seconds.
        """
        result: Dict[Tuple[int, str], int] = {}

        try:
            req = Request(xml_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=self.timeout) as resp:
                rss_data = resp.read()
        except (URLError, TimeoutError, OSError) as e:
            logger.warning("Failed to fetch RSS for %s: %s", feed_title, e)
            return result

        try:
            root = ET.fromstring(rss_data)
        except ET.ParseError as e:
            logger.warning("Failed to parse RSS for %s: %s", feed_title, e)
            return result

        for item in root.iter("item"):
            title_el = item.find("title")
            if title_el is None or not title_el.text:
                continue

            episode_title = html.unescape(title_el.text.strip())

            duration = self._extract_duration(item)
            if duration is not None:
                result[(feed_id, episode_title)] = duration

        return result

    def _extract_duration(self, item: ET.Element) -> Optional[int]:
        """Extract duration in seconds from an RSS <item> element."""
        # Try namespaced itunes:duration
        dur_el = item.find(f"{{{ITUNES_NS}}}duration")

        # Fallback: scan children for any tag containing 'duration'
        if dur_el is None:
            for child in item:
                if "duration" in child.tag.lower():
                    dur_el = child
                    break

        if dur_el is None or not dur_el.text:
            return None

        try:
            return parse_duration(dur_el.text)
        except ValueError as e:
            logger.warning(f"Failed to parse duration: {e}")
            return None
