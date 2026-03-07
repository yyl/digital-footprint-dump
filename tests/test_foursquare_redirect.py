import sys
from unittest.mock import MagicMock

# Mock requests and dotenv before importing src modules if not available
try:
    import requests
except ImportError:
    mock_requests = MagicMock()
    class RequestException(Exception): pass
    mock_requests.exceptions.RequestException = RequestException
    sys.modules["requests"] = mock_requests
    sys.modules["requests.exceptions"] = mock_requests.exceptions

try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = MagicMock()

import unittest
from unittest.mock import patch
from src.foursquare.api_client import FoursquareAPIClient
from src.config import Config

class TestFoursquareRedirect(unittest.TestCase):
    def test_default_redirect_uri(self):
        """Test that client uses default redirect URI from Config."""
        # Ensure Config has the expected default
        with patch.object(Config, "FOURSQUARE_REDIRECT_URI", "https://localhost:8888/callback"):
            client = FoursquareAPIClient()
            self.assertEqual(client.redirect_uri, "https://localhost:8888/callback")

    def test_config_override_redirect_uri(self):
        """Test that client uses overridden redirect URI from Config."""
        custom_uri = "https://myapp.com/callback"
        with patch.object(Config, "FOURSQUARE_REDIRECT_URI", custom_uri):
            client = FoursquareAPIClient()
            self.assertEqual(client.redirect_uri, custom_uri)

    def test_init_override_redirect_uri(self):
        """Test that client uses redirect URI passed to __init__."""
        init_uri = "https://another-app.com/callback"
        client = FoursquareAPIClient(redirect_uri=init_uri)
        self.assertEqual(client.redirect_uri, init_uri)

if __name__ == "__main__":
    unittest.main()
