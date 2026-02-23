"""GitHub REST API client for fetching public activity."""

import time
from typing import Optional, List, Dict, Any
import requests

from ..config import Config


class GitHubActivityClient:
    """Client for the GitHub REST API, focused on public commit activity."""
    
    API_BASE = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None, username: Optional[str] = None):
        """Initialize API client.
        
        Args:
            token: GitHub personal access token. Defaults to BLOG_GITHUB_TOKEN.
            username: GitHub username. Defaults to GITHUB_USERNAME config.
        """
        self.token = token or Config.BLOG_GITHUB_TOKEN
        self.username = username or Config.GITHUB_USERNAME
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self, response: Optional[requests.Response] = None) -> None:
        """Enforce rate limiting. Respects X-RateLimit-Remaining header."""
        if response is not None:
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining is not None and int(remaining) < 100:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                wait = max(0, reset_time - time.time()) + 1
                if int(remaining) < 10:
                    print(f"Rate limit low ({remaining} remaining). Waiting {wait:.0f}s...")
                    time.sleep(wait)
                    return
        
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _get(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make a GET request with rate limiting.
        
        Args:
            url: Full URL or path relative to API_BASE.
            params: Query parameters.
            
        Returns:
            Response object.
            
        Raises:
            requests.HTTPError: On API errors.
        """
        self._rate_limit()
        
        if not url.startswith("http"):
            url = f"{self.API_BASE}{url}"
        
        response = self.session.get(url, params=params, timeout=60)
        
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            if remaining == "0":
                self._rate_limit(response)
                return self._get(url, params=params)
        
        response.raise_for_status()
        self._rate_limit(response)  # Update rate limit state from response
        return response
    
    def _paginate(self, url: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Paginate through all pages of a GitHub API endpoint.
        
        Args:
            url: API endpoint path.
            params: Query parameters.
            
        Returns:
            Combined list of all results across pages.
        """
        params = params or {}
        params.setdefault("per_page", 100)
        
        all_results = []
        
        while url:
            response = self._get(url, params=params)
            data = response.json()
            
            if isinstance(data, list):
                all_results.extend(data)
            else:
                break
            
            # Follow Link header for next page
            link_header = response.headers.get("Link", "")
            url = None
            params = None  # URL from Link header includes params
            for part in link_header.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
                    break
        
        return all_results
    
    def get_public_repos(self) -> List[Dict[str, Any]]:
        """Get all public repos owned by the configured user.
        
        Returns:
            List of repo objects.
        """
        print(f"Fetching public repos for {self.username}...")
        repos = self._paginate(
            f"/users/{self.username}/repos",
            params={"type": "owner", "sort": "updated"}
        )
        # Filter to only non-fork public repos
        public_repos = [r for r in repos if not r.get("fork") and not r.get("private")]
        print(f"Found {len(public_repos)} public repos (non-fork)")
        return public_repos
    
    def get_commits(
        self, owner: str, repo: str, since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get commits by the configured user for a specific repo.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            since: ISO timestamp to fetch commits after (for incremental sync).
            
        Returns:
            List of commit objects.
        """
        params = {"author": self.username}
        if since:
            params["since"] = since
        
        return self._paginate(f"/repos/{owner}/{repo}/commits", params=params)
