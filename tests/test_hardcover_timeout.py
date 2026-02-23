import unittest
from unittest.mock import MagicMock, patch
from src.hardcover.api_client import HardcoverAPIClient

class TestHardcoverAPIClient(unittest.TestCase):
    def test_execute_query_timeout(self):
        """Test that _execute_query calls requests.post with a timeout."""
        with patch('src.hardcover.api_client.requests.Session') as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_post = mock_session.post
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"data": {}}

            client = HardcoverAPIClient(access_token="test_token")
            client._execute_query("{ me { id } }")

            # Check if timeout was passed
            call_kwargs = mock_post.call_args[1]
            self.assertIn("timeout", call_kwargs, "Timeout argument missing in requests.post call")
            self.assertGreater(call_kwargs["timeout"], 0, "Timeout should be greater than 0")

if __name__ == "__main__":
    unittest.main()
