import pytest
from unittest.mock import MagicMock, patch
from src.readwise.api_client import ReadwiseAPIClient

class TestReadwiseAPIClient:

    @pytest.fixture
    def client(self):
        with patch('src.readwise.api_client.Config') as MockConfig:
            MockConfig.READWISE_ACCESS_TOKEN = "test_token"
            MockConfig.READWISE_API_V2_BASE = "https://readwise.io/api/v2"
            MockConfig.READER_API_V3_BASE = "https://readwise.io/api/v3"
            MockConfig.READWISE_RATE_LIMIT = 20

            client = ReadwiseAPIClient(access_token="test_token")
            # Mock the session to avoid real network calls
            client.session = MagicMock()
            return client

    def test_export_highlights_pagination(self, client):
        # Setup mock responses
        mock_response_page1 = MagicMock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "results": [{"id": 1, "title": "Book 1"}],
            "nextPageCursor": "cursor1"
        }

        mock_response_page2 = MagicMock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {
            "results": [{"id": 2, "title": "Book 2"}],
            "nextPageCursor": None
        }

        client.session.get.side_effect = [mock_response_page1, mock_response_page2]

        results = list(client.export_highlights())

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2

        assert client.session.get.call_count == 2

        # Verify call arguments for page 1
        call_args_list = client.session.get.call_args_list
        args1, kwargs1 = call_args_list[0]
        assert kwargs1['params']['includeDeleted'] == "true"
        assert 'pageCursor' not in kwargs1['params']

        # Verify call arguments for page 2
        args2, kwargs2 = call_args_list[1]
        assert kwargs2['params']['pageCursor'] == "cursor1"
        assert kwargs2['params']['includeDeleted'] == "true"

    def test_list_documents_pagination(self, client):
        # Setup mock responses
        mock_response_page1 = MagicMock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "results": [{"id": "doc1", "title": "Doc 1"}],
            "nextPageCursor": "cursor_doc1"
        }

        mock_response_page2 = MagicMock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {
            "results": [{"id": "doc2", "title": "Doc 2"}],
            "nextPageCursor": None
        }

        client.session.get.side_effect = [mock_response_page1, mock_response_page2]

        results = list(client.list_documents(category="article"))

        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        assert results[1]["id"] == "doc2"

        assert client.session.get.call_count == 2

        # Verify call arguments
        call_args_list = client.session.get.call_args_list
        args1, kwargs1 = call_args_list[0]
        assert kwargs1['params']['category'] == "article"
        assert 'pageCursor' not in kwargs1['params']

        args2, kwargs2 = call_args_list[1]
        assert kwargs2['params']['pageCursor'] == "cursor_doc1"
        assert kwargs2['params']['category'] == "article"

    def test_rate_limiting_retry(self, client):
        # simulate 429 then 200
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "0"} # Set to 0 to speed up test

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "results": [{"id": 1}],
            "nextPageCursor": None
        }

        client.session.get.side_effect = [mock_response_429, mock_response_200]

        with patch('time.sleep') as mock_sleep:
            results = list(client.export_highlights())

            assert len(results) == 1
            assert client.session.get.call_count == 2
            mock_sleep.assert_called()
