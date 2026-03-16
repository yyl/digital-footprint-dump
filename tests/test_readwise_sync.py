import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock missing modules for environment compatibility
try:
    import dotenv
except ImportError:
    sys.modules['dotenv'] = MagicMock()

try:
    import requests
except ImportError:
    sys.modules['requests'] = MagicMock()

from src.readwise.sync import SyncManager

class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_api = MagicMock()
        self.manager = SyncManager(db=self.mock_db, api=self.mock_api)

    def test_init_defaults(self):
        """Test initialization with default values (using mocks for dependencies)."""
        with patch('src.readwise.sync.ReadwiseDatabase') as mock_db_cls, \
             patch('src.readwise.sync.ReadwiseAPIClient') as mock_api_cls:
            manager = SyncManager()
            self.assertEqual(manager.db, mock_db_cls.return_value)
            self.assertEqual(manager.api, mock_api_cls.return_value)

    def test_sync_documents_initial(self):
        """Test initial sync of documents when no previous state exists."""
        # Setup
        self.mock_db.get_sync_state.return_value = None
        self.mock_api.list_documents.return_value = [
            {"id": "doc1", "title": "Doc 1"},
            {"id": "doc2", "title": "Doc 2"}
        ]

        # Execute
        count = self.manager.sync_documents()

        # Verify
        self.assertEqual(count, 2)
        self.mock_db.get_sync_state.assert_called_with(SyncManager.ENTITY_DOCUMENTS)
        self.mock_api.list_documents.assert_called_with(updated_after=None)
        self.assertEqual(self.mock_db.upsert_document.call_count, 2)
        self.mock_db.update_sync_state.assert_called_once()
        args, kwargs = self.mock_db.update_sync_state.call_args
        self.assertEqual(args[0], SyncManager.ENTITY_DOCUMENTS)
        self.assertIn("last_sync_at", kwargs)

    def test_sync_documents_incremental(self):
        """Test incremental sync of documents using previous sync state."""
        # Setup
        last_sync = "2023-01-01T00:00:00Z"
        self.mock_db.get_sync_state.return_value = {"last_sync_at": last_sync}
        self.mock_api.list_documents.return_value = [{"id": "doc3", "title": "Doc 3"}]

        # Execute
        count = self.manager.sync_documents()

        # Verify
        self.assertEqual(count, 1)
        self.mock_api.list_documents.assert_called_with(updated_after=last_sync)
        self.mock_db.upsert_document.assert_called_once_with({"id": "doc3", "title": "Doc 3"})

    def test_sync_documents_empty(self):
        """Test sync when no documents are returned."""
        # Setup
        self.mock_api.list_documents.return_value = []

        # Execute
        count = self.manager.sync_documents()

        # Verify
        self.assertEqual(count, 0)
        self.mock_db.upsert_document.assert_not_called()

    def test_sync_all(self):
        """Test orchestration of all sync methods."""
        # Setup
        with patch.object(SyncManager, 'sync_books_and_highlights') as mock_books_sync, \
             patch.object(SyncManager, 'sync_documents') as mock_docs_sync:

            mock_books_sync.return_value = {"books": 5, "highlights": 50}
            mock_docs_sync.return_value = 10

            # Execute
            stats = self.manager.sync_all()

            # Verify
            self.assertEqual(stats["books"], 5)
            self.assertEqual(stats["highlights"], 50)
            self.assertEqual(stats["documents"], 10)
            mock_books_sync.assert_called_once()
            mock_docs_sync.assert_called_once()

if __name__ == '__main__':
    unittest.main()
