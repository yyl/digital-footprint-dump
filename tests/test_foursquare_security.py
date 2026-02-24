import sys
from unittest.mock import MagicMock

# Mock requests and dotenv before importing src modules if not available
try:
    import requests
except ImportError:
    sys.modules["requests"] = MagicMock()

try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = MagicMock()

import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Now import project modules
from src.foursquare.api_client import FoursquareAPIClient
# We need to ensure Config is imported correctly.
# src.config imports dotenv, so we mocked it above.
from src.config import Config

class TestFoursquareSecurity(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for the test
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Save original Config.PROJECT_ROOT
        self.original_project_root = Config.PROJECT_ROOT

        # Point Config.PROJECT_ROOT to our temp dir so .env is written there
        Config.PROJECT_ROOT = self.temp_path

    def tearDown(self):
        # Restore original Config.PROJECT_ROOT
        Config.PROJECT_ROOT = self.original_project_root

        # Remove temp directory
        shutil.rmtree(self.temp_dir)

    def test_save_token_secure_permissions(self):
        """Test that _save_token_to_env writes file with secure permissions (600)."""
        client = FoursquareAPIClient()
        test_token = "secure_test_token_123"

        # Call the method
        # Note: _save_token_to_env is internal, but we test it directly
        client._save_token_to_env(test_token)

        env_file = self.temp_path / ".env"
        self.assertTrue(env_file.exists(), ".env file should exist")

        # Check permissions
        st = os.stat(env_file)
        mode = st.st_mode & 0o777

        print(f"File permissions: {oct(mode)}")
        # This assert is expected to FAIL until fixed
        self.assertEqual(mode, 0o600, f"File permissions are {oct(mode)}, expected 0o600 (secure)")

    def test_save_token_fixes_existing_permissions(self):
        """Test that _save_token_to_env fixes permissions on existing insecure file."""
        env_file = self.temp_path / ".env"
        client = FoursquareAPIClient()

        # Create an insecure file first (e.g., 664)
        with open(env_file, "w") as f:
            f.write("EXISTING_VAR=foo\n")

        # Ensure it is insecure
        os.chmod(env_file, 0o664)
        st = os.stat(env_file)
        mode = st.st_mode & 0o777
        print(f"Initial insecure permissions: {oct(mode)}")

        # Run the method
        client._save_token_to_env("new_token")

        # Verify it fixed the permissions
        st = os.stat(env_file)
        mode = st.st_mode & 0o777
        print(f"Fixed permissions: {oct(mode)}")
        # This assert is expected to FAIL until fixed
        self.assertEqual(mode, 0o600, f"File permissions are {oct(mode)}, expected 0o600 (secure)")

if __name__ == "__main__":
    unittest.main()
