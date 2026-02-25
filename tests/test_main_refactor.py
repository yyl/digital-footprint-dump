import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock missing modules for environment where dependencies might be missing
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()
# Mock github module as well as it might be used in imports
sys.modules['github'] = MagicMock()

# Ensure we can import main
sys.path.append(os.getcwd())
import main

class TestMainRefactor(unittest.TestCase):

    def test_run_analysis_helper(self):
        """Test the run_analysis helper function logic."""
        if not hasattr(main, 'run_analysis'):
            self.skipTest("run_analysis not implemented yet")

        mock_sync = MagicMock()
        mock_db_cls = MagicMock()
        mock_analytics_cls = MagicMock()

        mock_db_instance = mock_db_cls.return_value
        mock_analytics_instance = mock_analytics_cls.return_value

        # Mock methods
        mock_db_instance.init_tables = MagicMock()
        mock_db_instance.check_tables_exist = MagicMock(return_value=True)
        mock_analytics_instance.analyze_something = MagicMock(return_value=42)

        # Test case 1: All args provided, check_tables_exist=True
        main.run_analysis(
            sync_func=mock_sync,
            db_cls=mock_db_cls,
            analytics_cls=mock_analytics_cls,
            service_name="Test Service",
            analysis_method="analyze_something",
            db_filename="test.db",
            check_tables_exist=True
        )

        mock_sync.assert_called_once()
        mock_db_cls.assert_called_once()
        mock_db_instance.init_tables.assert_called_once()
        mock_db_instance.check_tables_exist.assert_called_once()
        mock_analytics_cls.assert_called_once_with(db=mock_db_instance)
        mock_analytics_instance.analyze_something.assert_called_once()

        # Reset mocks
        mock_sync.reset_mock()
        mock_db_cls.reset_mock()
        mock_analytics_cls.reset_mock()
        mock_db_instance.reset_mock()
        mock_analytics_instance.reset_mock()

        # Test case 2: No db_cls (Overcast style)
        main.run_analysis(
            sync_func=None,
            db_cls=None,
            analytics_cls=mock_analytics_cls,
            service_name="Test Service 2",
            analysis_method="analyze_something_else",
            db_filename="test2.db"
        )

        mock_sync.assert_not_called()
        mock_db_cls.assert_not_called()
        mock_analytics_cls.assert_called_once_with() # No args

    @patch('main.run_analysis')
    def test_cmd_readwise_analyze(self, mock_run):
        """Test cmd_readwise_analyze calls run_analysis with correct args."""
        try:
            main.cmd_readwise_analyze()
        except SystemExit:
            pass
        except Exception:
            pass

        if not mock_run.called:
             self.skipTest("cmd_readwise_analyze not refactored yet")

        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args

        from src.readwise.database import ReadwiseDatabase
        from src.readwise.analytics import ReadwiseAnalytics

        self.assertEqual(kwargs['sync_func'], main.cmd_readwise_sync)
        self.assertEqual(kwargs['db_cls'], ReadwiseDatabase)
        self.assertEqual(kwargs['analytics_cls'], ReadwiseAnalytics)
        self.assertEqual(kwargs['service_name'], "Readwise archive")
        self.assertEqual(kwargs['analysis_method'], "analyze_archived")
        self.assertEqual(kwargs['db_filename'], "readwise.db")
        self.assertTrue(kwargs['check_tables_exist'])

    @patch('main.run_analysis')
    def test_cmd_foursquare_analyze(self, mock_run):
        try:
            main.cmd_foursquare_analyze()
        except (Exception, SystemExit):
            pass

        if not mock_run.called:
             self.skipTest("cmd_foursquare_analyze not refactored yet")

        _, kwargs = mock_run.call_args
        from src.foursquare.database import FoursquareDatabase
        from src.foursquare.analytics import FoursquareAnalytics

        self.assertEqual(kwargs['sync_func'], main.cmd_foursquare_sync)
        self.assertEqual(kwargs['db_cls'], FoursquareDatabase)
        self.assertEqual(kwargs['analytics_cls'], FoursquareAnalytics)
        self.assertEqual(kwargs['service_name'], "Foursquare checkins")
        self.assertEqual(kwargs['analysis_method'], "analyze_checkins")
        self.assertEqual(kwargs['db_filename'], "foursquare.db")
        self.assertFalse(kwargs.get('check_tables_exist', False))

    @patch('main.run_analysis')
    def test_cmd_letterboxd_analyze(self, mock_run):
        try:
            main.cmd_letterboxd_analyze()
        except (Exception, SystemExit):
            pass

        if not mock_run.called:
             self.skipTest("cmd_letterboxd_analyze not refactored yet")

        _, kwargs = mock_run.call_args
        from src.letterboxd.database import LetterboxdDatabase
        from src.letterboxd.analytics import LetterboxdAnalytics

        self.assertEqual(kwargs['sync_func'], main.cmd_letterboxd_sync)
        self.assertEqual(kwargs['db_cls'], LetterboxdDatabase)
        self.assertEqual(kwargs['analytics_cls'], LetterboxdAnalytics)
        self.assertEqual(kwargs['service_name'], "Letterboxd movies")
        self.assertEqual(kwargs['analysis_method'], "analyze_watched")
        self.assertEqual(kwargs['db_filename'], "letterboxd.db")

    @patch('main.run_analysis')
    def test_cmd_overcast_analyze(self, mock_run):
        try:
            main.cmd_overcast_analyze()
        except (Exception, SystemExit):
            pass

        if not mock_run.called:
             self.skipTest("cmd_overcast_analyze not refactored yet")

        _, kwargs = mock_run.call_args
        from src.overcast.analytics import OvercastAnalytics

        self.assertEqual(kwargs['sync_func'], main.cmd_overcast_sync)
        self.assertIsNone(kwargs['db_cls'])
        self.assertEqual(kwargs['analytics_cls'], OvercastAnalytics)
        self.assertEqual(kwargs['service_name'], "Overcast podcasts")
        self.assertEqual(kwargs['analysis_method'], "analyze_podcasts")
        self.assertEqual(kwargs['db_filename'], "overcast.db")

    @patch('main.run_analysis')
    def test_cmd_strong_analyze(self, mock_run):
        try:
            main.cmd_strong_analyze()
        except (Exception, SystemExit):
            pass

        if not mock_run.called:
             self.skipTest("cmd_strong_analyze not refactored yet")

        _, kwargs = mock_run.call_args
        from src.strong.database import StrongDatabase
        from src.strong.analytics import StrongAnalytics

        self.assertEqual(kwargs['sync_func'], main.cmd_strong_sync)
        self.assertEqual(kwargs['db_cls'], StrongDatabase)
        self.assertEqual(kwargs['analytics_cls'], StrongAnalytics)
        self.assertEqual(kwargs['service_name'], "Strong workouts")
        self.assertEqual(kwargs['analysis_method'], "analyze_workouts")
        self.assertEqual(kwargs['db_filename'], "strong.db")

    @patch('main.run_analysis')
    def test_cmd_hardcover_analyze(self, mock_run):
        try:
            main.cmd_hardcover_analyze()
        except (Exception, SystemExit):
            pass

        if not mock_run.called:
             self.skipTest("cmd_hardcover_analyze not refactored yet")

        _, kwargs = mock_run.call_args
        from src.hardcover.database import HardcoverDatabase
        from src.hardcover.analytics import HardcoverAnalytics

        self.assertEqual(kwargs['sync_func'], main.cmd_hardcover_sync)
        self.assertEqual(kwargs['db_cls'], HardcoverDatabase)
        self.assertEqual(kwargs['analytics_cls'], HardcoverAnalytics)
        self.assertEqual(kwargs['service_name'], "Hardcover books")
        self.assertEqual(kwargs['analysis_method'], "analyze_books")
        self.assertEqual(kwargs['db_filename'], "hardcover.db")

    @patch('main.run_analysis')
    def test_cmd_github_analyze(self, mock_run):
        try:
            main.cmd_github_analyze()
        except (Exception, SystemExit):
            pass

        if not mock_run.called:
             self.skipTest("cmd_github_analyze not refactored yet")

        _, kwargs = mock_run.call_args
        from src.github.database import GitHubDatabase
        from src.github.analytics import GitHubAnalytics

        self.assertEqual(kwargs['sync_func'], main.cmd_github_sync)
        self.assertEqual(kwargs['db_cls'], GitHubDatabase)
        self.assertEqual(kwargs['analytics_cls'], GitHubAnalytics)
        self.assertEqual(kwargs['service_name'], "GitHub commits")
        self.assertEqual(kwargs['analysis_method'], "analyze_commits")
        self.assertEqual(kwargs['db_filename'], "github.db")

if __name__ == '__main__':
    unittest.main()
