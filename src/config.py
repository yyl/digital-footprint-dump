"""Configuration loader for Digital Footprint Dump."""

import os
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv(override=True)


def _resolve_storage_root(project_root: Path) -> Path:
    """Resolve the base directory that contains data/ and files/."""
    configured_root = os.getenv("DATA_REPO_LOCAL_PATH", "").strip()
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    sibling_repo = (project_root.parent / "digital-footprint-data").resolve()
    if sibling_repo.exists():
        return sibling_repo

    return project_root


class Config:
    """Application configuration."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    STORAGE_ROOT = _resolve_storage_root(PROJECT_ROOT)
    DATA_DIR = STORAGE_ROOT / "data"
    FILES_DIR = STORAGE_ROOT / "files"
    
    # ==========================================================================
    # Readwise Configuration
    # ==========================================================================
    READWISE_ACCESS_TOKEN: str = os.getenv("READWISE_ACCESS_TOKEN", "")
    READWISE_API_V2_BASE = "https://readwise.io/api/v2"
    READER_API_V3_BASE = "https://readwise.io/api/v3"
    DATABASE_PATH = DATA_DIR / "readwise.db"
    READWISE_RATE_LIMIT = 20
    READER_RATE_LIMIT = 20
    
    # ==========================================================================
    # Foursquare Configuration
    # ==========================================================================
    FOURSQUARE_CLIENT_ID: str = os.getenv("FOURSQUARE_CLIENT_ID", "")
    FOURSQUARE_CLIENT_SECRET: str = os.getenv("FOURSQUARE_CLIENT_SECRET", "")
    FOURSQUARE_API_KEY: str = os.getenv("FOURSQUARE_API_KEY", "")
    FOURSQUARE_ACCESS_TOKEN: str = os.getenv("FOURSQUARE_ACCESS_TOKEN", "")
    FOURSQUARE_REDIRECT_URI: str = os.getenv(
        "FOURSQUARE_REDIRECT_URI", "https://localhost:8888/callback"
    )
    FOURSQUARE_DATABASE_PATH = DATA_DIR / "foursquare.db"
    
    # ==========================================================================
    # Letterboxd Configuration
    # ==========================================================================
    LETTERBOXD_DATABASE_PATH = DATA_DIR / "letterboxd.db"
    LETTERBOXD_RSS_URL: str = os.getenv(
        "LETTERBOXD_RSS_URL",
        "https://letterboxd.com/longyu/rss/"
    )
    TMDB_ACCESS_TOKEN: str = os.getenv("TMDB_ACCESS_TOKEN", "").strip()
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "").strip()
    
    # ==========================================================================
    # Overcast Configuration
    # ==========================================================================
    OVERCAST_DATABASE_PATH = DATA_DIR / "overcast.db"
    OVERCAST_COOKIE: str = os.getenv("OVERCAST_COOKIE", "").strip()
    OVERCAST_EMAIL: str = os.getenv("OVERCAST_EMAIL", "").strip()
    OVERCAST_PASSWORD: str = os.getenv("OVERCAST_PASSWORD", "")
    
    # ==========================================================================
    # Strong Configuration
    # ==========================================================================
    STRONG_DATABASE_PATH = DATA_DIR / "strong.db"

    # ==========================================================================
    # Apple Health Configuration
    # ==========================================================================
    APPLE_HEALTH_DATABASE_PATH = DATA_DIR / "apple_health.db"

    # ==========================================================================
    # Blog Tracking Configuration
    # ==========================================================================
    BLOG_DATABASE_PATH = DATA_DIR / "blog.db"
    BLOG_POSTS_INDEX_URL: str = os.getenv(
        "BLOG_POSTS_INDEX_URL",
        "https://www.mildlyjournaling.com/posts/index.json",
    )
    
    # ==========================================================================
    # Hardcover Configuration
    # ==========================================================================
    HARDCOVER_ACCESS_TOKEN: str = os.getenv("HARDCOVER_ACCESS_TOKEN", "")
    HARDCOVER_API_URL = "https://api.hardcover.app/v1/graphql"
    HARDCOVER_DATABASE_PATH = DATA_DIR / "hardcover.db"
    
    # ==========================================================================
    # GitHub Activity Configuration
    # ==========================================================================
    CODEBASE_USERNAME: str = os.getenv("CODEBASE_USERNAME", "")
    CODEBASE_DATABASE_PATH = DATA_DIR / "github.db"
    # Reuses BLOG_GITHUB_TOKEN for authenticated API access (5000 req/hr)
    
    # ==========================================================================
    # GitHub Publishing Configuration
    # ==========================================================================
    BLOG_GITHUB_TOKEN: str = os.getenv("BLOG_GITHUB_TOKEN", "")
    BLOG_REPO_OWNER: str = os.getenv("BLOG_REPO_OWNER", "")
    BLOG_REPO_NAME: str = os.getenv("BLOG_REPO_NAME", "")
    BLOG_GITHUB_TARGET_BRANCH: str = os.getenv("BLOG_GITHUB_TARGET_BRANCH", "main")
    DATA_REPO_GITHUB_TOKEN: str = os.getenv(
        "DATA_REPO_GITHUB_TOKEN",
        os.getenv("DATA_REPO_PAT", BLOG_GITHUB_TOKEN),
    )
    DATA_REPO_OWNER: str = os.getenv("DATA_REPO_OWNER", "yyl")
    DATA_REPO_NAME: str = os.getenv("DATA_REPO_NAME", "digital-footprint-data")
    DATA_GITHUB_TARGET_BRANCH: str = os.getenv("DATA_GITHUB_TARGET_BRANCH", "main")
    DATA_REPO_POSTS_DIR: str = os.getenv("DATA_REPO_POSTS_DIR", "posts").strip().strip("/") or "posts"
    
    @classmethod
    def validate_readwise(cls) -> bool:
        """Validate Readwise configuration."""
        if not cls.READWISE_ACCESS_TOKEN:
            raise ValueError(
                "READWISE_ACCESS_TOKEN is not set. "
                "Please copy .env.example to .env and add your token."
            )
        return True
    
    @classmethod
    def validate_foursquare(cls) -> bool:
        """Validate Foursquare configuration."""
        if not cls.FOURSQUARE_ACCESS_TOKEN:
            raise ValueError(
                "FOURSQUARE_ACCESS_TOKEN is not set. "
                "Run the OAuth flow locally to obtain a token, "
                "then add it to your .env file."
            )
        return True
    
    @classmethod
    def validate_hardcover(cls) -> bool:
        """Validate Hardcover configuration."""
        if not cls.HARDCOVER_ACCESS_TOKEN:
            raise ValueError(
                "HARDCOVER_ACCESS_TOKEN is not set. "
                "Get your token from https://hardcover.app/account/api "
                "and add it to your .env file."
            )
        return True
    
    @classmethod
    def validate_github_activity(cls) -> bool:
        """Validate GitHub activity configuration."""
        missing = []
        if not cls.CODEBASE_USERNAME:
            missing.append("CODEBASE_USERNAME")
        if not cls.BLOG_GITHUB_TOKEN:
            missing.append("BLOG_GITHUB_TOKEN (needed for API auth)")
        if missing:
            raise ValueError(
                f"Missing GitHub activity configuration: {', '.join(missing)}. "
                "Please add them to your .env file."
            )
        return True
    
    @classmethod
    def validate_github(cls) -> bool:
        """Validate GitHub publishing configuration."""
        missing = []
        if not cls.BLOG_GITHUB_TOKEN:
            missing.append("BLOG_GITHUB_TOKEN")
        if not cls.BLOG_REPO_OWNER:
            missing.append("BLOG_REPO_OWNER")
        if not cls.BLOG_REPO_NAME:
            missing.append("BLOG_REPO_NAME")
        if missing:
            raise ValueError(
                f"Missing GitHub configuration: {', '.join(missing)}. "
                "Please add them to your .env file."
            )
        return True

    @classmethod
    def validate_data_repo_github(cls) -> bool:
        """Validate GitHub publishing configuration for the data repository."""
        missing = []
        if not cls.DATA_REPO_GITHUB_TOKEN and not cls.BLOG_GITHUB_TOKEN:
            missing.append("DATA_REPO_GITHUB_TOKEN")
        if not cls.DATA_REPO_OWNER:
            missing.append("DATA_REPO_OWNER")
        if not cls.DATA_REPO_NAME:
            missing.append("DATA_REPO_NAME")
        if missing:
            raise ValueError(
                f"Missing data repo GitHub configuration: {', '.join(missing)}. "
                "Please add them to your .env file. DATA_REPO_PAT or BLOG_GITHUB_TOKEN "
                "can also be used as a backward-compatible data repo token."
            )
        return True
    
    @classmethod
    def validate(cls) -> bool:
        """Validate all configuration (legacy compatibility)."""
        return cls.validate_readwise()
    
    @classmethod
    def ensure_data_dir(cls) -> None:
        """Ensure the data directory exists."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
