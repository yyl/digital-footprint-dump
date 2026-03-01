"""Tests for cloud configuration validation."""

import os
import pytest
from unittest.mock import patch


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_validate_readwise_missing_token(self):
        """Test that missing Readwise token raises ValueError."""
        from src.config import Config
        
        with patch.object(Config, 'READWISE_ACCESS_TOKEN', ''):
            with pytest.raises(ValueError, match="READWISE_ACCESS_TOKEN"):
                Config.validate_readwise()

    def test_validate_readwise_with_token(self):
        """Test that Readwise validation passes with token."""
        from src.config import Config
        
        with patch.object(Config, 'READWISE_ACCESS_TOKEN', 'test_token'):
            assert Config.validate_readwise() is True

    def test_validate_foursquare_missing_token(self):
        """Test that missing Foursquare access token raises ValueError."""
        from src.config import Config
        
        with patch.object(Config, 'FOURSQUARE_ACCESS_TOKEN', ''):
            with pytest.raises(ValueError, match="FOURSQUARE_ACCESS_TOKEN"):
                Config.validate_foursquare()

    def test_validate_foursquare_with_token(self):
        """Test that Foursquare validation passes with access token."""
        from src.config import Config
        
        with patch.object(Config, 'FOURSQUARE_ACCESS_TOKEN', 'test_token'):
            assert Config.validate_foursquare() is True

    def test_validate_hardcover_missing_token(self):
        """Test that missing Hardcover token raises ValueError."""
        from src.config import Config

        with patch.object(Config, 'HARDCOVER_ACCESS_TOKEN', ''):
            with pytest.raises(ValueError, match="HARDCOVER_ACCESS_TOKEN"):
                Config.validate_hardcover()

    def test_validate_hardcover_with_token(self):
        """Test that Hardcover validation passes with token."""
        from src.config import Config

        with patch.object(Config, 'HARDCOVER_ACCESS_TOKEN', 'test_token'):
            assert Config.validate_hardcover() is True

    def test_validate_github_missing_token(self):
        """Test that missing GitHub config raises ValueError."""
        from src.config import Config
        
        with patch.object(Config, 'BLOG_GITHUB_TOKEN', ''):
            with patch.object(Config, 'BLOG_REPO_OWNER', 'owner'):
                with patch.object(Config, 'BLOG_REPO_NAME', 'repo'):
                    with pytest.raises(ValueError, match="BLOG_GITHUB_TOKEN"):
                        Config.validate_github()

    def test_validate_github_with_config(self):
        """Test that GitHub validation passes with full config."""
        from src.config import Config
        
        with patch.object(Config, 'BLOG_GITHUB_TOKEN', 'test_token'):
            with patch.object(Config, 'BLOG_REPO_OWNER', 'owner'):
                with patch.object(Config, 'BLOG_REPO_NAME', 'repo'):
                    assert Config.validate_github() is True

    def test_validate_github_activity_missing_config(self):
        """Test that missing GitHub activity config raises ValueError."""
        from src.config import Config

        # Test missing username
        with patch.object(Config, 'CODEBASE_USERNAME', ''):
            with patch.object(Config, 'BLOG_GITHUB_TOKEN', 'token'):
                with pytest.raises(ValueError, match="CODEBASE_USERNAME"):
                    Config.validate_github_activity()

        # Test missing token
        with patch.object(Config, 'CODEBASE_USERNAME', 'user'):
            with patch.object(Config, 'BLOG_GITHUB_TOKEN', ''):
                with pytest.raises(ValueError, match="BLOG_GITHUB_TOKEN"):
                    Config.validate_github_activity()

    def test_validate_github_activity_with_config(self):
        """Test that GitHub activity validation passes with full config."""
        from src.config import Config

        with patch.object(Config, 'CODEBASE_USERNAME', 'test_user'):
            with patch.object(Config, 'BLOG_GITHUB_TOKEN', 'test_token'):
                assert Config.validate_github_activity() is True


class TestDatabasePaths:
    """Test database path resolution."""

    def test_database_paths_are_absolute(self):
        """Test that all database paths are absolute."""
        from src.config import Config
        
        assert Config.DATABASE_PATH.is_absolute()
        assert Config.FOURSQUARE_DATABASE_PATH.is_absolute()
        assert Config.LETTERBOXD_DATABASE_PATH.is_absolute()
        assert Config.OVERCAST_DATABASE_PATH.is_absolute()

    def test_database_paths_in_data_dir(self):
        """Test that all database paths are in the data directory."""
        from src.config import Config
        
        assert Config.DATABASE_PATH.parent == Config.DATA_DIR
        assert Config.FOURSQUARE_DATABASE_PATH.parent == Config.DATA_DIR
        assert Config.LETTERBOXD_DATABASE_PATH.parent == Config.DATA_DIR
        assert Config.OVERCAST_DATABASE_PATH.parent == Config.DATA_DIR

    def test_ensure_data_dir_creates_directory(self, tmp_path):
        """Test that ensure_data_dir creates the data directory."""
        from src.config import Config
        
        # Temporarily override DATA_DIR
        original_data_dir = Config.DATA_DIR
        Config.DATA_DIR = tmp_path / "test_data"
        
        try:
            assert not Config.DATA_DIR.exists()
            Config.ensure_data_dir()
            assert Config.DATA_DIR.exists()
        finally:
            Config.DATA_DIR = original_data_dir
