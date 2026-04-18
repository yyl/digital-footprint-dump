from unittest.mock import patch
from src.overcast.rss_fetcher import RSSFetcher
import io

# Namespaced RSS
RSS_FIXTURE_1 = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
  <channel>
    <title>Podcast 1</title>
    <item>
      <title>Episode 1</title>
      <itunes:duration>1541</itunes:duration>
    </item>
    <item>
      <title>Episode 2 &amp; Stuff</title>
      <itunes:duration>02:31:53</itunes:duration>
    </item>
    <item>
      <title>Episode missing duration</title>
    </item>
  </channel>
</rss>
"""

# Non-namespaced RSS with fallback tag
RSS_FIXTURE_2 = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Podcast 2</title>
    <item>
      <title>Episode 3</title>
      <duration>05:00</duration>
    </item>
  </channel>
</rss>
"""

@patch('src.overcast.rss_fetcher.urlopen')
def test_fetch_durations(mock_urlopen):
    # Set up mock responses for two different URLs
    def mock_urlopen_side_effect(request, **kwargs):
        mock_response = io.BytesIO()
        if 'feed1.xml' in request.full_url:
            mock_response.write(RSS_FIXTURE_1)
        elif 'feed2.xml' in request.full_url:
            mock_response.write(RSS_FIXTURE_2)
        else:
            raise Exception("Unexpected URL")
        mock_response.seek(0)
        # Mock the read method
        response_obj = mock_response
        response_obj.read = lambda: mock_response.getvalue()
        return response_obj

    mock_urlopen.side_effect = mock_urlopen_side_effect

    fetcher = RSSFetcher()
    feeds = [
        {"overcastId": 101, "xmlUrl": "http://example.com/feed1.xml", "title": "Podcast 1"},
        {"overcastId": 102, "xmlUrl": "http://example.com/feed2.xml", "title": "Podcast 2"},
        {"overcastId": 103, "xmlUrl": None, "title": "No URL Podcast"},
    ]

    durations = fetcher.fetch_durations(feeds)

    assert len(durations) == 3
    # Check feed 1
    assert durations[(101, "Episode 1")] == 1541
    assert durations[(101, "Episode 2 & Stuff")] == 9113  # html entity unescaped
    # Check feed 2
    assert durations[(102, "Episode 3")] == 300
    
    # Missing duration episode is not in the dictionary
    assert (101, "Episode missing duration") not in durations

@patch('src.overcast.rss_fetcher.urlopen')
def test_fetch_durations_error_handling(mock_urlopen):
    # Make urlopen fail
    mock_urlopen.side_effect = Exception("Network error")
    
    fetcher = RSSFetcher()
    feeds = [{"overcastId": 101, "xmlUrl": "http://example.com/feed1.xml"}]
    
    # Should not crash, just return empty dict
    durations = fetcher.fetch_durations(feeds)
    assert durations == {}
