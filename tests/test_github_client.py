
import unittest
from unittest.mock import MagicMock, patch
from src.github.api_client import GitHubActivityClient

class TestGitHubActivityClient(unittest.TestCase):
    def setUp(self):
        # We need to patch requests.Session BEFORE client init so self.client.session is a mock
        self.session_patcher = patch("src.github.api_client.requests.Session")
        self.mock_session_cls = self.session_patcher.start()
        self.mock_session = self.mock_session_cls.return_value

        # Mock Config
        self.config_patcher = patch("src.github.api_client.Config")
        self.mock_config = self.config_patcher.start()
        self.mock_config.BLOG_GITHUB_TOKEN = "test_token"
        self.mock_config.GITHUB_USERNAME = "test_user"

        self.client = GitHubActivityClient()

    def tearDown(self):
        self.session_patcher.stop()
        self.config_patcher.stop()

    def test_get_timeout_enforced(self):
        """Test that requests.get is called with a timeout."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        self.mock_session.get.return_value = mock_response

        # Call the method
        self.client._get("/test")

        # Verify timeout argument
        self.mock_session.get.assert_called()
        args, kwargs = self.mock_session.get.call_args

        if 'timeout' not in kwargs:
            self.fail("timeout parameter missing in requests.get call")

        self.assertEqual(kwargs['timeout'], 60, "Timeout should be set to 60 seconds")

if __name__ == "__main__":
    unittest.main()
