
import unittest
from unittest.mock import MagicMock, patch
from src.github.api_client import GitHubActivityClient

class TestGitHubActivityClient(unittest.TestCase):
    def setUp(self):
        # Mock Config to avoid environment variable issues
        with patch("src.github.api_client.Config") as mock_config:
            mock_config.BLOG_GITHUB_TOKEN = "test_token"
            mock_config.GITHUB_USERNAME = "test_user"
            self.client = GitHubActivityClient()

    @patch("src.github.api_client.requests.Session.get")
    def test_get_timeout_enforced(self, mock_get):
        """Test that requests.get is called with a timeout."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        # Call the method
        self.client._get("/test")

        # Verify timeout argument
        mock_get.assert_called()
        args, kwargs = mock_get.call_args

        if 'timeout' not in kwargs:
             self.fail("timeout parameter missing in requests.get call")

        self.assertEqual(kwargs['timeout'], 60, "Timeout should be set to 60 seconds")

if __name__ == "__main__":
    unittest.main()
