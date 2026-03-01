import unittest
from unittest.mock import MagicMock
from src.publish.publisher import Publisher
from src.database import BaseDatabase

class TestPublisher(unittest.TestCase):
    def setUp(self):
        # Create mock databases
        self.mock_readwise_db = MagicMock(spec=BaseDatabase)
        self.mock_foursquare_db = MagicMock(spec=BaseDatabase)
        self.mock_letterboxd_db = MagicMock(spec=BaseDatabase)
        self.mock_overcast_db = MagicMock(spec=BaseDatabase)
        self.mock_strong_db = MagicMock(spec=BaseDatabase)
        self.mock_hardcover_db = MagicMock(spec=BaseDatabase)
        self.mock_github_activity_db = MagicMock(spec=BaseDatabase)

        # Initialize publisher with mocks
        self.publisher = Publisher(
            readwise_db=self.mock_readwise_db,
            foursquare_db=self.mock_foursquare_db,
            letterboxd_db=self.mock_letterboxd_db,
            overcast_db=self.mock_overcast_db,
            strong_db=self.mock_strong_db,
            hardcover_db=self.mock_hardcover_db,
            github_activity_db=self.mock_github_activity_db
        )

    # Test 1: No exists check, No suppression (Readwise style)
    def test_get_readwise_analysis_success(self):
        conn = MagicMock()
        cursor = MagicMock()
        self.mock_readwise_db.get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {'year_month': '2023-01', 'articles': 10}

        result = self.publisher._get_readwise_analysis('2023-01')
        self.assertEqual(result, {'year_month': '2023-01', 'articles': 10})

    def test_get_readwise_analysis_exception(self):
        # Should propagate exception
        self.mock_readwise_db.get_connection.side_effect = Exception("DB Error")
        with self.assertRaises(Exception):
            self.publisher._get_readwise_analysis('2023-01')

    # Test 2: No exists check, With suppression (Foursquare style)
    def test_get_foursquare_analysis_success(self):
        conn = MagicMock()
        cursor = MagicMock()
        self.mock_foursquare_db.get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {'year_month': '2023-01', 'checkins': 5}

        result = self.publisher._get_foursquare_analysis('2023-01')
        self.assertEqual(result, {'year_month': '2023-01', 'checkins': 5})

    def test_get_foursquare_analysis_exception(self):
        # Should suppress exception and return None
        self.mock_foursquare_db.get_connection.side_effect = Exception("DB Error")
        result = self.publisher._get_foursquare_analysis('2023-01')
        self.assertIsNone(result)

    # Test 3: With exists check, With suppression (Overcast style)
    def test_get_overcast_analysis_not_exists(self):
        self.mock_overcast_db.exists.return_value = False
        result = self.publisher._get_overcast_analysis('2023-01')
        self.assertIsNone(result)
        # Should not even try to connect
        self.mock_overcast_db.get_connection.assert_not_called()

    def test_get_overcast_analysis_exists_success(self):
        self.mock_overcast_db.exists.return_value = True
        conn = MagicMock()
        cursor = MagicMock()
        self.mock_overcast_db.get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {'year_month': '2023-01', 'episodes_played': 20}

        result = self.publisher._get_overcast_analysis('2023-01')
        self.assertEqual(result, {'year_month': '2023-01', 'episodes_played': 20})

    def test_get_overcast_analysis_exists_exception(self):
        self.mock_overcast_db.exists.return_value = True
        self.mock_overcast_db.get_connection.side_effect = Exception("DB Error")

        result = self.publisher._get_overcast_analysis('2023-01')
        self.assertIsNone(result)
