import unittest
from unittest.mock import MagicMock, patch
from src.readwise.api_client import ReadwiseAPIClient
from src.config import Config

class TestReadwiseClientSecurity(unittest.TestCase):

    def setUp(self):
        self.mock_config_patcher = patch('src.readwise.api_client.Config')
        self.mock_config = self.mock_config_patcher.start()
        self.mock_config.READWISE_API_V2_BASE = "https://readwise.io/api/v2"
        self.mock_config.READER_API_V3_BASE = "https://readwise.io/api/v3"
        self.mock_config.READWISE_RATE_LIMIT = 20

        self.mock_session_patcher = patch('requests.Session')
        self.mock_session_cls = self.mock_session_patcher.start()
        self.mock_session = self.mock_session_cls.return_value

        # Setup common response
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {}
        self.mock_session.get.return_value = self.mock_response

    def tearDown(self):
        self.mock_config_patcher.stop()
        self.mock_session_patcher.stop()

    def test_validate_token_timeout(self):
        self.mock_response.status_code = 204
        client = ReadwiseAPIClient(access_token="test_token")
        client.validate_token()

        self.mock_session.get.assert_called_with(
            f"{self.mock_config.READWISE_API_V2_BASE}/auth/",
            timeout=60
        )

    def test_export_highlights_timeout(self):
        client = ReadwiseAPIClient(access_token="test_token")
        # Consume the generator to trigger the request
        list(client.export_highlights())

        # Check call arguments
        args, kwargs = self.mock_session.get.call_args
        self.assertEqual(args[0], f"{self.mock_config.READWISE_API_V2_BASE}/export/")
        self.assertEqual(kwargs.get('timeout'), 60)

    def test_list_documents_timeout(self):
        client = ReadwiseAPIClient(access_token="test_token")
        # Consume the generator to trigger the request
        list(client.list_documents())

        # Check call arguments
        args, kwargs = self.mock_session.get.call_args
        self.assertEqual(args[0], f"{self.mock_config.READER_API_V3_BASE}/list/")
        self.assertEqual(kwargs.get('timeout'), 60)

    def test_get_daily_review_timeout(self):
        client = ReadwiseAPIClient(access_token="test_token")
        client.get_daily_review()

        # Check call arguments
        args, kwargs = self.mock_session.get.call_args
        self.assertEqual(args[0], f"{self.mock_config.READWISE_API_V2_BASE}/review/")
        self.assertEqual(kwargs.get('timeout'), 60)
