"""Configuration loader for Readwise Data Exporter."""

import os
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # API Configuration
    READWISE_ACCESS_TOKEN: str = os.getenv("READWISE_ACCESS_TOKEN", "")
    
    # API Base URLs
    READWISE_API_V2_BASE = "https://readwise.io/api/v2"
    READER_API_V3_BASE = "https://readwise.io/api/v3"
    
    # Database Configuration
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    DATABASE_PATH = DATA_DIR / "readwise.db"
    
    # Rate Limiting (requests per minute)
    READWISE_RATE_LIMIT = 20  # For export endpoint
    READER_RATE_LIMIT = 20   # Default rate
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.READWISE_ACCESS_TOKEN:
            raise ValueError(
                "READWISE_ACCESS_TOKEN is not set. "
                "Please copy .env.example to .env and add your token."
            )
        return True
    
    @classmethod
    def ensure_data_dir(cls) -> None:
        """Ensure the data directory exists."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
