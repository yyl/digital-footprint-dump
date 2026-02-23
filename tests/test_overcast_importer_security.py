import sys
from unittest.mock import MagicMock

# Mock missing dependencies before importing src
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['github'] = MagicMock()

import subprocess
from unittest.mock import patch
from pathlib import Path
from src.overcast.importer import OvercastImporter

def test_sync_timeout_handled():
    """Test that subprocess.TimeoutExpired is handled gracefully."""
    importer = OvercastImporter()

    # Mock find_latest_export to return a dummy path
    with patch.object(OvercastImporter, 'find_latest_export', return_value=Path("dummy.opml")):
        # Mock subprocess.run to raise TimeoutExpired
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=["overcast-to-sqlite"], timeout=60)):
            # Mock get_db_stats just in case, though it shouldn't be called on timeout
            with patch.object(OvercastImporter, 'get_db_stats') as mock_get_stats:
                stats = importer.sync()

                # Verify that it returns the initial empty stats
                assert stats == {"feeds": 0, "episodes": 0, "playlists": 0}
                # Verify that get_db_stats was NOT called because it should have timed out before
                mock_get_stats.assert_not_called()

def test_sync_called_process_error_handled():
    """Test that subprocess.CalledProcessError is handled gracefully."""
    importer = OvercastImporter()

    with patch.object(OvercastImporter, 'find_latest_export', return_value=Path("dummy.opml")):
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, ["overcast-to-sqlite"], stderr="error")):
            stats = importer.sync()
            assert stats == {"feeds": 0, "episodes": 0, "playlists": 0}

def test_sync_file_not_found_handled():
    """Test that FileNotFoundError is handled gracefully."""
    importer = OvercastImporter()

    with patch.object(OvercastImporter, 'find_latest_export', return_value=Path("dummy.opml")):
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            stats = importer.sync()
            assert stats == {"feeds": 0, "episodes": 0, "playlists": 0}
