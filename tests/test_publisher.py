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
        self.mock_apple_health_db = MagicMock(spec=BaseDatabase)
        self.mock_hardcover_db = MagicMock(spec=BaseDatabase)
        self.mock_github_activity_db = MagicMock(spec=BaseDatabase)

        # Initialize publisher with mocks
        self.publisher = Publisher(
            readwise_db=self.mock_readwise_db,
            foursquare_db=self.mock_foursquare_db,
            letterboxd_db=self.mock_letterboxd_db,
            overcast_db=self.mock_overcast_db,
            strong_db=self.mock_strong_db,
            apple_health_db=self.mock_apple_health_db,
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

    def test_get_apple_health_analysis_exists_success(self):
        self.mock_apple_health_db.exists.return_value = True
        conn = MagicMock()
        cursor = MagicMock()
        self.mock_apple_health_db.get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {'year_month': '2023-01', 'workouts': 8, 'total_duration_seconds': 5400, 'total_calories': 1234.5}

        result = self.publisher._get_apple_health_analysis('2023-01')
        self.assertEqual(result, {'year_month': '2023-01', 'workouts': 8, 'total_duration_seconds': 5400, 'total_calories': 1234.5})

    def test_get_apple_health_activity_breakdown(self):
        self.mock_apple_health_db.exists.return_value = True
        conn = MagicMock()
        cursor = MagicMock()
        self.mock_apple_health_db.get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value = cursor
        cursor.fetchall.return_value = [
            {'activity_type': 'run', 'workouts': 3},
            {'activity_type': 'walk', 'workouts': 2},
        ]

        result = self.publisher._get_apple_health_activity_breakdown('2023-01')
        self.assertEqual(result, [
            {'activity_type': 'run', 'workouts': 3},
            {'activity_type': 'walk', 'workouts': 2},
        ])

    def test_get_target_year_month_uses_all_sources(self):
        self.mock_readwise_db.exists.return_value = True
        self.mock_foursquare_db.exists.return_value = True
        self.mock_letterboxd_db.exists.return_value = True
        self.mock_overcast_db.exists.return_value = True
        self.mock_strong_db.exists.return_value = True
        self.mock_apple_health_db.exists.return_value = True
        self.mock_hardcover_db.exists.return_value = True
        self.mock_github_activity_db.exists.return_value = True

        self.mock_readwise_db.get_connection.side_effect = Exception("readwise missing")
        self.mock_foursquare_db.get_connection.side_effect = Exception("foursquare missing")

        def make_conn(year_month):
            conn = MagicMock()
            cursor = MagicMock()
            conn.cursor.return_value = cursor
            cursor.fetchall.return_value = [] if year_month is None else [{"year_month": year_month}]
            manager = MagicMock()
            manager.__enter__.return_value = conn
            manager.__exit__.return_value = None
            return manager

        self.mock_letterboxd_db.get_connection.return_value = make_conn("2024-12")
        self.mock_overcast_db.get_connection.return_value = make_conn("2025-01")
        self.mock_strong_db.get_connection.return_value = make_conn("2025-12")
        self.mock_apple_health_db.get_connection.return_value = make_conn("2025-02")
        self.mock_hardcover_db.get_connection.return_value = make_conn("2025-03")
        self.mock_github_activity_db.get_connection.return_value = make_conn("2025-01")

        result = self.publisher._get_target_year_month()

        self.assertEqual(result, "2025-03")
        
        # Test last_month flag
        result_last = self.publisher._get_target_year_month(last_month=True)
        self.assertEqual(result_last, "2025-02")
